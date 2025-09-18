"""
Configuration constants and type definitions for the Weather Helper application.
"""

from datetime import date, datetime
from functools import lru_cache
from typing import Union

import pytz

# Type definitions
NumericType = Union[int, float]

# API settings
USER_AGENT = "WeatherHelper/1.0"
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
API_URL_COMPACT = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
FORECAST_DAYS = 7  # Max days for forecast processing
DAYLIGHT_END_HOUR = 20
DAYLIGHT_START_HOUR = 8


# Utility functions
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


def safe_average(values: list[NumericType]) -> float | None:
    """Calculate the average of a list of values, handling empty lists."""
    if not values:
        return None
    return sum(values) / len(values)
