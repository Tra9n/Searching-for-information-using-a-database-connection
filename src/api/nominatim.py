import requests
from config import NOMINATIM_USER_AGENT


def get_country_bbox(country_name: str):
    """Возвращает (min_lat, max_lat, min_lon, max_lon) для страны."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": country_name, "format": "json", "limit": 1}
    headers = {"User-Agent": NOMINATIM_USER_AGENT}

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError(f"Страна не найдена: {country_name}")

    min_lat, max_lat, min_lon, max_lon = map(float, data[0]["boundingbox"])
    return min_lat, max_lat, min_lon, max_lon