import pytest

from src.core.locations import Location


@pytest.fixture
def test_location():
  """Fixture providing a test location."""
  return Location("test", "Test City", 40.7128, -74.0060)


@pytest.fixture
def sample_weather_data():
  """Fixture providing sample weather data."""
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
                              "wind_speed": 5.0,
                              "precipitation_amount": 0.0,
                              "cloud_area_fraction": 30.0
                          }
                      },
                      "next_1_hours": {
                          "details": {
                              "precipitation_amount": 0.0
                          },
                          "summary": {
                              "symbol_code": "partlycloudy_day"
                          }
                      }
                  }
              }
          ]
      }
  }
