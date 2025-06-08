"""
Defines the data models for HourlyWeather and DailyReport.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.core.types import NumericType


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
    return sum([self.weather_score, self.temp_score, self.wind_score, self.cloud_score, self.precip_prob_score])
