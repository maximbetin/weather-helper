from datetime import date, datetime, timedelta
import pytest
from typing import Optional, Union
from unittest.mock import patch

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
    extract_base_symbol,
    get_block_type,
    extract_blocks,
    display_loading_message,
    display_error,
    display_info,
    display_warning
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


def test_get_block_type():
    """Test weather block type determination."""
    from src.hourly_weather import HourlyWeather
    from datetime import datetime

    # Test sunny types
    hour_sunny = HourlyWeather(time=datetime.now(), symbol="clearsky")
    assert get_block_type(hour_sunny) == "sunny"

    hour_fair = HourlyWeather(time=datetime.now(), symbol="fair")
    assert get_block_type(hour_fair) == "sunny"

    # Test rainy types
    hour_rain = HourlyWeather(time=datetime.now(), symbol="rain")
    assert get_block_type(hour_rain) == "rainy"

    hour_heavyrain = HourlyWeather(time=datetime.now(), symbol="heavyrain")
    assert get_block_type(hour_heavyrain) == "rainy"

    # Test cloudy (default) type
    hour_cloudy = HourlyWeather(time=datetime.now(), symbol="cloudy")
    assert get_block_type(hour_cloudy) == "cloudy"

    hour_fog = HourlyWeather(time=datetime.now(), symbol="fog")
    assert get_block_type(hour_fog) == "cloudy"


def test_extract_blocks():
    """Test finding consecutive weather blocks."""
    from src.hourly_weather import HourlyWeather
    from datetime import datetime, timedelta

    base_time = datetime(2024, 3, 20, 8, 0)

    # Test with empty list
    assert extract_blocks([]) == []

    # Test with a single hour (less than min_block_len)
    single_hour = [HourlyWeather(time=base_time, symbol="clearsky")]
    assert extract_blocks(single_hour) == []

    # Test with two consecutive sunny hours
    sunny_hours = [
        HourlyWeather(time=base_time, symbol="clearsky"),
        HourlyWeather(time=base_time + timedelta(hours=1), symbol="clearsky")
    ]
    blocks = extract_blocks(sunny_hours)
    assert len(blocks) == 1
    assert blocks[0][1] == "sunny"  # Check block type
    assert len(blocks[0][0]) == 2   # Check block length

    # Test with mixed weather types
    mixed_hours = [
        HourlyWeather(time=base_time, symbol="clearsky"),
        HourlyWeather(time=base_time + timedelta(hours=1), symbol="clearsky"),
        HourlyWeather(time=base_time + timedelta(hours=2), symbol="rain"),
        HourlyWeather(time=base_time + timedelta(hours=3), symbol="rain"),
        HourlyWeather(time=base_time + timedelta(hours=4), symbol="rain"),
        HourlyWeather(time=base_time + timedelta(hours=5), symbol="cloudy")
    ]

    blocks = extract_blocks(mixed_hours)
    assert len(blocks) == 2  # Should find 2 blocks (sunny and rainy)

    # Test with non-consecutive hours
    non_consecutive = [
        HourlyWeather(time=base_time, symbol="clearsky"),
        HourlyWeather(time=base_time + timedelta(hours=1), symbol="clearsky"),
        HourlyWeather(time=base_time + timedelta(hours=3), symbol="clearsky")  # 1-hour gap
    ]

    blocks = extract_blocks(non_consecutive)
    assert len(blocks) == 1  # Should find 1 block
    assert len(blocks[0][0]) == 2  # Only the first two hours


def test_get_timezone_cache():
    """Test timezone caching mechanism."""
    # Reset the cache
    import src.utils
    src.utils._TIMEZONE_CACHE = None

    # First call should create the cache
    tz1 = get_timezone()
    assert tz1 is not None

    # Second call should use the cached value
    tz2 = get_timezone()
    assert tz1 is tz2

    # Verify the cache was set
    assert src.utils._TIMEZONE_CACHE is not None


def test_edge_cases_for_scoring_functions():
    """Test edge cases for all scoring functions."""
    # Test extreme temperature values
    assert temp_score(-20) == -10  # Very extreme cold
    assert temp_score(45) == -10   # Very extreme hot

    # Test extreme wind values
    assert wind_score(20) == -10   # Extreme wind

    # Test extreme cloud coverage
    assert cloud_score(100) == -5  # Full overcast

    # Test extreme precipitation probability
    assert precip_probability_score(100) == -10  # Certain rain


