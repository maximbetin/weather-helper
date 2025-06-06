import pytest
from datetime import datetime, date
from src.core.evaluation import (
    process_forecast,
    get_available_dates,
    get_time_blocks_for_date,
    get_top_locations_for_date
)
from src.core.hourly_weather import HourlyWeather


def test_get_available_dates():
  # Test with empty forecast
  assert get_available_dates({}) == []

  # Test with valid forecast
  test_date = date(2024, 3, 15)
  test_forecast = {
      "daily_forecasts": {
          test_date: [
              HourlyWeather(
                  time=datetime(2024, 3, 15, 12),
                  temp=20,
                  wind=5,
                  humidity=60,
                  cloud_coverage=20,
                  fog=0,
                  wind_direction=180,
                  wind_gust=10,
                  precipitation_amount=0,
                  precipitation_probability=0,
                  symbol="clearsky",
                  weather_score=10,
                  temp_score=8,
                  wind_score=9,
                  cloud_score=10,
                  precip_prob_score=10
              )
          ]
      }
  }
  assert get_available_dates(test_forecast) == [test_date]


def test_get_time_blocks_for_date():
  # Test with empty forecast
  assert get_time_blocks_for_date({}, date(2024, 3, 15)) == []

  # Test with valid forecast
  test_date = date(2024, 3, 15)
  test_hour = datetime(2024, 3, 15, 12)
  test_weather = HourlyWeather(
      time=test_hour,
      temp=20,
      wind=5,
      humidity=60,
      cloud_coverage=20,
      fog=0,
      wind_direction=180,
      wind_gust=10,
      precipitation_amount=0,
      precipitation_probability=0,
      symbol="clearsky",
      weather_score=10,
      temp_score=8,
      wind_score=9,
      cloud_score=10,
      precip_prob_score=10
  )
  test_forecast = {
      "daily_forecasts": {
          test_date: [test_weather]
      }
  }
  blocks = get_time_blocks_for_date(test_forecast, test_date)
  assert len(blocks) == 1
  assert blocks[0].time == test_hour
  assert blocks[0].temp == 20


def test_get_top_locations_for_date():
  # Test with empty data
  assert get_top_locations_for_date({}, date(2024, 3, 15)) == []

  # Test with valid data
  test_date = date(2024, 3, 15)
  test_data = {
      "loc1": {
          "day_scores": {
              test_date: type('obj', (object,), {
                  'location_name': 'Location 1',
                  'avg_score': 15,
                  'min_temp': 18,
                  'max_temp': 22,
                  'weather_description': 'Sunny'
              })
          }
      },
      "loc2": {
          "day_scores": {
              test_date: type('obj', (object,), {
                  'location_name': 'Location 2',
                  'avg_score': 10,
                  'min_temp': 15,
                  'max_temp': 20,
                  'weather_description': 'Cloudy'
              })
          }
      }
  }

  results = get_top_locations_for_date(test_data, test_date)
  assert len(results) == 2
  assert results[0]["location_name"] == "Location 1"  # Higher score
  assert results[0]["avg_score"] == 15
  assert results[1]["location_name"] == "Location 2"  # Lower score
  assert results[1]["avg_score"] == 10
