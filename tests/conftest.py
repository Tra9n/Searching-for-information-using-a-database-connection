"""Общие фикстуры для тестов."""

import os

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

os.environ.setdefault("LC_MESSAGES", "C")
os.environ.setdefault("LANG", "C")

TEST_DB_NAME = os.getenv("TEST_DB_NAME", "sky_db_test")
TEST_DB_PARAMS = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}


def _decode_pg_error(exc: Exception) -> str:
    """Libpq на русской Windows отдаёт сообщения в cp1251."""
    raw = getattr(exc, "pgerror", None) or (exc.args[0] if exc.args else "")
    if isinstance(raw, bytes):
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return repr(raw)
    return str(raw)


@pytest.fixture(scope="session")
def db_available():
    """True, если PostgreSQL доступен. Иначе — интеграционные тесты skip."""
    try:
        conn = psycopg2.connect(dbname="postgres", **TEST_DB_PARAMS)
        conn.close()
        return True
    except UnicodeDecodeError as exc:
        raw = exc.object
        for enc in ("cp1251", "utf-8", "latin-1"):
            try:
                print(f"\n[conftest] PostgreSQL ответил ({enc}): {raw.decode(enc)}")
                break
            except UnicodeDecodeError:
                continue
        return False
    except Exception as exc:
        print(f"\n[conftest] PostgreSQL недоступен: {exc}")
        return False


def _create_test_database() -> None:
    """Создаёт тестовую БД, если её нет."""
    conn = psycopg2.connect(dbname="postgres", **TEST_DB_PARAMS)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s;", (TEST_DB_NAME,)
            )
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE \"{TEST_DB_NAME}\" ENCODING 'UTF8';")
    finally:
        conn.close()


@pytest.fixture(scope="session")
def setup_test_db(db_available):
    """Создаёт тестовую БД и таблицы. Только если PostgreSQL доступен."""
    if not db_available:
        pytest.skip("PostgreSQL недоступен — интеграционные тесты пропущены.")

    _create_test_database()

    from src.database.loader import SCHEMA_SQL

    conn = psycopg2.connect(dbname=TEST_DB_NAME, **TEST_DB_PARAMS)
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

    yield

    conn = psycopg2.connect(dbname=TEST_DB_NAME, **TEST_DB_PARAMS)
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS aeroplanes;")
            cur.execute("DROP TABLE IF EXISTS countries;")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def clean_db(setup_test_db):
    """Очищает и наполняет таблицы тестовыми данными."""
    conn = psycopg2.connect(dbname=TEST_DB_NAME, **TEST_DB_PARAMS)
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE aeroplanes RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE countries RESTART IDENTITY CASCADE;")

            cur.execute("INSERT INTO countries (name) VALUES ('Germany') RETURNING id;")
            germany_id = cur.fetchone()[0]
            cur.execute("INSERT INTO countries (name) VALUES ('France') RETURNING id;")
            france_id = cur.fetchone()[0]
            cur.execute("INSERT INTO countries (name) VALUES ('Spain');")

            rows = [
                ("abc123", "ACA101", "Canada", 250.0, germany_id),
                ("def456", "DLH202", "Germany", 300.0, germany_id),
                ("ghi789", "AFR303", "France", 150.0, france_id),
                ("jkl012", "ACA404", "Canada", 200.0, france_id),
            ]
            cur.executemany(
                """INSERT INTO aeroplanes
                   (icao24, callsign, origin_country, velocity, country_id)
                   VALUES (%s, %s, %s, %s, %s);""",
                rows,
            )
        conn.commit()
    finally:
        conn.close()
    yield


@pytest.fixture
def db_manager(clean_db):
    """DBManager, подключённый к тестовой БД."""
    from src.database.db_manager import DBManager

    manager = DBManager(TEST_DB_NAME, TEST_DB_PARAMS)
    yield manager
    manager.close()
