"""
Data models for weather information.
Defines HourlyWeather and DailyReport classes used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.core.config import NumericType, safe_average


@dataclass
class HourlyWeather:
    """Represents hourly weather data with calculated scores."""
    time: datetime
    temp: Optional[NumericType] = None
    wind: Optional[NumericType] = None
    cloud_coverage: Optional[NumericType] = None
    precipitation_amount: Optional[NumericType] = None
    relative_humidity: Optional[NumericType] = None
    temp_score: NumericType = 0
    wind_score: NumericType = 0
    cloud_score: NumericType = 0
    precip_amount_score: NumericType = 0
    humidity_score: NumericType = 0
    total_score: NumericType = field(init=False)
    hour: int = field(init=False)

    def __post_init__(self) -> None:
        """Calculate derived fields after initialization."""
        self.hour = self.time.hour
        self.total_score = self._calculate_total_score()

    def _calculate_total_score(self) -> NumericType:
        """Calculate the total score from individual component scores."""
        return self.temp_score + self.wind_score + self.cloud_score + self.precip_amount_score + self.humidity_score


class DailyReport:
    """Represents a daily weather report with calculated statistics."""

    def __init__(self, date: datetime, daylight_hours: list[HourlyWeather], location_name: str):
        self.date = date
        self.daylight_hours = daylight_hours
        self.location_name = location_name

        if not daylight_hours:
            self._initialize_empty_report()
            return

        # Calculate all stats in one pass through the data
        self._calculate_all_stats()

    def _get_weather_description(self) -> str:
        """Determine overall weather description based on temperature and precipitation."""
        # Check if there's significant precipitation
        if self.likely_rain_hours > 0:
            return f"Rain ({self.likely_rain_hours}h)"

        # Base description on temperature
        if self.avg_temp is not None:
            if self.avg_temp >= 22:
                return "Warm"
            elif self.avg_temp >= 18:
                return "Pleasant"
            elif self.avg_temp >= 10:
                return "Cool"
            else:
                return "Cold"

        return "Mixed"

    def _initialize_empty_report(self) -> None:
        """Initialize default values for an empty report (no daylight hours)."""
        self.avg_score: NumericType = -float('inf')
        self.likely_rain_hours: int = 0
        self.min_temp: Optional[NumericType] = None
        self.max_temp: Optional[NumericType] = None
        self.avg_temp: Optional[NumericType] = None

    def _calculate_all_stats(self) -> None:
        """Calculate all statistics in a single pass through the data."""
        self.likely_rain_hours = sum(1 for hour in self.daylight_hours if isinstance(
            hour.precipitation_amount, (int, float)) and hour.precipitation_amount > 0.5)

        valid_temps = [hour.temp for hour in self.daylight_hours if hour.temp is not None]

        total_score = sum(hour.total_score for hour in self.daylight_hours)

        self.min_temp = min(valid_temps) if valid_temps else None
        self.max_temp = max(valid_temps) if valid_temps else None
        self.avg_temp = safe_average(valid_temps)

        num_hours = len(self.daylight_hours)
        self.avg_score = total_score / num_hours if num_hours > 0 else 0

    @property
    def weather_description(self) -> str:
        """Get weather description based on condition hours.

        Returns:
            str: Description of the overall weather
        """
        return self._get_weather_description()
