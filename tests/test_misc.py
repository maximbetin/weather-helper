import pytest
from datetime import datetime, timedelta
from src.utils.misc import (
    get_weather_score,
    get_weather_description,
    get_weather_description_from_counts,
    get_block_type,
    extract_blocks
)
from src.core.hourly_weather import HourlyWeather


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


def test_get_weather_description():
  # Test valid weather symbols
  assert get_weather_description("clearsky") == "Clear Sky"
  assert get_weather_description("fair") == "Fair"
  assert get_weather_description("partlycloudy") == "Partly Cloudy"
  assert get_weather_description("cloudy") == "Cloudy"
  assert get_weather_description("lightrain") == "Light Rain"
  assert get_weather_description("heavyrain") == "Heavy Rain"
  assert get_weather_description("thunderstorm") == "Thunderstorm"

  # Test invalid inputs
  assert get_weather_description("") == ""
  assert get_weather_description("invalid_symbol") == "Invalid_symbol"
  assert get_weather_description("partly_cloudy") == "Partly_cloudy"


def test_get_weather_description_from_counts():
  # Test sunny conditions
  assert get_weather_description_from_counts(5, 2, 0) == "Sunny"
  assert get_weather_description_from_counts(3, 3, 0) == "Sunny"

  # Test partly cloudy conditions
  assert get_weather_description_from_counts(2, 4, 0) == "Partly Cloudy"
  assert get_weather_description_from_counts(1, 5, 0) == "Partly Cloudy"

  # Test rainy conditions
  assert get_weather_description_from_counts(2, 2, 1) == "Rain (1h)"
  assert get_weather_description_from_counts(0, 0, 3) == "Rain (3h)"

  # Test with precipitation probability
  assert get_weather_description_from_counts(5, 2, 0, 45) == "Sunny - 45% rain"
  assert get_weather_description_from_counts(2, 2, 1, 60) == "Rain (1h)"

  # Test edge cases
  assert get_weather_description_from_counts(0, 0, 0) == "Mixed"
  assert get_weather_description_from_counts(0, 0, 0, 30) == "Mixed"


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
  assert get_block_type(sunny_hour) == "sunny"
  assert get_block_type(rainy_hour) == "rainy"
  assert get_block_type(cloudy_hour) == "cloudy"


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
  assert len(blocks) == 4  # Fixed: Should find 4 blocks (3 sunny, 2 cloudy, 3 rainy, 2 sunny)
  assert len(blocks[0][0]) == 3  # First block: 3 sunny hours
  assert blocks[0][1] == "sunny"
  assert len(blocks[1][0]) == 2  # Second block: 2 cloudy hours
  assert blocks[1][1] == "cloudy"
  assert len(blocks[2][0]) == 3  # Third block: 3 rainy hours
  assert blocks[2][1] == "rainy"
  assert len(blocks[3][0]) == 2  # Fourth block: 2 sunny hours
  assert blocks[3][1] == "sunny"

  # Test with minimum length 3
  blocks = extract_blocks(hours, min_block_len=3)
  assert len(blocks) == 2  # Should find 2 blocks
  assert len(blocks[0][0]) == 3  # First block: 3 sunny hours
  assert blocks[0][1] == "sunny"
  assert len(blocks[1][0]) == 3  # Second block: 3 rainy hours
  assert blocks[1][1] == "rainy"

  # Test with empty input
  assert extract_blocks([]) == []
