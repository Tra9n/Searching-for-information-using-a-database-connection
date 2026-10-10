"""Загрузка данных о самолётах из внешних API в PostgreSQL."""

import time
from typing import Any

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.api.nominatim import get_country_bbox
from src.api.opensky import get_airplanes_in_bbox
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS aeroplanes (
    id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10),
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    velocity REAL,
    country_id INTEGER REFERENCES countries(id) ON DELETE CASCADE
);
"""


class DataLoader:
    """
    Оркестрирует полный цикл загрузки
    """

    def __init__(
        self,
        db_name: str,
        db_params: dict,
        nominatim_delay: float = 1.2,
        opensky_delay: float = 0.5,
    ) -> None:

        self.db_name = db_name
        self.db_params = db_params
        self.nominatim_delay = nominatim_delay
        self.opensky_delay = opensky_delay

    def load(self, countries: list[str]) -> None:
        """
        Загружает данные по всем указанным странам.
        """
        self.ensure_database()
        self.create_schema()

        for country in countries:
            try:
                self._load_country(country)
            except Exception as exc:
                logger.exception("Ошибка загрузки для страны '%s': %s", country, exc)

    def ensure_database(self) -> None:
        """Создаёт БД, если она ещё не существует."""
        conn = psycopg2.connect(dbname="postgres", **self.db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_name,)
                )
                if not cur.fetchone():
                    cur.execute(f"CREATE DATABASE \"{self.db_name}\" ENCODING 'UTF8';")
                    logger.info("База данных '%s' создана.", self.db_name)
                else:
                    logger.info("База данных '%s' уже существует.", self.db_name)
        finally:
            conn.close()

    def create_schema(self) -> None:
        """Создаёт таблицы countries и aeroplanes (idempotent)."""
        conn = psycopg2.connect(dbname=self.db_name, **self.db_params)
        try:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
            logger.info("Схема БД готова.")
        finally:
            conn.close()

    def _load_country(self, country: str) -> None:
        """Скачивает данные по одной стране и сохраняет их в БД."""
        min_lat, max_lat, min_lon, max_lon = get_country_bbox(country)
        time.sleep(self.nominatim_delay)

        states = get_airplanes_in_bbox(min_lat, max_lat, min_lon, max_lon)
        time.sleep(self.opensky_delay)

        self._save_country(country, states)

    def _save_country(self, country: str, states: list[list[Any]]) -> None:
        """Сохраняет страну и её самолёты одной транзакцией."""
        conn = psycopg2.connect(dbname=self.db_name, **self.db_params)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO countries (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                    """,
                    (country,),
                )
                country_id: int = cur.fetchone()[0]

                rows = [
                    (
                        s[0],
                        s[1].strip() if s[1] else None,
                        s[2],
                        s[9],
                        country_id,
                    )
                    for s in states
                ]
                if rows:
                    cur.executemany(
                        """
                        INSERT INTO aeroplanes
                            (icao24, callsign, origin_country, velocity, country_id)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        rows,
                    )

            conn.commit()
            logger.info("'%s': сохранено %d самолётов.", country, len(states))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
