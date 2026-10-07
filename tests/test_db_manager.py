import pytest


def test_get_countries_and_aeroplanes_count(db_manager):
    """Проверяет подсчёт самолётов по странам, включая страны без самолётов."""
    result = db_manager.get_countries_and_aeroplanes_count()
    result_dict = dict(result)

    assert result_dict["Germany"] == 2
    assert result_dict["France"] == 2
    assert result_dict["Spain"] == 0

    # Сортировка по убыванию количества
    counts = [count for _, count in result]
    assert counts == sorted(counts, reverse=True)


def test_get_all_aeroplanes(db_manager):
    """Проверяет список всех самолётов."""
    result = db_manager.get_all_aeroplanes()
    assert len(result) == 4

    callsigns = {row[1] for row in result}
    assert callsigns == {"ACA101", "DLH202", "AFR303", "ACA404"}


def test_get_avg_speed(db_manager):
    """Средняя скорость: (250 + 300 + 150 + 200) / 4 = 225.0"""
    avg = db_manager.get_avg_speed()
    assert avg == pytest.approx(225.0, rel=1e-3)


def test_get_avg_speed_empty(clean_db, monkeypatch):
    """Если нет самолётов, метод возвращает 0."""
    import config
    from tests.conftest import TEST_DB_CONFIG
    monkeypatch.setattr(config, "DB_CONFIG", TEST_DB_CONFIG)

    import importlib
    import src.database.db_manager as dbm
    importlib.reload(dbm)

    # Очищаем таблицу
    import psycopg2
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("TRUNCATE aeroplanes RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()
    conn.close()

    manager = dbm.DBManager()
    try:
        assert manager.get_avg_speed() == 0
    finally:
        manager.close()


def test_get_aeroplanes_with_higher_speed(db_manager):
    """Скорость выше средней (225): DLH202 (300) и ACA101 (250)."""
    result = db_manager.get_aeroplanes_with_higher_speed()
    callsigns = {row[1] for row in result}

    assert callsigns == {"ACA101", "DLH202"}
    assert len(result) == 2


def test_get_aeroplanes_with_keyword(db_manager):
    """Поиск по ключевому слову 'ACA' — находит 2 самолёта."""
    result = db_manager.get_aeroplanes_with_keyword("ACA")
    callsigns = {row[1] for row in result}

    assert callsigns == {"ACA101", "ACA404"}
    assert len(result) == 2


def test_get_aeroplanes_with_keyword_case_insensitive(db_manager):
    """ILIKE должен быть регистронезависимым."""
    result_lower = db_manager.get_aeroplanes_with_keyword("aca")
    result_upper = db_manager.get_aeroplanes_with_keyword("ACA")

    assert {r[1] for r in result_lower} == {r[1] for r in result_upper}


def test_get_aeroplanes_with_keyword_no_match(db_manager):
    """Если совпадений нет, возвращается пустой список."""
    result = db_manager.get_aeroplanes_with_keyword("XYZ")
    assert result == []


def test_get_aeroplanes_with_keyword_partial(db_manager):
    """Поиск по части позывного: '10' — находит ACA101."""
    result = db_manager.get_aeroplanes_with_keyword("10")
    assert len(result) == 1
    assert result[0][1] == "ACA101"