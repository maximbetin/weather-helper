"""
Utility functions for calculating weather-related scores.
"""

from config import WEATHER_SYMBOLS


def get_weather_score(symbol):
  """Return weather score from symbol code."""
  if not symbol or not isinstance(symbol, str):
    return 0
  base = symbol
  _, score = WEATHER_SYMBOLS.get(base, ("", 0))
  return score


def temp_score(temp):
  """Rate temperature for outdoor comfort on a scale of -10 to 10."""
  if temp is None or not isinstance(temp, (int, float)):
    return 0
  if 18 <= temp <= 24:
    return 10
  elif 15 <= temp < 18 or 24 < temp <= 28:
    return 8
  elif 10 <= temp < 15 or 28 < temp <= 32:
    return 5
  elif 5 <= temp < 10 or 32 < temp <= 35:
    return 0
  elif 0 <= temp < 5 or 35 < temp <= 38:
    return -5
  else:
    return -10


def wind_score(wind_speed):
  """Rate wind speed comfort on a scale of -10 to 0."""
  if wind_speed is None or not isinstance(wind_speed, (int, float)):
    return 0
  if wind_speed < 2:
    return 0
  elif 2 <= wind_speed < 4:
    return -2
  elif 4 <= wind_speed < 6:
    return -4
  elif 6 <= wind_speed < 10:
    return -6
  else:
    return -10


def cloud_score(cloud_coverage):
  """Rate cloud coverage for outdoor activities on a scale of -5 to 5."""
  if cloud_coverage is None or not isinstance(cloud_coverage, (int, float)):
    return 0
  if cloud_coverage < 20:
    return 5
  elif cloud_coverage < 40:
    return 3
  elif cloud_coverage < 60:
    return 1
  elif cloud_coverage < 80:
    return -2
  else:
    return -5


def precip_probability_score(probability):
  """Rate precipitation probability on a scale of -10 to 0."""
  if probability is None or not isinstance(probability, (int, float)):
    return 0
  if probability < 10:
    return 0
  elif probability < 30:
    return -2
  elif probability < 50:
    return -5
  elif probability < 70:
    return -7
  else:
    return -10

# calc_total_score was part of HourlyWeather and is now its _calculate_total_score method.
# No need for a separate one here if HourlyWeather handles its own total.
