import os
os.environ.setdefault("LC_MESSAGES", "C")
os.environ.setdefault("LANG", "C")

import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

TEST_DB_NAME = os.getenv("TEST_DB_NAME", "sky_db_test")
TEST_DB_USER = os.getenv("DB_USER", "postgres")
TEST_DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
TEST_DB_HOST = os.getenv("DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("DB_PORT", "5432")

TEST_DB_CONFIG = {
    "dbname": TEST_DB_NAME,
    "user": TEST_DB_USER,
    "password": TEST_DB_PASSWORD,
    "host": TEST_DB_HOST,
    "port": TEST_DB_PORT,
}

_ADMIN_CONNECT_KWARGS = {
    "user": TEST_DB_USER,
    "password": TEST_DB_PASSWORD,
    "host": TEST_DB_HOST,
    "port": TEST_DB_PORT,
}



@pytest.fixture(scope="session")
def db_available():
    """True, если PostgreSQL доступен. Иначе тесты с БД будут пропущены."""
    try:
        conn = psycopg2.connect(dbname="postgres", **_ADMIN_CONNECT_KWARGS)
        conn.close()
        return True
    except Exception as e:
        print(f"\n[conftest] PostgreSQL недоступен: {e!r}")
        return False



def _create_test_database():
    conn = psycopg2.connect(dbname="postgres", **_ADMIN_CONNECT_KWARGS)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (TEST_DB_NAME,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}" ENCODING \'UTF8\';')
    cur.close()
    conn.close()


@pytest.fixture(scope="session")
def setup_test_db(db_available):
    """Создаёт тестовую БД и таблицы. Запускается ТОЛЬКО если БД доступна."""
    if not db_available:
        pytest.skip("PostgreSQL недоступен — интеграционные тесты пропущены.")

    _create_test_database()

    conn = psycopg2.connect(**TEST_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
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
            country_id INTEGER REFERENCES countries(id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

    yield

    conn = psycopg2.connect(**TEST_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS aeroplanes;")
    cur.execute("DROP TABLE IF EXISTS countries;")
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture
def clean_db(setup_test_db):
    """Очищает и наполняет таблицы тестовыми данными."""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("TRUNCATE aeroplanes RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE countries RESTART IDENTITY CASCADE;")

    cur.execute("INSERT INTO countries (name) VALUES ('Germany') RETURNING id;")
    germany_id = cur.fetchone()[0]
    cur.execute("INSERT INTO countries (name) VALUES ('France') RETURNING id;")
    france_id = cur.fetchone()[0]
    cur.execute("INSERT INTO countries (name) VALUES ('Spain') RETURNING id;")

    aeroplanes = [
        ("abc123", "ACA101", "Canada", 250.0, germany_id),
        ("def456", "DLH202", "Germany", 300.0, germany_id),
        ("ghi789", "AFR303", "France", 150.0, france_id),
        ("jkl012", "ACA404", "Canada", 200.0, france_id),
    ]
    for icao, callsign, origin, velocity, cid in aeroplanes:
        cur.execute(
            """INSERT INTO aeroplanes (icao24, callsign, origin_country, velocity, country_id)
               VALUES (%s, %s, %s, %s, %s);""",
            (icao, callsign, origin, velocity, cid),
        )

    conn.commit()
    cur.close()
    conn.close()
    yield


@pytest.fixture
def db_manager(clean_db, monkeypatch):
    """DBManager, подключённый к тестовой БД."""
    import config
    monkeypatch.setattr(config, "DB_CONFIG", TEST_DB_CONFIG)

    import importlib
    import src.database.db_manager as dbm
    importlib.reload(dbm)

    manager = dbm.DBManager()
    yield manager
    manager.close()