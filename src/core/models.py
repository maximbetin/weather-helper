"""
Data models for weather information.
Defines HourlyWeather and DailyReport classes used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from src.core.config import NumericType, safe_average

SIGNIFICANT_RAIN_MM = 0.5
WARM_TEMP_C = 22
PLEASANT_TEMP_C = 18
COOL_TEMP_C = 10


@dataclass
class HourlyWeather:
    """Represents hourly weather data with calculated scores."""

    time: datetime
    temp: Optional[NumericType] = None
    wind: Optional[NumericType] = None
    cloud_coverage: Optional[NumericType] = None
    precipitation_amount: Optional[NumericType] = None
    precipitation_probability: Optional[NumericType] = None
    symbol_code: Optional[str] = None
    relative_humidity: Optional[NumericType] = None
    water_temp: Optional[NumericType] = None
    wave_height: Optional[NumericType] = None
    coverage_hours: int = 1
    temp_score: NumericType = 0
    wind_score: NumericType = 0
    cloud_score: NumericType = 0
    precip_amount_score: NumericType = 0
    humidity_score: NumericType = 0
    water_temp_score: NumericType = 0
    wave_height_score: NumericType = 0
    total_score: NumericType = field(init=False)
    hour: int = field(init=False)

    def __post_init__(self) -> None:
        """Calculate derived fields after initialization."""
        self.hour = self.time.hour
        self.total_score = self._calculate_total_score()

    @property
    def end_time(self) -> datetime:
        """Return the first instant no longer described by this entry."""
        return self.time + timedelta(hours=self.coverage_hours)

    @property
    def is_hourly(self) -> bool:
        """Return True when this entry describes a single hour."""
        return self.coverage_hours == 1

    @property
    def has_core_readings(self) -> bool:
        """Return True when the readings a recommendation depends on are present.

        A missing reading scores as zero, which is indistinguishable from a
        mediocre real one. Rather than let a gap in the data masquerade as
        weather, entries missing a core reading are shown but never form the
        basis of a recommendation.
        """
        return all(
            value is not None
            for value in (self.temp, self.wind, self.precipitation_amount)
        )

    @property
    def precipitation_rate(self) -> Optional[NumericType]:
        """Return precipitation in mm per hour.

        Beyond roughly two days the forecast only reports six-hour totals.
        Scoring those totals as if they fell in one hour would exaggerate rain
        on later days, so scores are always based on the hourly rate.
        """
        if self.precipitation_amount is None:
            return None
        return self.precipitation_amount / self.coverage_hours

    def _calculate_total_score(self) -> NumericType:
        """Calculate the total score from individual component scores."""
        return (
            self.temp_score
            + self.wind_score
            + self.cloud_score
            + self.precip_amount_score
            + self.humidity_score
            + self.water_temp_score
            + self.wave_height_score
        )


class DailyReport:
    """Represents a daily weather report with calculated statistics."""

    def __init__(
        self, date: datetime, daylight_hours: list[HourlyWeather], location_name: str
    ):
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
        if self.likely_rain_hours > 0:
            return f"Rain ({self.likely_rain_hours}h)"

        return _describe_temperature(self.avg_temp)

    def _initialize_empty_report(self) -> None:
        """Initialize default values for an empty report (no daylight hours)."""
        self.avg_score: NumericType = -float("inf")
        self.likely_rain_hours: int = 0
        self.min_temp: Optional[NumericType] = None
        self.max_temp: Optional[NumericType] = None
        self.avg_temp: Optional[NumericType] = None

    def _calculate_all_stats(self) -> None:
        """Calculate all statistics in a single pass through the data."""
        temperatures = _valid_temperatures(self.daylight_hours)
        total_score = sum(hour.total_score for hour in self.daylight_hours)
        self.likely_rain_hours = _count_likely_rain_hours(self.daylight_hours)
        self._set_temperature_stats(temperatures)
        self.avg_score = total_score / len(self.daylight_hours)

    def _set_temperature_stats(self, temperatures: list[NumericType]) -> None:
        """Set min, max, and average temperature fields."""
        self.min_temp = min(temperatures) if temperatures else None
        self.max_temp = max(temperatures) if temperatures else None
        self.avg_temp = safe_average(temperatures)

    @property
    def weather_description(self) -> str:
        """Get weather description based on condition hours.

        Returns:
            str: Description of the overall weather
        """
        return self._get_weather_description()


def _valid_temperatures(hours: list[HourlyWeather]) -> list[NumericType]:
    """Return non-empty temperature readings from hourly weather."""
    return [hour.temp for hour in hours if hour.temp is not None]


def _count_likely_rain_hours(hours: list[HourlyWeather]) -> int:
    """Count the hours covered by entries above the rain threshold."""
    return sum(hour.coverage_hours for hour in hours if _has_significant_rain(hour))


def _has_significant_rain(hour: HourlyWeather) -> bool:
    """Return True when an hour is likely rainy."""
    rate = hour.precipitation_rate
    return isinstance(rate, (int, float)) and rate > SIGNIFICANT_RAIN_MM


def _describe_temperature(avg_temp: Optional[NumericType]) -> str:
    """Return a coarse description for an average temperature."""
    if avg_temp is None:
        return "Mixed"
    if avg_temp >= WARM_TEMP_C:
        return "Warm"
    if avg_temp >= PLEASANT_TEMP_C:
        return "Pleasant"
    if avg_temp >= COOL_TEMP_C:
        return "Cool"
    return "Cold"
