import pytest
from unittest.mock import Mock, patch
from src.api.opensky import get_airplanes_in_bbox


@patch("src.api.opensky.requests.get")
def test_get_airplanes_in_bbox_success(mock_get):
    """Возвращает список states при успешном ответе."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "states": [
            ["abc123", "ACA101", "Canada", None, None, 10.0, 20.0, 10000, False, 250.0],
            ["def456", "DLH202", "Germany", None, None, 11.0, 21.0, 11000, False, 300.0],
        ]
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    states = get_airplanes_in_bbox(47.0, 55.0, 5.0, 15.0)

    assert len(states) == 2
    assert states[0][1] == "ACA101"
    assert states[1][1] == "DLH202"


@patch("src.api.opensky.requests.get")
def test_get_airplanes_in_bbox_empty(mock_get):
    """Когда states = None, возвращается пустой список."""
    mock_response = Mock()
    mock_response.json.return_value = {"states": None}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    states = get_airplanes_in_bbox(47.0, 55.0, 5.0, 15.0)
    assert states == []


@patch("src.api.opensky.requests.get")
def test_get_airplanes_in_bbox_no_key(mock_get):
    """Если ключа 'states' нет, возвращается пустой список."""
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    states = get_airplanes_in_bbox(47.0, 55.0, 5.0, 15.0)
    assert states == []


@patch("src.api.opensky.requests.get")
def test_get_airplanes_in_bbox_http_error(mock_get):
    """Ошибка HTTP — исключение пробрасывается."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="429"):
        get_airplanes_in_bbox(47.0, 55.0, 5.0, 15.0)