"""Клиент для получения данных о самолётах через OpenSky Network API."""

from typing import Any

import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OPENSKY_URL = "https://opensky-network.org/api/states/all"


def get_airplanes_in_bbox(
    min_lat: float, max_lat: float, min_lon: float, max_lon: float
) -> list[list[Any]]:
    """
    Возвращает список состояний самолётов в заданной области.
    """
    params = {
        "lamin": min_lat,
        "lamax": max_lat,
        "lomin": min_lon,
        "lomax": max_lon,
    }

    logger.info(
        "OpenSky: запрос самолётов в bbox=%s", (min_lat, max_lat, min_lon, max_lon)
    )
    response = requests.get(OPENSKY_URL, params=params, timeout=30)
    response.raise_for_status()

    states = response.json().get("states") or []
    logger.info("OpenSky: получено %d самолётов", len(states))
    return states
