"""
Utility functions used across the application.
"""
from functools import lru_cache
from datetime import date, datetime
from typing import List, Optional, TypeVar, Union

import pytz

from src.core.config import TIMEZONE

T = TypeVar('T')


@lru_cache(maxsize=None)
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


def safe_average(values: List[Union[int, float]]) -> Optional[float]:
  """Calculate the average of a list of values, handling empty lists.

  Args:
      values: List of numeric values

  Returns:
      Optional[float]: Average value or None if list is empty
  """
  if not values:
    return None
  return sum(values) / len(values)