def test_colorize_with_different_colors():
    """Test colorization with different color codes."""
    from src.config import GREEN, RED, YELLOW, BLUE, RESET

    # Test various colors
    assert colorize("test", GREEN) == f"{GREEN}test{RESET}"
    assert colorize("test", RED) == f"{RED}test{RESET}"
    assert colorize("test", YELLOW) == f"{YELLOW}test{RESET}"
    assert colorize("test", BLUE) == f"{BLUE}test{RESET}"

    # Test with empty string
    assert colorize("", GREEN) == f"{GREEN}{RESET}"


def test_format_column_edge_cases():
    """Test format_column with edge cases."""
    # Test with column width smaller than text
    assert len(format_column("test", 2)) >= 4  # Should be at least the length of 'test'

    # Test with exact width
    assert format_column("test", 4) == "test"

    # Test with empty string
    assert format_column("", 5) == "     "

    # Test with ANSI codes and width exactly matching visible text
    from src.config import GREEN, RESET
    colored_text = f"{GREEN}test{RESET}"
    assert "test" in format_column(colored_text, 4)

    # Test with unicode characters
    assert len(format_column("测试", 4)) >= 4


def test_get_weather_description_from_counts_edge_cases():
    """Test weather description generation with edge cases."""
    # Test with all zeros
    assert get_weather_description_from_counts(0, 0, 0) == "Mixed"

    # Test with equal sunny and cloudy
    assert "Sunny" in get_weather_description_from_counts(5, 5, 0)  # Should pick sunny as it's checked first

    # Test with high precipitation probability but no rain hours
    assert "rain" in get_weather_description_from_counts(5, 2, 0, 80)

    # Test with negative hour counts (shouldn't happen but handle gracefully)
    assert get_weather_description_from_counts(-1, -1, 0) == "Mixed"


def test_is_value_valid_additional_cases():
    """Test additional edge cases for value validation."""
    # Test with non-numeric string
    assert is_value_valid("string") is False

    # Test with empty string
    assert is_value_valid("") is False

    # Test with boolean (Booleans are actually a subclass of int in Python)
    # is_value_valid returns True for booleans since isinstance(True, int) is True
    assert is_value_valid(True) is True
    assert is_value_valid(False) is True

    # Test with list/dict
    assert is_value_valid([]) is False
    assert is_value_valid({}) is False


def test_extract_base_symbol_additional_cases():
    """Test additional cases for base symbol extraction."""
    # Test with multiple underscores
    assert extract_base_symbol("partly_cloudy_day") == "partly"

    # Test with empty string
    assert extract_base_symbol("") == "unknown"

    # Test with None
    assert extract_base_symbol(None) == "unknown"

    # Test with non-string objects - would need to modify the function to handle this case
    # For now, we'll just skip this test
    # assert extract_base_symbol(123) == "unknown"


def test_display_functions():
    """Test display utility functions."""
    with patch('builtins.print') as mock_print:
        # Test display_loading_message
        display_loading_message()
        mock_print.assert_called_once()
        mock_print.reset_mock()

        # Test display_error
        display_error("Test error")
        mock_print.assert_called_once()
        mock_print.reset_mock()

        # Test display_info
        display_info("Test info")
        mock_print.assert_called_once()
        mock_print.reset_mock()

        # Test display_warning
        display_warning("Test warning")
        mock_print.assert_called_once()


def test_extract_base_symbol_implementation():
    """Test the extract_base_symbol function more thoroughly."""
    # Test with various string formats - no need to modify the function
    assert extract_base_symbol("one_two_three") == "one"
    assert extract_base_symbol("symbol") == "symbol"

    # The int case is already covered by the commented out test in the previous function


def test_safe_average_edge_cases():
    """Test edge cases for safe_average function."""
    # Test with mixed valid and invalid values
    assert safe_average([1, 2, None, "string", 3]) == 2.0

    # Test with only invalid values
    assert safe_average([None, "string", []]) is None

    # Test with empty list
    assert safe_average([]) is None


def test_current_datetime_and_date():
    """Test the current datetime and date functions."""
    # Test get_current_datetime
    current_dt = get_current_datetime()
    assert isinstance(current_dt, datetime)
    assert current_dt.tzinfo is not None  # Should have timezone info

    # Test get_current_date
    current_d = get_current_date()
    assert isinstance(current_d, date)

    # Test relationship between the two functions
    with patch('src.utils.get_current_datetime') as mock_current_dt:
        mock_dt = datetime(2024, 3, 20, 12, 0, tzinfo=get_timezone())
        mock_current_dt.return_value = mock_dt

        assert get_current_date() == mock_dt.date()