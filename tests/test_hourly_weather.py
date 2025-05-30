from datetime import datetime

import pytest

from src.hourly_weather import HourlyWeather


@pytest.fixture
def sample_hourly_weather():
  """Fixture providing a sample HourlyWeather instance."""
  return HourlyWeather(
      time=datetime(2024, 3, 20, 12, 0),
      temp=20.0,
      wind=5.0,
      humidity=65.0,
      cloud_coverage=30.0,
      precipitation_amount=0.0,
      symbol="partlycloudy_day",
      weather_score=8,
      temp_score=7,
      wind_score=9,
      cloud_score=8,
      precip_prob_score=10
  )


def test_hourly_weather_creation(sample_hourly_weather):
  """Test creating an HourlyWeather instance with valid data."""
  assert sample_hourly_weather.time == datetime(2024, 3, 20, 12, 0)
  assert sample_hourly_weather.temp == 20.0
  assert sample_hourly_weather.wind == 5.0
  assert sample_hourly_weather.humidity == 65.0
  assert sample_hourly_weather.cloud_coverage == 30.0
  assert sample_hourly_weather.precipitation_amount == 0.0
  assert sample_hourly_weather.symbol == "partlycloudy_day"


def test_hourly_weather_derived_fields(sample_hourly_weather):
  """Test that derived fields are calculated correctly."""
  assert sample_hourly_weather.hour == 12
  assert sample_hourly_weather.total_score == 42  # Sum of all scores


def test_hourly_weather_minimal_creation():
  """Test creating an HourlyWeather instance with minimal data."""
  weather = HourlyWeather(
      time=datetime(2024, 3, 20, 12, 0),
      symbol="sunny",
      weather_score=10,
      temp_score=0,
      wind_score=0,
      cloud_score=0,
      precip_prob_score=0
  )
  assert weather.time == datetime(2024, 3, 20, 12, 0)
  assert weather.symbol == "sunny"
  assert weather.total_score == 10


def test_hourly_weather_score_calculation():
  """Test score calculation with different combinations."""
  weather = HourlyWeather(
      time=datetime(2024, 3, 20, 12, 0),
      symbol="sunny",
      weather_score=5,
      temp_score=5,
      wind_score=5,
      cloud_score=5,
      precip_prob_score=5
  )
  assert weather.total_score == 25


def test_hourly_weather_optional_fields():
  """Test that optional fields can be None."""
  weather = HourlyWeather(
      time=datetime(2024, 3, 20, 12, 0),
      symbol="sunny",
      weather_score=10,
      temp_score=0,
      wind_score=0,
      cloud_score=0,
      precip_prob_score=0
  )
  assert weather.temp is None
  assert weather.wind is None
  assert weather.humidity is None
  assert weather.cloud_coverage is None
