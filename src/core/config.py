"""
Configuration constants and type definitions for the Weather Helper application.
"""

import logging
from datetime import date, datetime
from functools import lru_cache
from typing import Optional, Union

import pytz

logger = logging.getLogger(__name__)

# Type definitions
NumericType = Union[int, float]

# API settings
PROJECT_URL = "https://github.com/maximbetin/weather-helper"
MET_NORWAY_SOURCE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/"
MET_NORWAY_LICENSE_URL = "https://api.met.no/doc/License"
USER_AGENT = f"WeatherHelper ({PROJECT_URL})"
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
API_URL_COMPACT = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


# Fallback time zone for locations that do not declare their own.
TIMEZONE = "Europe/Madrid"

# Weather display settings
FORECAST_DAYS = 7  # Max days for forecast processing
DAYLIGHT_END_HOUR = 20
DAYLIGHT_START_HOUR = 8


# Utility functions
@lru_cache(maxsize=None)
def get_timezone(timezone_name: Optional[str] = None):
    """Get a timezone object, falling back to the application default.

    Every forecast is interpreted in the time zone of the place it describes,
    so callers pass the location's own zone. An unknown zone name falls back to
    the application default rather than failing a whole forecast load.
    """
    if not timezone_name:
        return pytz.timezone(TIMEZONE)
    try:
        return pytz.timezone(timezone_name)
    except pytz.UnknownTimeZoneError:
        logger.warning(
            "Unknown time zone %r; falling back to %s", timezone_name, TIMEZONE
        )
        return pytz.timezone(TIMEZONE)


def get_current_datetime(timezone_name: Optional[str] = None) -> datetime:
    """Get the current datetime in a location's time zone."""
    return datetime.now(get_timezone(timezone_name))


def get_current_date(timezone_name: Optional[str] = None) -> date:
    """Get the current date in a location's time zone."""
    return get_current_datetime(timezone_name).date()


def safe_average(values: list[NumericType]) -> float | None:
    """Calculate the average of a list of values, handling empty lists."""
    if not values:
        return None
    return sum(values) / len(values)
