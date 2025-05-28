"""
Utility functions for calculating weather-related scores.
"""

from typing import Optional, Union

from core.config import WEATHER_SYMBOLS

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
