"""Класс DBManager — аналитические запросы к БД."""

from typing import Any

import psycopg2


class DBManager:
    """
    Обёртка над psycopg2 для аналитических запросов.
    """

    def __init__(self, db_name: str, db_params: dict) -> None:
        self.conn = psycopg2.connect(dbname=db_name, **db_params)
        self.cur = self.conn.cursor()

    def close(self) -> None:
        """Закрывает курсор и соединение."""
        self.cur.close()
        self.conn.close()

    def get_countries_and_aeroplanes_count(self) -> list[tuple[str, int]]:
        """
        Возвращает список стран и количество самолётов в каждой.
        """
        self.cur.execute("""
            SELECT c.name, COUNT(a.id) AS aeroplanes_count
            FROM countries c
            LEFT JOIN aeroplanes a ON c.id = a.country_id
            GROUP BY c.name
            ORDER BY aeroplanes_count DESC, c.name ASC;
        """)
        return self.cur.fetchall()

    def get_all_aeroplanes(self) -> list[tuple]:
        """
        Возвращает список всех самолётов с названием страны.
        """
        self.cur.execute("""
            SELECT a.icao24, a.callsign, a.origin_country, a.velocity, c.name
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id
            ORDER BY a.velocity DESC NULLS LAST;
        """)
        return self.cur.fetchall()

    def get_avg_speed(self) -> float:
        """
        Средняя скорость по всем самолётам (м/с).
        """
        self.cur.execute(
            "SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL;"
        )
        result = self.cur.fetchone()
        return float(result[0]) if result and result[0] is not None else 0.0

    def get_aeroplanes_with_higher_speed(self) -> list[tuple]:
        """
        Возвращает самолёты со скоростью выше средней.
        """
        self.cur.execute("""
            SELECT a.icao24, a.callsign, a.velocity
            FROM aeroplanes a
            WHERE a.velocity > (
                SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL
            )
            ORDER BY a.velocity DESC;
        """)
        return self.cur.fetchall()

    def get_aeroplanes_with_keyword(self, keyword: str) -> list[tuple]:
        """
        Возвращает самолёты, в позывном которых встречается подстрока.
        """
        self.cur.execute(
            """
            SELECT a.icao24, a.callsign, a.velocity
            FROM aeroplanes a
            WHERE a.callsign ILIKE %s
            ORDER BY a.callsign;
            """,
            (f"%{keyword}%",),
        )
        return self.cur.fetchall()
