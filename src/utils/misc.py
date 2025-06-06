"""
Utility functions used across the application.
"""
import re
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, TypeVar, Union

import pytz

from src.core.config import TIMEZONE, WEATHER_SYMBOLS
from src.core.locations import LOCATIONS

T = TypeVar('T')

# Cache the timezone object to avoid repeatedly creating it
_TIMEZONE_CACHE = None


def get_timezone():
  """Get the application timezone object.

  Returns:
      pytz.timezone: The timezone object
  """
  global _TIMEZONE_CACHE
  if _TIMEZONE_CACHE is None:
    _TIMEZONE_CACHE = pytz.timezone(TIMEZONE)
  return _TIMEZONE_CACHE


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


# Consolidated value handling utilities
def is_value_valid(value: Optional[Union[int, float]]) -> bool:
  """Check if a numeric value is valid (not None and is a number).

  Args:
      value: The value to check

  Returns:
      bool: True if the value is a valid number
  """
  return value is not None and isinstance(value, (int, float))


def get_value_or_default(value: Optional[T], default: T) -> T:
  """Get a value if it's not None, otherwise return the default.
  This is a generic utility that works with any type.

  Args:
      value: The value to check
      default: Default value to return if value is None

  Returns:
      The value if not None, otherwise the default
  """
  return value if value is not None else default


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


def get_weather_description_from_counts(sunny_hours: int, partly_cloudy_hours: int, rainy_hours: int,
                                        avg_precip_prob: Optional[float] = None) -> str:
  """Determine overall weather description based on hour counts.

  Args:
      sunny_hours: Number of sunny hours
      partly_cloudy_hours: Number of partly cloudy hours
      rainy_hours: Number of rainy hours
      avg_precip_prob: Average precipitation probability

  Returns:
      str: Description of the overall weather
  """
  # First check if there's significant rain
  if rainy_hours > 0:
    return f"Rain ({rainy_hours}h)"

  # Determine the dominant condition
  max_hours = max(sunny_hours, partly_cloudy_hours, 0)  # Ensure non-negative

  # Format precipitation warning if needed
  precip_warning = ""
  if avg_precip_prob is not None and avg_precip_prob > 40:
    precip_warning = f" - {avg_precip_prob:.0f}% rain"

  if max_hours == 0:
    return "Mixed" + precip_warning
  elif sunny_hours == max_hours:
    return "Sunny" + precip_warning
  elif partly_cloudy_hours == max_hours:
    return "Partly Cloudy" + precip_warning
  else:
    return "Mixed" + precip_warning


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


def get_location_display_name(location_key: str) -> str:
  """Get the display name for a location key.

  Args:
      location_key: The location key

  Returns:
      str: The location display name
  """
  return LOCATIONS[location_key].name

# Type alias for numeric types
NumericType = Union[int, float]


def get_weather_score(symbol: Optional[str]) -> int:
  """Return weather score from symbol code.

  Args:
      symbol: Weather symbol code

  Returns:
      Integer score representing the weather condition quality
  """
  if not symbol or not isinstance(symbol, str):
    return 0
  _, score = WEATHER_SYMBOLS.get(symbol, ("", 0))
  return score


def temp_score(temp: Optional[NumericType]) -> int:
  """Rate temperature for outdoor comfort on a scale of -10 to 8.

  Args:
      temp: Temperature in Celsius

  Returns:
      Integer score representing temperature comfort
  """
  if temp is None or not isinstance(temp, (int, float)):
    return 0

  # Temperature ranges and their scores
  temp_ranges = [
      ((18, 23), 8),    # Ideal temperature
      ((15, 18), 6),    # Slightly cool but pleasant
      ((23, 26), 6),    # Slightly warm but pleasant
      ((10, 15), 4),    # Cool
      ((26, 30), 3),    # Warm
      ((5, 10), 0),     # Cold
      ((30, 33), -2),   # Hot
      ((0, 5), -5),     # Very cold
      ((33, 36), -5),   # Very hot
      ((-5, 0), -8),    # Extremely cold
      ((36, 40), -8),   # Extremely hot
      (None, -10)       # Beyond extreme temperatures
  ]

  for (range_tuple, score_value) in temp_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= temp <= high:
      return score_value

  return -10  # Default for extreme temperatures


