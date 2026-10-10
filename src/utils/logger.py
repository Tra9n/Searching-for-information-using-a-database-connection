"""Настройка логирования для всего проекта."""

import logging
import sys


def setup_logger(
    name: str = "sky_project", level: int = logging.INFO
) -> logging.Logger:
    """
    Возвращает настроенный логгер с выводом в stdout.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
