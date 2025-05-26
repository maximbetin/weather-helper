"""
Defines the data models for HourlyWeather and DailyReport.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Union, Any

from core_utils import safe_average, is_value_valid

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
    return sum(score for score in [
        self.weather_score,
        self.temp_score,
        self.wind_score,
        self.cloud_score,
        self.precip_prob_score
    ] if isinstance(score, (int, float)))


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

    self._calculate_condition_hours()
    self._calculate_precipitation_stats()
    self._calculate_temperature_stats()
    self._calculate_scores()

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

  def _calculate_condition_hours(self) -> None:
    """Calculate hours for different weather conditions."""
    self.sunny_hours = sum(1 for h in self.daylight_hours if h.symbol in ["clearsky", "fair"])
    self.partly_cloudy_hours = sum(1 for h in self.daylight_hours if h.symbol == "partlycloudy")
    self.rainy_hours = sum(1 for h in self.daylight_hours if "rain" in h.symbol or "shower" in h.symbol)
    self.likely_rain_hours = sum(1 for h in self.daylight_hours
                                 if isinstance(h.precipitation_probability, (int, float))
                                 and h.precipitation_probability > 30)

  def _calculate_precipitation_stats(self) -> None:
    """Calculate precipitation-related statistics."""
    precip_probs = [h.precipitation_probability for h in self.daylight_hours
                    if is_value_valid(h.precipitation_probability)]
    # Convert to list of valid values to fix type error
    valid_probs = [p for p in precip_probs if p is not None]
    self.avg_precip_prob = safe_average(valid_probs)

  def _calculate_temperature_stats(self) -> None:
    """Calculate temperature-related statistics."""
    # Filter out None values first
    valid_temps = [h.temp for h in self.daylight_hours if is_value_valid(h.temp) and h.temp is not None]
    self.min_temp = min(valid_temps) if valid_temps else None
    self.max_temp = max(valid_temps) if valid_temps else None
    self.avg_temp = safe_average(valid_temps)

  def _calculate_scores(self) -> None:
    """Calculate overall scores for the day."""
    num_hours = len(self.daylight_hours)
    score_types = ["weather_score", "temp_score", "wind_score", "cloud_score", "precip_prob_score"]

    # Count how many score types are available (always at least 3: weather, temp, wind)
    available_score_types = []
    for score_type in score_types:
      if any(is_value_valid(getattr(h, score_type, None)) for h in self.daylight_hours):
        available_score_types.append(score_type)

    # Calculate total score
    self.total_score_sum = sum(
        getattr(h, score_type)
        for h in self.daylight_hours
        for score_type in available_score_types
        if is_value_valid(getattr(h, score_type, None))
    )

    # Calculate average score
    self.avg_score = self.total_score_sum / (num_hours * len(available_score_types)) if num_hours > 0 and available_score_types else 0
