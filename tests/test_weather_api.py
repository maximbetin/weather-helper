import pytest
from unittest.mock import patch, MagicMock
from src.core.weather_api import fetch_weather_data
from src.core.locations import LOCATIONS, Location


def test_fetch_weather_data_invalid_location():
  # Test with invalid location
  with pytest.raises(AttributeError):
    fetch_weather_data(None)  # type: ignore


@patch('src.core.weather_api._make_request')
def test_fetch_weather_data_api_error(mock_make_request):
  # Mock API error response
  mock_make_request.return_value = None

  # Test with API error
  test_location = next(iter(LOCATIONS.values()))
  assert fetch_weather_data(test_location) is None


@patch('src.core.weather_api._make_request')
def test_fetch_weather_data_success(mock_make_request):
  # Mock successful API response
  mock_make_request.return_value = {
      "properties": {
          "timeseries": [
              {"time": "2024-03-15T12:00:00Z", "data": {}},
              {"time": "2024-03-15T13:00:00Z", "data": {}},
              {"time": "2024-03-15T14:00:00Z", "data": {}},
              {"time": "2024-03-15T15:00:00Z", "data": {}},
              {"time": "2024-03-15T16:00:00Z", "data": {}},
          ]
      }
  }

  # Test with successful API response from complete endpoint
  test_location = next(iter(LOCATIONS.values()))
  result = fetch_weather_data(test_location)
  assert result is not None
  assert len(result["properties"]["timeseries"]) >= 5


@patch('src.core.weather_api._make_request')
def test_fetch_weather_data_fallback_to_compact(mock_make_request):
  # Mock response from complete endpoint with insufficient data
  mock_make_request.side_effect = [
      {
          "properties": {
              "timeseries": [
                  {"time": "2024-03-15T12:00:00Z", "data": {}}
              ]
          }
      },
      {
          "properties": {
              "timeseries": [
                  {"time": "2024-03-15T12:00:00Z", "data": {}},
                  {"time": "2024-03-15T13:00:00Z", "data": {}},
              ]
          }
      }
  ]

  # Test that the compact endpoint is called
  test_location = next(iter(LOCATIONS.values()))
  result = fetch_weather_data(test_location)
  assert result is not None
  assert len(result["properties"]["timeseries"]) == 2
  assert mock_make_request.call_count == 2
