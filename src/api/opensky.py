import requests


def get_airplanes_in_bbox(min_lat, max_lat, min_lon, max_lon):
    """Возвращает список состояний самолётов в bounding box."""
    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": min_lat, "lamax": max_lat,
        "lomin": min_lon, "lomax": max_lon,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("states", []) or []