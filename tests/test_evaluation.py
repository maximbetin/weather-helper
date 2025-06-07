import pytest
from datetime import datetime, timedelta
from src.core.evaluation import (
    get_weather_score,
    get_block_type,
    find_optimal_weather_block,
    process_forecast
)
from src.core.hourly_weather import HourlyWeather
from src.core.enums import WeatherBlockType


def test_get_weather_score():
  # Test valid weather symbols
  assert get_weather_score("clearsky") == 7
  assert get_weather_score("fair") == 5
  assert get_weather_score("partlycloudy") == 3
  assert get_weather_score("cloudy") == 1
  assert get_weather_score("lightrain") == -3
  assert get_weather_score("heavyrain") == -10
  assert get_weather_score("thunderstorm") == -15

  # Test invalid inputs
  assert get_weather_score(None) == 0
  assert get_weather_score("") == 0
  assert get_weather_score("invalid_symbol") == 0


def test_get_block_type():
  # Create test HourlyWeather objects
  sunny_hour = HourlyWeather(
      time=datetime.now(),
      symbol="clearsky",
      weather_score=7,
      temp_score=0,
      wind_score=0,
      cloud_score=0,
      precip_prob_score=0
  )

  rainy_hour = HourlyWeather(
      time=datetime.now(),
      symbol="lightrain",
      weather_score=-3,
      temp_score=0,
      wind_score=0,
      cloud_score=0,
      precip_prob_score=0
  )

  cloudy_hour = HourlyWeather(
      time=datetime.now(),
      symbol="cloudy",
      weather_score=1,
      temp_score=0,
      wind_score=0,
      cloud_score=0,
      precip_prob_score=0
  )

  # Test weather types
  assert get_block_type(sunny_hour) == WeatherBlockType.SUNNY
  assert get_block_type(rainy_hour) == WeatherBlockType.RAINY
  assert get_block_type(cloudy_hour) == WeatherBlockType.CLOUDY


def test_find_optimal_weather_block_empty():
  assert find_optimal_weather_block([]) is None


def test_process_forecast_empty():
  assert process_forecast({}, "Test Location") is None
