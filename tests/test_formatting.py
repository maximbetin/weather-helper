from datetime import date, datetime
from src.gui.formatting import (
    format_time,
    format_date,
    get_weather_description,
)


def test_format_time():
  dt = datetime(2023, 1, 1, 14, 30)
  assert format_time(dt) == "14:30"


def test_format_date_default():
  dt = date(2023, 6, 15)
  assert format_date(dt) == "Thu, 15 Jun"


def test_get_weather_description():
  assert get_weather_description("clearsky") == "Clear Sky"
  assert get_weather_description("cloudy") == "Cloudy"
  assert get_weather_description("heavyrain") == "Heavy Rain"
  assert get_weather_description("invalid_symbol") == "Invalid Symbol"
  assert get_weather_description("partly_cloudy") == "Partly Cloudy"
  assert get_weather_description(None) == ""
