import psycopg2
from config import DB_CONFIG


def init_db(schema_path="sql/schema.sql"):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print("Таблицы созданы.")