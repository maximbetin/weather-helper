"""
Tests for weather API functionality.
"""

from unittest.mock import Mock, patch

import requests

from src.core.locations import Location
from src.core.weather_api import _make_request, fetch_weather_data

def test_fetch_weather_data_invalid_location():
    """Test fetch_weather_data with invalid location coordinates."""
    location = Location("invalid", "Invalid", -999, -999)

    with patch('src.core.weather_api._make_request') as mock_request:
        # Mock both complete and compact endpoints failing
        mock_request.return_value = None

        result = fetch_weather_data(location)
        assert result is None

def test_fetch_weather_data_api_error():
    """Test fetch_weather_data when API returns errors."""
    location = Location("test", "Test", 40.0, -3.0)

    with patch('src.core.weather_api._make_request') as mock_request:
        # Simulate API error
        mock_request.side_effect = [None, None]  # Both endpoints fail

        result = fetch_weather_data(location)
        assert result is None

def test_fetch_weather_data_success():
    """Test successful weather data fetch."""
    location = Location("madrid", "Madrid", 40.4168, -3.7038)

    mock_data = {
        "properties": {
            "timeseries": [{"time": "2024-03-15T10:00:00Z"} for _ in range(10)]  # Sufficient data
        }
    }

    with patch('src.core.weather_api._make_request') as mock_request:
        mock_request.return_value = mock_data

        result = fetch_weather_data(location)
        assert result == mock_data
        assert result is not None and len(result["properties"]["timeseries"]) >= 5

def test_fetch_weather_data_fallback_to_compact():
    """Test fallback to compact endpoint when complete endpoint has insufficient data."""
    location = Location("test", "Test", 40.0, -3.0)

    # Mock insufficient data from complete endpoint
    insufficient_data = {
        "properties": {
            "timeseries": [{"time": "2024-03-15T10:00:00Z"}]  # Only 1 entry, less than 5
        }
    }

    # Mock sufficient data from compact endpoint
    sufficient_data = {
        "properties": {
            "timeseries": [{"time": "2024-03-15T10:00:00Z"} for _ in range(6)]
        }
    }

    with patch('src.core.weather_api._make_request') as mock_request:
        # First call (complete) returns insufficient data, second call (compact) returns good data
        mock_request.side_effect = [insufficient_data, sufficient_data]

        result = fetch_weather_data(location)
        assert result == sufficient_data
        assert mock_request.call_count == 2

def test_make_request_success():
    """Test _make_request with successful response."""
    location = Location("test", "Test", 40.0, -3.0)
    headers = {"User-Agent": "TestAgent"}

    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {"test": "data"}
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response) as mock_get:
        result = _make_request("http://test.url", location, headers)

        assert result == {"test": "data"}
        mock_get.assert_called_once_with("http://test.url", headers=headers, timeout=10)

def test_make_request_request_exception():
    """Test _make_request with requests.RequestException."""
    location = Location("test", "Test", 40.0, -3.0)
    headers = {"User-Agent": "TestAgent"}

    with patch('requests.get', side_effect=requests.exceptions.RequestException("Network error")) as mock_get:
        result = _make_request("http://test.url", location, headers)

        assert result is None

def test_make_request_value_error():
    """Test _make_request with JSON decode error."""
    location = Location("test", "Test", 40.0, -3.0)
    headers = {"User-Agent": "TestAgent"}

    # Mock response that raises ValueError on json()
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        result = _make_request("http://test.url", location, headers)

        assert result is None

def test_make_request_http_error():
    """Test _make_request with HTTP error."""
    location = Location("test", "Test", 40.0, -3.0)
    headers = {"User-Agent": "TestAgent"}

    # Mock response that raises HTTPError
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")

    with patch('requests.get', return_value=mock_response):
        result = _make_request("http://test.url", location, headers)

        assert result is None

def test_fetch_weather_data_complete_endpoint_empty_timeseries():
    """Test fetch_weather_data when complete endpoint returns empty timeseries."""
    location = Location("test", "Test", 40.0, -3.0)

    # Mock data with empty timeseries
    empty_data = {
        "properties": {
            "timeseries": []
        }
    }

    # Mock sufficient data from compact endpoint
    sufficient_data = {
        "properties": {
            "timeseries": [{"time": "2024-03-15T10:00:00Z"} for _ in range(6)]
        }
    }

    with patch('src.core.weather_api._make_request') as mock_request:
        # First call returns empty data, second call returns good data
        mock_request.side_effect = [empty_data, sufficient_data]

        result = fetch_weather_data(location)
        assert result == sufficient_data
        assert mock_request.call_count == 2

def test_fetch_weather_data_complete_endpoint_no_properties():
    """Test fetch_weather_data when complete endpoint returns no properties."""
    location = Location("test", "Test", 40.0, -3.0)

    # Mock data without properties
    no_properties_data = {"other_key": "value"}

    # Mock sufficient data from compact endpoint
    sufficient_data = {
        "properties": {
            "timeseries": [{"time": "2024-03-15T10:00:00Z"} for _ in range(6)]
        }
    }

    with patch('src.core.weather_api._make_request') as mock_request:
        # First call returns data without properties, second call returns good data
        mock_request.side_effect = [no_properties_data, sufficient_data]

        result = fetch_weather_data(location)
        assert result == sufficient_data
        assert mock_request.call_count == 2
