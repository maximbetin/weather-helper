import pytest
from datetime import datetime, date
from src.gui.formatting import (
    format_datetime,
    format_time,
    format_date,
    format_human_date,
    get_weather_description,
    format_column,
)


def test_format_datetime():
  dt = datetime(2023, 1, 1, 14, 30)
  assert format_datetime(dt, "%Y-%m-%d %H:%M") == "2023-01-01 14:30"


def test_format_time():
  dt = datetime(2023, 1, 1, 14, 30)
  assert format_time(dt) == "14:30"


def test_format_date():
  dt = datetime(2023, 6, 15)
  assert format_date(dt) == "Thu, 15 Jun"


def test_format_human_date():
  d = date(2023, 6, 6)
  assert format_human_date(d) == "June 6th, Tuesday"


def test_get_weather_description():
  assert get_weather_description("clearsky") == "Clear Sky"
  assert get_weather_description("lightrain") == "Light Rain"
  assert get_weather_description("heavyrainshowers") == "Heavy Rain Showers"
  assert get_weather_description("sleet") == "Sleet"


def test_format_column():
  assert format_column("test", 10) == "test      "
  assert format_column("test", 3) == "test"
