import pytest
from datetime import datetime, timedelta
from src.core.evaluation import (
    get_weather_score,
    get_block_type,
    extract_blocks,
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


def test_extract_blocks():
  # Create a sequence of hourly weather objects
  base_time = datetime.now()
  hours = [
      HourlyWeather(
          time=base_time + timedelta(hours=i),
          symbol=symbol,
          weather_score=7 if symbol in ["clearsky", "fair"] else -3 if "rain" in symbol else 1,
          temp_score=0,
          wind_score=0,
          cloud_score=0,
          precip_prob_score=0
      )
      for i, symbol in enumerate([
          "clearsky", "clearsky", "clearsky",  # 3 sunny hours
          "cloudy", "cloudy",  # 2 cloudy hours
          "lightrain", "lightrain", "lightrain",  # 3 rainy hours
          "clearsky", "clearsky"  # 2 sunny hours
      ])
  ]

  # Test block extraction with minimum length 2
  blocks = extract_blocks(hours, min_block_len=2)
  assert len(blocks) == 4
  assert len(blocks[0][0]) == 3
  assert blocks[0][1] == WeatherBlockType.SUNNY
  assert len(blocks[1][0]) == 2
  assert blocks[1][1] == WeatherBlockType.CLOUDY
  assert len(blocks[2][0]) == 3
  assert blocks[2][1] == WeatherBlockType.RAINY
  assert len(blocks[3][0]) == 2
  assert blocks[3][1] == WeatherBlockType.SUNNY

  # Test with minimum length 3
  blocks = extract_blocks(hours, min_block_len=3)
  assert len(blocks) == 2
  assert len(blocks[0][0]) == 3
  assert blocks[0][1] == WeatherBlockType.SUNNY
  assert len(blocks[1][0]) == 3
  assert blocks[1][1] == WeatherBlockType.RAINY

  # Test with empty input
  assert extract_blocks([]) == []


def test_find_optimal_weather_block_empty():
  assert find_optimal_weather_block([]) is None


def test_process_forecast_empty():
  assert process_forecast({}, "Test Location") is None
