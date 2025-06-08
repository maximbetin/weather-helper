"""Tests for formatting utilities."""

import pytest
from src.gui.formatting import (
    format_temperature,
    format_percentage,
    format_wind_speed,
    format_time,
    format_date,
    get_weather_description
)
from src.gui.themes import get_rating_color
from src.core.types import NumericType


def test_format_temperature():
  assert format_temperature(25.5) == "25.5°C"
  assert format_temperature(0) == "0.0°C"
  assert format_temperature(-5.2) == "-5.2°C"
  assert format_temperature(None) == "N/A"
  assert format_temperature(100.0) == "100.0°C"
  assert format_temperature(25.555) == "25.6°C"
  assert format_temperature(-5.222) == "-5.2°C"


def test_format_percentage():
  assert format_percentage(75.5) == "76%"
  assert format_percentage(0) == "0%"
  assert format_percentage(100) == "100%"
  assert format_percentage(None) == "N/A"
  assert format_percentage(0.0) == "0%"
  assert format_percentage(100.0) == "100%"
  assert format_percentage(75.555) == "76%"
  assert format_percentage(0.222) == "0%"


def test_format_percentage_additional():
  # Custom suffix
  assert format_percentage(50, suffix=" pct") == "50 pct"
  # Negative value
  assert format_percentage(-10) == "-10%"
  # Float with decimal
  assert format_percentage(12.34) == "12%"
  # None with custom suffix
  assert format_percentage(None, suffix=" pct") == "N/A"


def test_format_wind_speed():
  assert format_wind_speed(15.5) == "15.5 m/s"
  assert format_wind_speed(0) == "0.0 m/s"
  assert format_wind_speed(100) == "100.0 m/s"
  assert format_wind_speed(None) == "N/A"
  assert format_wind_speed(0.0) == "0.0 m/s"
  assert format_wind_speed(100.0) == "100.0 m/s"
  assert format_wind_speed(15.555) == "15.6 m/s"
  assert format_wind_speed(0.222) == "0.2 m/s"


def test_format_time():
  from datetime import datetime
  assert format_time(datetime(2024, 3, 15, 9, 30)) == "09:30"
  assert format_time(datetime(2024, 3, 15, 0, 0)) == "00:00"
  assert format_time(datetime(2024, 3, 15, 23, 59)) == "23:59"


def test_format_date():
  from datetime import datetime, date
  assert format_date(date(2024, 3, 15)) == "Fri, 15 Mar"
  assert format_date(datetime(2024, 1, 1, 12, 0)) == "Mon, 01 Jan"
  assert format_date(date(2024, 12, 31)) == "Tue, 31 Dec"


def test_get_weather_description():
  assert get_weather_description("clearsky") == "Clear Sky"
  assert get_weather_description("lightrain") == "Light Rain"
  assert get_weather_description("heavysnow") == "Heavy Snow"
  assert get_weather_description("") == ""
  assert get_weather_description(None) == ""
  assert get_weather_description("unknown_code") == "Unknown Code"


def test_get_rating_color():
  assert get_rating_color("Excellent")
  assert get_rating_color("Very Good")
  assert get_rating_color("Good")
  assert get_rating_color("Fair")
  assert get_rating_color("Poor")
  # Unknown rating falls back to text color
  assert get_rating_color("N/A")
