"""
Utility functions used across the application.
"""
from functools import lru_cache
from datetime import date, datetime
from typing import List, Optional

import pytz

from src.core.config import TIMEZONE
from src.core.types import NumericType


@lru_cache(maxsize=None)
def get_timezone():
  """Get the application timezone object."""
  return pytz.timezone(TIMEZONE)


def get_current_datetime() -> datetime:
  """Get the current datetime in the application timezone."""
  return datetime.now(get_timezone())


def get_current_date() -> date:
  """Get the current date in the application timezone."""
  return get_current_datetime().date()


def safe_average(values: List[NumericType]) -> Optional[float]:
  """Calculate the average of a list of values, handling empty lists."""
  if not values:
    return None
  return sum(values) / len(values)
