import psycopg2
from config import DB_CONFIG


class DBManager:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def get_countries_and_aeroplanes_count(self):
        self.cur.execute("""
            SELECT c.name, COUNT(a.id)
            FROM countries c
            LEFT JOIN aeroplanes a ON c.id = a.country_id
            GROUP BY c.name
            ORDER BY COUNT(a.id) DESC;
        """)
        return self.cur.fetchall()

    def get_all_aeroplanes(self):
        self.cur.execute("""
            SELECT a.icao24, a.callsign, a.origin_country, a.velocity, c.name
            FROM aeroplanes a
            LEFT JOIN countries c ON a.country_id = c.id;
        """)
        return self.cur.fetchall()

    def get_avg_speed(self):
        self.cur.execute("SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL;")
        result = self.cur.fetchone()
        return result[0] if result and result[0] is not None else 0

    def get_aeroplanes_with_higher_speed(self):
        self.cur.execute("""
            SELECT a.icao24, a.callsign, a.velocity
            FROM aeroplanes a
            WHERE a.velocity > (SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL);
        """)
        return self.cur.fetchall()

    def get_aeroplanes_with_keyword(self, keyword: str):
        self.cur.execute("""
            SELECT a.icao24, a.callsign, a.velocity
            FROM aeroplanes a
            WHERE a.callsign ILIKE %s;
        """, (f"%{keyword}%",))
        return self.cur.fetchall()