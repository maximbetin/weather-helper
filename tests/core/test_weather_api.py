from unittest.mock import Mock, patch

import pytest
import requests

from src.core.locations import Location
from src.core.weather_api import fetch_weather_data


@pytest.fixture
def mock_location():
  """Fixture providing a test location."""
  return Location("test", "Test City", 40.7128, -74.0060)


@pytest.fixture
def mock_weather_response():
  """Fixture providing a mock weather API response."""
  return {
      "properties": {
          "timeseries": [
              {
                  "time": "2024-03-20T12:00:00Z",
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": 20.0,
                              "relative_humidity": 65.0,
                              "wind_speed": 5.0
                          }
                      }
                  }
              }
          ]
      }
  }


def test_fetch_weather_data_success(mock_location, mock_weather_response):
  """Test successful weather data fetch."""
  with patch('requests.get') as mock_get:
    # Configure mock response
    mock_response = Mock()
    mock_response.json.return_value = mock_weather_response
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Call the function
    result = fetch_weather_data(mock_location)

    # Verify the result
    assert result == mock_weather_response
    mock_get.assert_called_once()


def test_fetch_weather_data_timeout(mock_location):
  """Test weather data fetch with timeout error."""
  with patch('requests.get') as mock_get:
    # Configure mock to raise timeout
    mock_get.side_effect = requests.exceptions.Timeout()

    # Call the function
    result = fetch_weather_data(mock_location)

    # Verify the result
    assert result is None
    mock_get.assert_called_once()


def test_fetch_weather_data_invalid_json(mock_location):
  """Test weather data fetch with invalid JSON response."""
  with patch('requests.get') as mock_get:
    # Configure mock response with invalid JSON
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Call the function
    result = fetch_weather_data(mock_location)

    # Verify the result
    assert result is None
    mock_get.assert_called_once()


def test_fetch_weather_data_http_error(mock_location):
  """Test weather data fetch with HTTP error."""
  with patch('requests.get') as mock_get:
    # Configure mock to raise HTTP error
    mock_get.side_effect = requests.exceptions.RequestException("HTTP Error")

    # Call the function
    result = fetch_weather_data(mock_location)

    # Verify the result
    assert result is None
    mock_get.assert_called_once()
