"""UI-independent display formatting and the shared application palette."""

from datetime import date, datetime
from typing import Optional, Union

from src.core.config import NumericType

BASE_COLORS = {
    "primary": "#1e3a8a",
    "background": "#f8fafc",
    "surface": "#ffffff",
    "border": "#e2e8f0",
    "text": "#1e293b",
    "text_secondary": "#64748b",
    "excellent": "#15803d",
    "very_good": "#65a30d",
    "good": "#ca8a04",
    "fair": "#ea580c",
    "poor": "#b91c1c",
}

RATING_COLORS = {
    "Excellent": BASE_COLORS["excellent"],
    "Very Good": BASE_COLORS["very_good"],
    "Good": BASE_COLORS["good"],
    "Fair": BASE_COLORS["fair"],
    "Poor": BASE_COLORS["poor"],
}

RATING_BACKGROUNDS = {
    "Excellent": "#f0fdf4",
    "Very Good": "#f7fee7",
    "Good": "#fefce8",
    "Fair": "#fff7ed",
    "Poor": "#fef2f2",
}


def get_rating_color(rating: str) -> str:
    """Return the shared foreground color for a descriptive rating."""
    return RATING_COLORS.get(rating, BASE_COLORS["text"])


def get_rating_background(rating: str) -> str:
    """Return the subtle background color for a descriptive rating."""
    return RATING_BACKGROUNDS.get(rating, BASE_COLORS["surface"])


def format_time(value: datetime) -> str:
    """Format a forecast timestamp as a 24-hour time."""
    return value.strftime("%H:%M")


def format_date(value: Union[date, datetime]) -> str:
    """Format a date for compact selectors."""
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%a, %d %b")


def format_duration(hours: int) -> str:
    """Format an hour count with correct singular/plural wording."""
    return "1 hour" if hours == 1 else f"{hours} hours"


def format_temperature(
    value: Optional[NumericType], unit: str = "°C"
) -> str:
    """Format a temperature with one decimal place and a fallback."""
    return "N/A" if value is None else f"{value:.1f}{unit}"


def format_percentage(
    value: Optional[NumericType], suffix: str = "%"
) -> str:
    """Format a percentage with no decimal places and a fallback."""
    return "N/A" if value is None else f"{value:.0f}{suffix}"


def format_precipitation(
    value: Optional[NumericType], unit: str = " mm"
) -> str:
    """Format precipitation using zero as the dry-hour fallback."""
    amount = 0 if value is None else value
    return f"{amount:.1f}{unit}"


def format_wind_speed(
    value: Optional[NumericType], unit: str = " m/s"
) -> str:
    """Format wind speed with one decimal place and a fallback."""
    return "N/A" if value is None else f"{value:.1f}{unit}"
