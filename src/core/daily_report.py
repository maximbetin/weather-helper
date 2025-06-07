"""
Defines the data models for HourlyWeather and DailyReport.
"""

from datetime import datetime
from typing import List, Optional

from src.core.hourly_weather import HourlyWeather
from src.utils.misc import safe_average


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

  def _get_weather_description(self) -> str:
    """Determine overall weather description based on hour counts."""
    # First check if there's significant rain
    if self.rainy_hours > 0:
      return f"Rain ({self.rainy_hours}h)"

    # Determine the dominant condition
    max_hours = max(self.sunny_hours, self.partly_cloudy_hours, 0)  # Ensure non-negative

    # Format precipitation warning if needed
    precip_warning = ""
    if self.avg_precip_prob is not None and self.avg_precip_prob > 40:
      precip_warning = f" - {self.avg_precip_prob:.0f}% rain"

    if max_hours == 0:
      return "Mixed" + precip_warning
    elif self.sunny_hours == max_hours:
      return "Sunny" + precip_warning
    else:
      return "Partly Cloudy" + precip_warning

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
    self.sunny_hours = sum(1 for hour in self.daylight_hours if hour.symbol in ["clearsky", "fair"])
    self.partly_cloudy_hours = sum(1 for hour in self.daylight_hours if hour.symbol == "partlycloudy")
    self.rainy_hours = sum(1 for hour in self.daylight_hours if "rain" in hour.symbol or "shower" in hour.symbol)
    self.likely_rain_hours = sum(1 for hour in self.daylight_hours if isinstance(
      hour.precipitation_probability, (int, float)) and hour.precipitation_probability > 30)

    valid_temps = [hour.temp for hour in self.daylight_hours if hour.temp is not None]
    valid_precip_probs = [hour.precipitation_probability for hour in self.daylight_hours if hour.precipitation_probability is not None]

    total_score = sum(hour.total_score for hour in self.daylight_hours)

    self.min_temp = min(valid_temps) if valid_temps else None
    self.max_temp = max(valid_temps) if valid_temps else None
    self.avg_temp = safe_average(valid_temps)

    self.avg_precip_prob = safe_average(valid_precip_probs)

    num_hours = len(self.daylight_hours)
    self.avg_score = total_score / num_hours if num_hours > 0 else 0

  @property
  def weather_description(self) -> str:
    """Get weather description based on condition hours.

    Returns:
        str: Description of the overall weather
    """
    return self._get_weather_description()
