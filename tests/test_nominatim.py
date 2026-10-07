import pytest
from unittest.mock import Mock, patch
from src.api.nominatim import get_country_bbox


@patch("src.api.nominatim.requests.get")
def test_get_country_bbox_success(mock_get):
    """Успешное получение bounding box для страны."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {"boundingbox": ["47.2701114", "55.099161", "5.8663153", "15.0419319"]}
    ]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    min_lat, max_lat, min_lon, max_lon = get_country_bbox("Germany")

    assert min_lat == 47.2701114
    assert max_lat == 55.099161
    assert min_lon == 5.8663153
    assert max_lon == 15.0419319
    mock_get.assert_called_once()


@patch("src.api.nominatim.requests.get")
def test_get_country_bbox_not_found(mock_get):
    """Страна не найдена — пустой ответ API."""
    mock_response = Mock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Страна не найдена"):
        get_country_bbox("Narnia")


@patch("src.api.nominatim.requests.get")
def test_get_country_bbox_http_error(mock_get):
    """Ошибка HTTP — исключение пробрасывается дальше."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("500 Server Error")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="500 Server Error"):
        get_country_bbox("Germany")