"""
Defines the data models for HourlyWeather and DailyReport.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

from core_utils import get_weather_description_from_counts, is_value_valid, safe_average

NumericType = Union[int, float]


@dataclass
class HourlyWeather:
  """Represents hourly weather data with calculated scores."""
  time: datetime
  temp: Optional[NumericType] = None
  wind: Optional[NumericType] = None
  humidity: Optional[NumericType] = None
  cloud_coverage: Optional[NumericType] = None
  fog: Optional[NumericType] = None
  wind_direction: Optional[NumericType] = None
  wind_gust: Optional[NumericType] = None
  precipitation_amount: Optional[NumericType] = None
  precipitation_probability: Optional[NumericType] = None
  symbol: str = ""
  weather_score: NumericType = 0
  temp_score: NumericType = 0
  wind_score: NumericType = 0
  cloud_score: NumericType = 0
  precip_prob_score: NumericType = 0
  total_score: NumericType = field(init=False)
  hour: int = field(init=False)

  def __post_init__(self) -> None:
    """Calculate derived fields after initialization."""
    self.hour = self.time.hour
    self.total_score = self._calculate_total_score()

  def _calculate_total_score(self) -> NumericType:
    """Calculate the total score from individual component scores."""
    # Define the score components to include
    score_components = [
        self.weather_score,
        self.temp_score,
        self.wind_score,
        self.cloud_score,
        self.precip_prob_score
    ]
    # Filter valid numeric values and sum them
    return sum(score for score in score_components if isinstance(score, (int, float)))


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
    self.total_score_sum: float = 0
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
    self.total_score_sum = 0
    score_types = ["weather_score", "temp_score", "wind_score", "cloud_score", "precip_prob_score"]
    available_score_types = []

    # Check which score types are available
    for score_type in score_types:
      if any(is_value_valid(getattr(h, score_type, None)) for h in self.daylight_hours):
        available_score_types.append(score_type)

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

      # Sum scores
      for score_type in available_score_types:
        score_value = getattr(hour, score_type, 0)
        if is_value_valid(score_value):
          self.total_score_sum += score_value

    # Calculate temperature stats
    self.min_temp = min(valid_temps) if valid_temps else None
    self.max_temp = max(valid_temps) if valid_temps else None
    self.avg_temp = safe_average(valid_temps)

    # Calculate precipitation stats
    self.avg_precip_prob = safe_average(valid_precip_probs)

    # Calculate average score
    self.avg_score = self.total_score_sum / (num_hours * len(available_score_types)) if num_hours > 0 and available_score_types else 0

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
