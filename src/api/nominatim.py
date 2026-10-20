"""Клиент для получения географических координат через Nominatim (OpenStreetMap)."""

import os

import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "SkyProject/1.0 (test@example.com)"


def get_country_bbox(country_name: str) -> tuple[float, float, float, float]:
    """
    Возвращает ограничивающую рамку (bounding box) для страны.
    """
    user_agent = os.getenv("NOMINATIM_USER_AGENT", DEFAULT_USER_AGENT)
    headers = {"User-Agent": user_agent}
    params = {"q": country_name, "format": "json", "limit": 1}

    logger.info("Nominatim: запрос bbox для %s", country_name)
    response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    if not data:
        raise ValueError(f"Страна не найдена: {country_name}")

    min_lat, max_lat, min_lon, max_lon = map(float, data[0]["boundingbox"])
    logger.debug(
        "Nominatim: %s -> %s", country_name, (min_lat, max_lat, min_lon, max_lon)
    )
    return min_lat, max_lat, min_lon, max_lon
