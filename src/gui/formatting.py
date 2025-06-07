"""
This module contains utility functions for formatting data for display in the GUI.
"""
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


def format_date(d: Union[date, datetime]) -> str:
  """Format a date or datetime object.

  Args:
      d: The date or datetime to format

  Returns:
      Formatted date string
  """
  if isinstance(d, datetime):
    d = d.date()

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
  return weather_map.get(s, s.replace("_", " ").title())
