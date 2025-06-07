"""
This module contains utility functions for formatting data for display in the GUI.
"""
import re
from datetime import date, datetime
from typing import Union


def format_datetime(dt: Union[datetime, date], format_str: str) -> str:
  """Format a datetime or date object according to the provided format string.

  Args:
      dt: The datetime or date to format
      format_str: The format string to use

  Returns:
      str: Formatted datetime string
  """
  return dt.strftime(format_str)


def format_time(dt: datetime) -> str:
  """Format a datetime object to display time.

  Args:
      dt: The datetime to format

  Returns:
      str: Formatted time string (e.g., "14:30")
  """
  return format_datetime(dt, "%H:%M")


def format_date(dt: Union[datetime, date]) -> str:
  """Format a date or datetime object to display date.

  Args:
      dt: The date or datetime to format

  Returns:
      str: Formatted date string (e.g., "Mon, 15 Jun")
  """
  if isinstance(dt, datetime):
    dt = dt.date()
  return format_datetime(dt, "%a, %d %b")


def format_human_date(d: date) -> str:
  """Format a date object into a human-readable string.

  Args:
      d: The date to format.

  Returns:
      A string in the format 'Month Day (Weekday)', e.g., 'June 6th (Friday)'.
  """
  day = d.day
  suffix = 'th' if 11 <= day <= 13 else {
      1: 'st',
      2: 'nd',
      3: 'rd'
  }.get(day % 10, 'th')
  return d.strftime(f"%B {day}{suffix}, %A")


def get_weather_description(symbol: str) -> str:
  """Return a human-readable weather description from a symbol code.

  Args:
      symbol: The weather symbol code.

  Returns:
      A human-readable weather description.
  """
  weather_map = {
      'clearsky': 'Clear Sky',
      'fair': 'Fair',
      'partlycloudy': 'Partly Cloudy',
      'cloudy': 'Cloudy',
      'lightrain': 'Light Rain',
      'lightrainshowers': 'Light Rain Showers',
      'rain': 'Rain',
      'rainshowers': 'Rain Showers',
      'heavyrain': 'Heavy Rain',
      'heavyrainshowers': 'Heavy Rain Showers',
      'lightsnow': 'Light Snow',
      'snow': 'Snow',
      'fog': 'Fog',
      'thunderstorm': 'Thunderstorm',
      'sleet': 'Sleet',
      'lightsleet': 'Light Sleet',
      'sleetshowers': 'Sleet Showers',
      'lightsleetshowers': 'Light Sleet Showers',
      'heavysnow': 'Heavy Snow',
      'heavysnowshowers': 'Heavy Snow Showers',
  }
  s = symbol.lower() if symbol else ''
  if s in weather_map:
    return weather_map[s]
  # Fallback: Insert space before uppercase letters (except the first)
  return re.sub(r'(?<!^)(?=[A-Z])', ' ',
                s).replace('  ', ' ').strip().capitalize()


def format_column(text: str, width: int) -> str:
  """Format a column with proper width accounting for ANSI color codes.

  Args:
      text: The text to format (may include ANSI color codes)
      width: The desired visual width of the column

  Returns:
      Formatted text with proper spacing
  """
  # ANSI color codes don't affect visual width, so we need to handle them specially
  # Use regex to remove all ANSI escape codes for length calculation
  visible_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
  padding = width - len(visible_text)
  if padding < 0:
    padding = 0
  return f"{text}{' ' * padding}"
