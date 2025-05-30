from datetime import date, datetime, timedelta
import pytest
from typing import Optional, Union

from src.utils import (
    get_timezone,
    get_current_datetime,
    get_current_date,
    format_datetime,
    format_time,
    format_date,
    get_weather_desc,
    is_value_valid,
    get_value_or_default,
    safe_average,
    get_weather_description_from_counts,
    format_column,
    get_location_display_name,
    display_temperature,
    get_rating_info,
    colorize,
    get_weather_score,
    temp_score,
    wind_score,
    cloud_score,
    precip_probability_score,
    extract_base_symbol
)


def test_get_timezone():
    """Test timezone retrieval."""
    tz = get_timezone()
    assert tz is not None
    # Test that it's cached
    tz2 = get_timezone()
    assert tz is tz2


def test_format_datetime():
    """Test datetime formatting."""
    dt = datetime(2024, 3, 20, 14, 30)
    assert format_datetime(dt, "%Y-%m-%d") == "2024-03-20"
    assert format_datetime(dt, "%H:%M") == "14:30"


def test_format_time():
    """Test time formatting."""
    dt = datetime(2024, 3, 20, 14, 30)
    assert format_time(dt) == "14:30"


def test_format_date():
    """Test date formatting."""
    dt = datetime(2024, 3, 20, 14, 30)
    assert format_date(dt) == "Wed, 20 Mar"
    # Test with date object
    d = date(2024, 3, 20)
    assert format_date(d) == "Wed, 20 Mar"


def test_get_weather_desc():
    """Test weather description generation."""
    assert get_weather_desc("clearsky") == "Sunny"
    assert get_weather_desc("partlycloudy") == "Partly Cloudy"
    assert get_weather_desc("rain") == "Rain"
    assert get_weather_desc("") == "Unknown"
    assert get_weather_desc(None) == "Unknown"
    assert get_weather_desc("unknown_symbol") == "Unknown symbol"


def test_is_value_valid():
    """Test value validation."""
    assert is_value_valid(10) is True
    assert is_value_valid(10.5) is True
    assert is_value_valid(None) is False
    assert is_value_valid("10") is False


def test_get_value_or_default():
    """Test default value handling."""
    assert get_value_or_default(10, 0) == 10
    assert get_value_or_default(None, 0) == 0
    assert get_value_or_default("test", "default") == "test"
    assert get_value_or_default(None, "default") == "default"


def test_safe_average():
    """Test average calculation with invalid values."""
    assert safe_average([1, 2, 3]) == 2.0
    assert safe_average([1, None, 3]) == 2.0
    assert safe_average([]) is None
    assert safe_average([None, None]) is None


def test_get_weather_description_from_counts():
    """Test weather description generation from hour counts."""
    # Test rain condition
    assert get_weather_description_from_counts(2, 1, 1) == "Rain (1h)"

    # Test sunny condition
    assert get_weather_description_from_counts(3, 1, 0) == "Sunny"

    # Test partly cloudy condition
    assert get_weather_description_from_counts(1, 3, 0) == "Partly Cloudy"

    # Test mixed condition
    assert get_weather_description_from_counts(0, 0, 0) == "Mixed"

    # Test with precipitation warning
    assert get_weather_description_from_counts(3, 1, 0, 45.0) == "Sunny - 45% rain"


def test_format_column():
    """Test column formatting with ANSI colors."""
    # Test without colors
    assert format_column("test", 6) == "test  "

    # Test with colors (simplified)
    colored_text = "\033[32mtest\033[0m"
    formatted = format_column(colored_text, 6)
    assert len(formatted) > 6  # Should be longer due to color codes
    assert "test" in formatted


def test_get_location_display_name():
    """Test location name retrieval."""
    # This test depends on your LOCATIONS configuration
    # Add appropriate assertions based on your actual location data
    pass


def test_display_temperature():
    """Test temperature display formatting."""
    assert display_temperature(20.5) == "20.5°C"
    assert display_temperature(None) == "N/A"
    assert display_temperature(-5.0) == "-5.0°C"


def test_get_rating_info():
    """Test rating information generation."""
    # Test different score ranges
    rating, color = get_rating_info(20)
    assert rating == "Excellent"

    rating, color = get_rating_info(12)
    assert rating == "Very Good"

    rating, color = get_rating_info(8)
    assert rating == "Good"

    rating, color = get_rating_info(3)
    assert rating == "Fair"

    rating, color = get_rating_info(-5)
    assert rating == "Poor"

    rating, color = get_rating_info(None)
    assert rating == "N/A"


def test_colorize():
    """Test text coloring."""
    colored = colorize("test", "\033[32m")
    assert "\033[32m" in colored
    assert "test" in colored
    assert "\033[0m" in colored


def test_get_weather_score():
    """Test weather score calculation."""
    assert get_weather_score("clearsky") > get_weather_score("partlycloudy")
    assert get_weather_score("partlycloudy") > get_weather_score("rain")
    assert get_weather_score(None) == 0


def test_temp_score():
    """Test temperature score calculation."""
    # Test comfortable temperatures
    assert temp_score(20) > temp_score(30)  # 20°C should score better than 30°C
    assert temp_score(20) > temp_score(10)  # 20°C should score better than 10°C

    # Test edge cases
    assert temp_score(None) == 0
    assert temp_score(-10) < temp_score(20)  # Very cold should score worse
    assert temp_score(40) < temp_score(20)  # Very hot should score worse


def test_wind_score():
    """Test wind score calculation."""
    # Test optimal wind speeds
    assert wind_score(5) > wind_score(20)  # Light breeze should score better than strong wind
    assert wind_score(0) > wind_score(30)  # No wind should score better than very strong wind

    # Test edge cases
    assert wind_score(None) == 0
    assert wind_score(50) < wind_score(10)  # Very strong wind should score worse


def test_cloud_score():
    """Test cloud coverage score calculation."""
    # Test optimal cloud coverage
    assert cloud_score(0) > cloud_score(50)  # Clear sky should score better than partly cloudy
    assert cloud_score(50) > cloud_score(100)  # Partly cloudy should score better than overcast

    # Test edge cases
    assert cloud_score(None) == 0
    assert cloud_score(100) < cloud_score(0)  # Overcast should score worse than clear


def test_precip_probability_score():
    """Test precipitation probability score calculation."""
    # Test optimal probabilities
    assert precip_probability_score(0) > precip_probability_score(50)  # No rain should score better than likely rain
    assert precip_probability_score(20) > precip_probability_score(80)  # Low probability should score better than high

    # Test edge cases
    assert precip_probability_score(None) == 0
    assert precip_probability_score(100) < precip_probability_score(0)  # Certain rain should score worse


def test_extract_base_symbol():
    """Test weather symbol extraction."""
    assert extract_base_symbol("clearsky_day") == "clearsky"
    assert extract_base_symbol("partlycloudy_night") == "partlycloudy"
    assert extract_base_symbol("rain") == "rain"
    assert extract_base_symbol("") == "unknown"
    assert extract_base_symbol(None) == "unknown"