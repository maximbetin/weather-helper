"""
Defines the data models for HourlyWeather and DailyReport.
"""

from datetime import datetime
from typing import List, Optional

from src.core.hourly_weather import HourlyWeather
from src.core.locations import Location
from src.utils.misc import get_weather_description_from_counts, is_value_valid, safe_average


class DailyReport:
  """Represents a daily weather report with calculated statistics."""

  def __init__(self, date: datetime, daylight_hours: List[HourlyWeather], location_name: str):
    self.date = date
    self.daylight_hours = daylight_hours
    self.location_name = location_name
    self.day_name = date.strftime("%A")

    if not daylight_hours:
      self._initialize_empty_report()
      return

    # Calculate all stats in one pass through the data
    self._calculate_all_stats()

  def _initialize_empty_report(self) -> None:
    """Initialize default values for an empty report (no daylight hours)."""
    self.avg_score: float = -float('inf')
    self.sunny_hours: int = 0
    self.partly_cloudy_hours: int = 0
    self.rainy_hours: int = 0
    self.likely_rain_hours: int = 0
    self.avg_precip_prob: Optional[float] = None
    self.min_temp: Optional[float] = None
    self.max_temp: Optional[float] = None
    self.avg_temp: Optional[float] = None

  def _calculate_all_stats(self) -> None:
    """Calculate all statistics in a single pass through the data."""
    # Initialize counters and aggregators
    self.sunny_hours = 0
    self.partly_cloudy_hours = 0
    self.rainy_hours = 0
    self.likely_rain_hours = 0

    # For temperature stats
    valid_temps = []

    # For precipitation stats
    valid_precip_probs = []

    # For score calculation
    num_hours = len(self.daylight_hours)
    total_score = 0

    # Process each hour in a single loop
    for hour in self.daylight_hours:
      # Count condition hours
      if hour.symbol in ["clearsky", "fair"]:
        self.sunny_hours += 1
      elif hour.symbol == "partlycloudy":
        self.partly_cloudy_hours += 1
      elif "rain" in hour.symbol or "shower" in hour.symbol:
        self.rainy_hours += 1

      # Count likely rain hours
      if isinstance(hour.precipitation_probability, (int, float)) and hour.precipitation_probability > 30:
        self.likely_rain_hours += 1

      # Collect temperature data
      if is_value_valid(hour.temp):
        valid_temps.append(hour.temp)

      # Collect precipitation probability data
      if is_value_valid(hour.precipitation_probability):
        valid_precip_probs.append(hour.precipitation_probability)

      # Sum the total score directly
      total_score += hour.total_score

    # Calculate temperature stats
    self.min_temp = min(valid_temps) if valid_temps else None
    self.max_temp = max(valid_temps) if valid_temps else None
    self.avg_temp = safe_average(valid_temps)

    # Calculate precipitation stats
    self.avg_precip_prob = safe_average(valid_precip_probs)

    # Calculate average score
    self.avg_score = total_score / num_hours if num_hours > 0 else 0

  @property
  def weather_description(self) -> str:
    """Get weather description based on condition hours.

    Returns:
        str: Description of the overall weather
    """
    return get_weather_description_from_counts(
        self.sunny_hours,
        self.partly_cloudy_hours,
        self.rainy_hours,
        self.avg_precip_prob
    )