def wind_score(wind_speed: Optional[NumericType]) -> int:
  """Rate wind speed comfort on a scale of -10 to 0.

  Args:
      wind_speed: Wind speed in m/s

  Returns:
      Integer score representing wind comfort
  """
  if wind_speed is None or not isinstance(wind_speed, (int, float)):
    return 0

  # Wind speed ranges and their scores
  wind_ranges = [
      ((0, 1), 0),      # Calm
      ((1, 2), -1),     # Light air
      ((2, 3.5), -2),   # Light breeze
      ((3.5, 5), -3),   # Gentle breeze
      ((5, 8), -5),     # Moderate breeze
      ((8, 10.5), -7),  # Fresh breeze
      ((10.5, 13), -8),  # Strong breeze
      ((13, 15.5), -9),  # Near gale
      (None, -10)       # Gale and above
  ]

  for (range_tuple, score_value) in wind_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= wind_speed < high:
      return score_value

  # If we get here, wind_speed is >= 15.5
  return -10


def cloud_score(cloud_coverage: Optional[NumericType]) -> int:
  """Rate cloud coverage for outdoor activities on a scale of -5 to 5.

  Args:
      cloud_coverage: Cloud coverage percentage (0-100)

  Returns:
      Integer score representing cloud cover impact
  """
  if cloud_coverage is None or not isinstance(cloud_coverage, (int, float)):
    return 0

  # Cloud coverage ranges and their scores
  cloud_ranges = [
      ((0, 10), 5),     # Clear
      ((10, 25), 3),    # Few clouds
      ((25, 50), 1),    # Partly cloudy
      ((50, 75), -2),   # Mostly cloudy
      ((75, 90), -3),   # Very cloudy
      (None, -5)        # Overcast
  ]

  for (range_tuple, score_value) in cloud_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= cloud_coverage < high:
      return score_value

  return -5  # Default for high cloud coverage


def precip_probability_score(probability: Optional[NumericType]) -> int:
  """Rate precipitation probability on a scale of -10 to 0.

  Args:
      probability: Precipitation probability percentage (0-100)

  Returns:
      Integer score representing precipitation probability impact
  """
  if probability is None or not isinstance(probability, (int, float)):
    return 0

  # Precipitation probability ranges and their scores
  precip_ranges = [
      ((0, 5), 0),      # Very unlikely
      ((5, 15), -1),    # Unlikely
      ((15, 30), -3),   # Slight chance
      ((30, 50), -5),   # Moderate chance
      ((50, 70), -7),   # Likely
      ((70, 85), -9),   # Very likely
      (None, -10)       # Almost certain
  ]

  for (range_tuple, score_value) in precip_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= probability < high:
      return score_value

  return -10  # Default for high precipitation probability


def extract_base_symbol(symbol_code):
  """Extract the base symbol from a symbol code.

  Args:
      symbol_code: The full symbol code (e.g., 'partlycloudy_day')

  Returns:
      str: Base symbol without time of day suffix
  """
  if not symbol_code:
    return "unknown"

  return symbol_code.split('_')[0] if '_' in symbol_code else symbol_code


def get_block_type(hour_obj):
  """Determine weather block type from hour object.

  Args:
      hour_obj: HourlyWeather object

  Returns:
      str: Weather type ("sunny", "rainy", or "cloudy")
  """
  s = hour_obj.symbol  # symbol is already base form
  if s in ("clearsky", "fair"):
    return "sunny"
  if "rain" in s:
    return "rainy"
  return "cloudy"


def extract_blocks(hours, min_block_len=2):
  """Find consecutive blocks of hours with similar weather type.

  Args:
      hours: List of HourlyWeather objects
      min_block_len: Minimum number of hours to consider a block

  Returns:
      List of (hour_block, weather_type) tuples
  """
  if not hours:
    return []

  # Ensure hours are HourlyWeather objects and sorted
  sorted_hours = sorted(hours, key=lambda x: x.time)  # Sort by full datetime
  blocks = []
  current_block = [sorted_hours[0]]

  current_type = get_block_type(sorted_hours[0])
  for hour_obj in sorted_hours[1:]:
    hour_type = get_block_type(hour_obj)
    # Check for consecutive hours (time difference of 1 hour)
    if hour_type == current_type and (hour_obj.time - current_block[-1].time) == timedelta(hours=1):
      current_block.append(hour_obj)
    else:
      if len(current_block) >= min_block_len:
        blocks.append((current_block, current_type))
      current_block = [hour_obj]
      current_type = hour_type

  # Don't forget the last block
  if len(current_block) >= min_block_len:
    blocks.append((current_block, current_type))

  return blocks
