"""Конфигурация проекта: чтение параметров подключения к БД."""

from configparser import ConfigParser


def config(filename: str = "database.ini", section: str = "postgresql") -> dict:
    """
    Читает параметры подключения к PostgreSQL из ini-файла.

    :param filename: путь к ini-файлу
    :param section: имя секции с параметрами
    :return: словарь с ключами host, user, password, port, database
    :raises FileNotFoundError: если файл не найден
    :raises Exception: если секция отсутствует
    """
    parser = ConfigParser()
    if not parser.read(filename):
        raise FileNotFoundError(f"Файл конфигурации не найден: {filename}")

    if not parser.has_section(section):
        raise Exception(f"Секция [{section}] не найдена в {filename}")

    return dict(parser.items(section))
