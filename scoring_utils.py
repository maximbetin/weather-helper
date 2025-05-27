"""
Utility functions for calculating weather-related scores.
"""

from typing import Optional, Union
from config import WEATHER_SYMBOLS

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
  """Rate temperature for outdoor comfort on a scale of -10 to 10.

  Args:
      temp: Temperature in Celsius

  Returns:
      Integer score representing temperature comfort
  """
  if temp is None or not isinstance(temp, (int, float)):
    return 0

  # Temperature ranges and their scores
  temp_ranges = [
      ((18, 24), 10),   # Ideal temperature
      ((15, 18), 8),    # Slightly cool but pleasant
      ((24, 28), 8),    # Slightly warm but pleasant
      ((10, 15), 5),    # Cool
      ((28, 32), 5),    # Warm
      ((5, 10), 0),     # Cold
      ((32, 35), 0),    # Hot
      ((0, 5), -5),     # Very cold
      ((35, 38), -5),   # Very hot
      (None, -10)       # Extreme temperatures
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
      ((0, 2), 0),      # Calm to light air
      ((2, 4), -2),     # Light breeze
      ((4, 6), -4),     # Gentle breeze
      ((6, 10), -6),    # Moderate to fresh breeze
      (None, -10)       # Strong breeze and above
  ]

  for (range_tuple, score_value) in wind_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= wind_speed < high:
      return score_value

  return -10  # Default for high wind speeds


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
      ((0, 20), 5),     # Clear to mostly clear
      ((20, 40), 3),    # Few clouds
      ((40, 60), 1),    # Partly cloudy
      ((60, 80), -2),   # Mostly cloudy
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
      ((0, 10), 0),     # Very unlikely
      ((10, 30), -2),   # Slight chance
      ((30, 50), -5),   # Moderate chance
      ((50, 70), -7),   # Likely
      (None, -10)       # Very likely
  ]

  for (range_tuple, score_value) in precip_ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if low <= probability < high:
      return score_value

  return -10  # Default for high precipitation probability
