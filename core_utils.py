"""
Core utility functions used across the application.
"""

import pytz
from datetime import datetime, date, time, timedelta
from typing import Optional, Union, List, TypeVar, Any

from config import TIMEZONE, WEATHER_SYMBOLS

T = TypeVar('T')


def get_timezone():
  """Get the application timezone object.

  Returns:
      pytz.timezone: The timezone object
  """
  return pytz.timezone(TIMEZONE)


def get_current_datetime() -> datetime:
  """Get the current datetime in the application timezone.

  Returns:
      datetime: Current datetime in application timezone
  """
  return datetime.now(get_timezone())


def get_current_date() -> date:
  """Get the current date in the application timezone.

  Returns:
      date: Current date in application timezone
  """
  return get_current_datetime().date()


def format_time(dt: datetime) -> str:
  """Format a datetime object to display time.

  Args:
      dt: The datetime to format

  Returns:
      str: Formatted time string (e.g., "14:30")
  """
  return dt.strftime("%H:%M")


def format_date(dt: Union[datetime, date]) -> str:
  """Format a date or datetime object to display date.

  Args:
      dt: The date or datetime to format

  Returns:
      str: Formatted date string (e.g., "Mon, 15 Jun")
  """
  if isinstance(dt, datetime):
    dt = dt.date()
  return dt.strftime("%a, %d %b")


def get_weather_desc(symbol: str) -> str:
  """Return standardized weather description from symbol code.

  Args:
      symbol: Weather symbol code

  Returns:
      str: Human-readable weather description
  """
  if not symbol or not isinstance(symbol, str):
    return "Unknown"
  desc, _ = WEATHER_SYMBOLS.get(symbol, (symbol.replace('_', ' ').capitalize(), 0))
  return desc


def is_value_valid(value: Optional[Union[int, float]]) -> bool:
  """Check if a numeric value is valid (not None).

  Args:
      value: The value to check

  Returns:
      bool: True if the value is a valid number
  """
  return value is not None and isinstance(value, (int, float))


def safe_average(values: List[Union[int, float]]) -> Optional[float]:
  """Calculate the average of a list of values, handling empty lists.

  Args:
      values: List of numeric values

  Returns:
      Optional[float]: Average value or None if list is empty
  """
  valid_values = [v for v in values if is_value_valid(v)]
  if not valid_values:
    return None
  return sum(valid_values) / len(valid_values)


def get_or_default(value: Optional[T], default: T) -> T:
  """Get a value if it's not None, otherwise return the default.

  Args:
      value: The value to check
      default: Default value to return if value is None

  Returns:
      The value if not None, otherwise the default
  """
  return value if value is not None else default


def safe_get_numeric(value: Optional[Union[int, float]], default: Union[int, float] = 0) -> Union[int, float]:
  """Safely get a numeric value, returning a default if None.

  Args:
      value: The numeric value to check
      default: Default value to return if value is None

  Returns:
      The value if it's a valid number, otherwise the default
  """
  if is_value_valid(value):
    return value  # type: ignore
  return default
