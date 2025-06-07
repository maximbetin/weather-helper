"""
This module contains utility functions for formatting data for display in the GUI.
"""
import re
from datetime import date, datetime
from typing import Union, Optional


def format_time(dt: datetime) -> str:
  """Format a datetime object to display time.

  Args:
      dt: The datetime to format

  Returns:
      str: Formatted time string (e.g., "14:30")
  """
  return dt.strftime("%H:%M")


def format_date(d: Union[date, datetime], human_readable: bool = False) -> str:
  """Format a date or datetime object.

  Args:
      d: The date or datetime to format
      human_readable: If True, returns a more descriptive format

  Returns:
      Formatted date string
  """
  if isinstance(d, datetime):
    d = d.date()

  if human_readable:
    day = d.day
    suffix = 'th' if 11 <= day <= 13 else {
        1: 'st',
        2: 'nd',
        3: 'rd'
    }.get(day % 10, 'th')
    return d.strftime(f"%B {day}{suffix}, %A")
  else:
    return d.strftime("%a, %d %b")


def get_weather_description(symbol: Optional[str]) -> str:
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
  s = re.sub(r'(?<!^)(?=[A-Z])', ' ', symbol if symbol else '').strip()
  return ' '.join(word.capitalize() for word in s.split())


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
