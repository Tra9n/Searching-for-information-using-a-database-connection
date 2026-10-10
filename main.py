"""Точка входа Sky Project."""

import argparse

from dotenv import load_dotenv

from config import config
from src.database.db_manager import DBManager
from src.database.loader import DataLoader
from src.utils.logger import setup_logger

logger = setup_logger("main")

DEFAULT_COUNTRIES = [
    "Germany",
    "France",
    "Italy",
    "Spain",
]


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Sky Project — сбор данных о самолётах."
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_COUNTRIES,
        help="Список стран для отслеживания (по умолчанию: Germany France Italy Spain)",
    )
    parser.add_argument(
        "--keyword",
        default="ACA",
        help="Ключевое слово для поиска по позывному (по умолчанию: ACA)",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Пропустить загрузку данных, вывести только аналитику",
    )
    return parser.parse_args()


def main() -> None:
    """Основная логика: загрузка данных и вывод аналитики."""
    load_dotenv()
    args = parse_args()

    params = config()
    db_name = params.pop("database")
    logger.info(
        "Подключение к БД '%s' (%s:%s)", db_name, params["host"], params["port"]
    )

    if not args.skip_load:
        loader = DataLoader(db_name=db_name, db_params=params)
        loader.load(args.countries)
    else:
        logger.info("Загрузка данных пропущена (--skip-load).")

    db = DBManager(db_name=db_name, db_params=params)
    try:
        _print_analytics(db, keyword=args.keyword)
    finally:
        db.close()


def _print_analytics(db: DBManager, keyword: str) -> None:
    """Печатает базовую аналитику по загруженным данным."""
    print("\n=== Страны и количество самолётов ===")
    for name, count in db.get_countries_and_aeroplanes_count():
        print(f"  {name}: {count}")

    avg_speed = db.get_avg_speed()
    print(f"\n=== Средняя скорость: {avg_speed:.2f} м/с ===")

    faster = db.get_aeroplanes_with_higher_speed()
    print(f"\n=== Самолёты быстрее средней: {len(faster)} ===")
    for icao24, callsign, velocity in faster[:10]:
        print(f"  {callsign or icao24}: {velocity:.1f} м/с")

    matched = db.get_aeroplanes_with_keyword(keyword)
    print(f"\n=== Совпадения по '{keyword}': {len(matched)} ===")
    for icao24, callsign, velocity in matched[:10]:
        print(f"  {callsign}: {velocity} м/с")


if __name__ == "__main__":
    main()
