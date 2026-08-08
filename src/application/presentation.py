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

RATING_COLOR_KEYS = {
    "Excellent": "excellent",
    "Very Good": "very_good",
    "Good": "good",
    "Fair": "fair",
    "Poor": "poor",
}

RATING_COLORS = {
    rating: BASE_COLORS[key] for rating, key in RATING_COLOR_KEYS.items()
}

RATING_BACKGROUNDS = {
    "Excellent": "#f0fdf4",
    "Very Good": "#f7fee7",
    "Good": "#fefce8",
    "Fair": "#fff7ed",
    "Poor": "#fef2f2",
}

# Dark-mode equivalents. Rating hues stay recognisable but are lightened so
# they keep their contrast against a dark surface.
DARK_COLORS = {
    "primary": "#93b4ff",
    "background": "#0f172a",
    "surface": "#1e293b",
    "border": "#334155",
    "text": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "excellent": "#4ade80",
    "very_good": "#a3e635",
    "good": "#facc15",
    "fair": "#fb923c",
    "poor": "#f87171",
}

DARK_RATING_BACKGROUNDS = {
    "Excellent": "#16321f",
    "Very Good": "#26310f",
    "Good": "#332b0b",
    "Fair": "#3a2410",
    "Poor": "#3b1616",
}

RATING_ORDER = ("Excellent", "Very Good", "Good", "Fair", "Poor")


def get_palette(dark: bool = False) -> dict:
    """Return the colour palette for the requested brightness."""
    return DARK_COLORS if dark else BASE_COLORS


def get_rating_color(rating: str, dark: bool = False) -> str:
    """Return the shared foreground color for a descriptive rating."""
    palette = get_palette(dark)
    key = RATING_COLOR_KEYS.get(rating)
    if key is None:
        return palette["text"]
    return palette[key]


def get_rating_background(rating: str, dark: bool = False) -> str:
    """Return the subtle background color for a descriptive rating."""
    backgrounds = DARK_RATING_BACKGROUNDS if dark else RATING_BACKGROUNDS
    return backgrounds.get(rating, get_palette(dark)["surface"])


MISSING_VALUE = "—"


def format_optional(value: Optional[NumericType], formatter) -> str:
    """Format a value, or return the shared missing-data marker.

    Missing readings are shown as a dash rather than a plausible-looking
    number, so a gap in the source data can never be mistaken for weather.
    """
    return MISSING_VALUE if value is None else formatter(value)


def format_relative_date(value: date, today: date) -> str:
    """Label a date relative to today when that is what a person would say."""
    delta = (value - today).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    return value.strftime("%a, %d %b")


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
    """Format precipitation without presenting missing data as dry weather."""
    return "N/A" if value is None else f"{value:.1f}{unit}"


def format_wind_speed(
    value: Optional[NumericType], unit: str = " m/s"
) -> str:
    """Format wind speed with one decimal place and a fallback."""
    return "N/A" if value is None else f"{value:.1f}{unit}"
