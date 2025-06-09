import pytest
from datetime import datetime, timedelta
from src.core.evaluation import (
    get_weather_score,
    find_optimal_weather_block,
    process_forecast
)
from src.core.hourly_weather import HourlyWeather


def test_get_weather_score():
  # Test valid weather symbols
  assert get_weather_score("clearsky") == 5
  assert get_weather_score("fair") == 3
  assert get_weather_score("partlycloudy") == 1
  assert get_weather_score("cloudy") == -1
  assert get_weather_score("lightrain") == -3
  assert get_weather_score("heavyrain") == -10
  assert get_weather_score("thunderstorm") == -15

  # Test invalid inputs
  assert get_weather_score(None) == 0
  assert get_weather_score("") == 0
  assert get_weather_score("invalid_symbol") == 0


def test_find_optimal_weather_block_empty():
  assert find_optimal_weather_block([]) is None


def test_process_forecast_empty():
  assert process_forecast({}, "Test Location") is None
