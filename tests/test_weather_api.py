import pytest
from unittest.mock import patch, MagicMock
from src.core.weather_api import fetch_weather_data
from src.core.locations import LOCATIONS, Location
import requests


def test_fetch_weather_data_invalid_location():
  # Test with invalid location
  with pytest.raises(AttributeError):
    fetch_weather_data(None)  # type: ignore


@patch('src.core.weather_api.requests.get')
def test_fetch_weather_data_api_error(mock_get):
  # Mock API error response
  mock_response = MagicMock()
  mock_response.status_code = 500
  mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
  mock_get.return_value = mock_response

  # Test with API error
  test_location = next(iter(LOCATIONS.values()))
  assert fetch_weather_data(test_location) is None


@patch('src.core.weather_api.requests.get')
def test_fetch_weather_data_success(mock_get):
  # Mock successful API response
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.json.return_value = {
      "properties": {
          "timeseries": [
              {
                  "time": "2024-03-15T12:00:00Z",
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": 20,
                              "wind_speed": 5,
                              "relative_humidity": 60,
                              "cloud_area_fraction": 20
                          }
                      },
                      "next_1_hours": {
                          "summary": {
                              "symbol_code": "clearsky"
                          },
                          "details": {
                              "precipitation_amount": 0,
                              "probability_of_precipitation": 0
                          }
                      }
                  }
              }
          ]
      }
  }
  mock_get.return_value = mock_response

  # Test with successful API response
  test_location = next(iter(LOCATIONS.values()))
  result = fetch_weather_data(test_location)
  assert result is not None
  assert "properties" in result
  assert "timeseries" in result["properties"]
