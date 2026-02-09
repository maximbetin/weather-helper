"""
Tests for core functionality including evaluation, processing, and configuration utilities.
Consolidates tests for the core business logic of the weather helper.
"""

from datetime import date, datetime

from src.core.config import (
    get_current_date,
    get_current_datetime,
    get_timezone,
    safe_average,
)
from src.core.evaluation import (
    _calculate_weather_averages,
    find_optimal_weather_block,
    get_available_dates,
    get_time_blocks_for_date,
    get_top_locations_for_date,
    process_forecast,
)
from src.core.scoring import _get_value_from_ranges, normalize_score
from src.core.models import HourlyWeather


# Tests for basic evaluation functions
def test_find_optimal_weather_block_empty():
    assert find_optimal_weather_block([]) is None


def test_process_forecast_empty():
    assert process_forecast({}, "Test Location") is None
    assert process_forecast({"properties": {}}, "Test Location") is None

    # Empty timeseries returns empty structure but not None
    result = process_forecast({"properties": {"timeseries": []}}, "Test Location")
    assert result is not None
    assert result["daily_forecasts"] == {}
    assert result["day_scores"] == {}


def test_process_forecast_with_fixture(sample_forecast_data):
    """Test process_forecast using shared fixture."""
    result = process_forecast(sample_forecast_data, "Test Location")
    assert result is not None
    assert "daily_forecasts" in result
    assert "day_scores" in result


# Tests for configuration utilities


def test_get_timezone():
    tz = get_timezone()
    assert tz is not None
    assert str(tz) == "Europe/Madrid"


def test_get_current_datetime():
    dt = get_current_datetime()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None


def test_get_current_date():
    d = get_current_date()
    assert isinstance(d, date)


def test_safe_average():
    assert safe_average([]) is None
    assert safe_average([1, 2, 3]) == 2.0
    assert safe_average([5]) == 5.0
    expected = 2.333333333333333
    result = safe_average([1.5, 2.5, 3.0])
    assert result is not None and abs(result - expected) < 0.000001


# Tests for _get_value_from_ranges function


def test_get_value_from_ranges():
    ranges = [
        ((0, 10), "low"),
        ((10, 20), "medium"),
        ((20, 30), "high"),
        (None, "default"),
    ]

    # Test normal range matching
    assert _get_value_from_ranges(5, ranges) == "low"
    assert _get_value_from_ranges(15, ranges) == "medium"
    assert _get_value_from_ranges(25, ranges) == "high"

    # Test boundary values (exclusive by default)
    assert _get_value_from_ranges(10, ranges) == "medium"
    assert _get_value_from_ranges(20, ranges) == "high"

    # Test inclusive mode
    assert _get_value_from_ranges(10, ranges, inclusive=True) == "low"
    assert _get_value_from_ranges(20, ranges, inclusive=True) == "medium"

    # Test default case
    assert _get_value_from_ranges(35, ranges) == "default"

    # Test None value
    assert _get_value_from_ranges(None, ranges) is None

    # Test string value (invalid) - need to use type ignore since we're testing error handling
    assert _get_value_from_ranges("invalid", ranges) is None  # type: ignore


# Tests for other missing functions


def test_get_available_dates():
    # Test with empty/invalid data
    assert get_available_dates({}) == []
    assert get_available_dates({"other_key": {}}) == []

    # Test with valid data
    test_data = {
        "daily_forecasts": {
            date(2024, 3, 15): [],
            date(2024, 3, 16): [],
            date(2024, 3, 14): [],
        }
    }
    dates = get_available_dates(test_data)
    assert len(dates) == 3
    assert dates == [
        date(2024, 3, 14),
        date(2024, 3, 15),
        date(2024, 3, 16),
    ]  # Should be sorted


def test_get_time_blocks_for_date():
    # Test with empty/invalid data
    assert get_time_blocks_for_date({}, date(2024, 3, 15)) == []
    assert get_time_blocks_for_date({"other_key": {}}, date(2024, 3, 15)) == []

    # Test with valid data
    test_date = date(2024, 3, 15)
    hour1 = HourlyWeather(
        time=datetime(2024, 3, 15, 10),
        temp_score=1,
        wind_score=1,
        cloud_score=1,
        precip_amount_score=1,
    )
    hour2 = HourlyWeather(
        time=datetime(2024, 3, 15, 8),
        temp_score=2,
        wind_score=2,
        cloud_score=2,
        precip_amount_score=2,
    )

    test_data = {"daily_forecasts": {test_date: [hour1, hour2]}}

    blocks = get_time_blocks_for_date(test_data, test_date)
    assert len(blocks) == 2
    assert blocks[0].hour == 8  # Should be sorted by hour
    assert blocks[1].hour == 10


def test_calculate_weather_averages(sample_hourly_weather):
    # Test with empty list
    avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages([])
    assert avg_temp is None
    assert avg_wind is None
    assert avg_humidity is None
    assert avg_precip is None

    # Test with hours that have None values
    hour1 = HourlyWeather(
        time=datetime(2024, 3, 15, 10), temp=None, wind=None, relative_humidity=None, precipitation_amount=None
    )
    avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages([hour1])
    assert avg_temp is None
    assert avg_wind is None
    assert avg_humidity is None
    assert avg_precip is None

    # Test with fixture
    avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages([sample_hourly_weather])
    assert avg_temp == 20.0
    assert avg_wind == 5.0
    assert avg_humidity == 60.0
    assert avg_precip == 0.0

    # Test with mixed valid and None data
    hour2 = HourlyWeather(
        time=datetime(2024, 3, 15, 11), temp=22, wind=3, relative_humidity=55, precipitation_amount=0.2
    )
    hour3 = HourlyWeather(
        time=datetime(2024, 3, 15, 12), temp=None, wind=7, relative_humidity=65, precipitation_amount=None
    )  # Mixed None values

    avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages(
        [sample_hourly_weather, hour2, hour3]
    )
    # (20 + 22) / 2 = 21.0
    assert avg_temp == 21.0
    # (5 + 3 + 7) / 3 = 5.0
    assert avg_wind == 5.0
    # (60 + 55 + 65) / 3 = 60.0
    assert avg_humidity == 60.0
    # (0.0 + 0.2) / 2 = 0.1
    assert avg_precip == 0.1


# Tests for the process_forecast function with more edge cases


def test_process_forecast_complex():
    # Create mock forecast data
    mock_timeseries = [
        {
            "time": "2024-03-15T10:00:00Z",
            "data": {
                "instant": {
                    "details": {
                        "air_temperature": 20,
                        "wind_speed": 5,
                        "cloud_area_fraction": 30,
                        "relative_humidity": 65,
                    }
                },
                "next_1_hours": {"details": {"precipitation_amount": 0.1}},
            },
        },
        {
            "time": "2024-03-15T11:00:00Z",
            "data": {
                "instant": {
                    "details": {
                        "air_temperature": 22,
                        "wind_speed": 3,
                        "cloud_area_fraction": 20,
                        "relative_humidity": 55,
                    }
                },
                "next_1_hours": {"details": {"precipitation_amount": 0.0}},
            },
        },
    ]

    forecast_data = {"properties": {"timeseries": mock_timeseries}}

    result = process_forecast(forecast_data, "Test Location")
    assert result is not None
    assert "daily_forecasts" in result
    assert "day_scores" in result


def test_get_top_locations_for_date():
    # Test with empty data
    assert get_top_locations_for_date({}, date(2024, 3, 15)) == []

    # Test with no matching date
    test_data = {
        "location1": {
            "day_scores": {date(2024, 3, 14): None},
            "daily_forecasts": {date(2024, 3, 14): []},
        }
    }
    assert get_top_locations_for_date(test_data, date(2024, 3, 15)) == []


def test_get_top_locations_for_date_no_data():
    result = get_top_locations_for_date({}, date(2024, 3, 15))
    assert result == []


def test_get_top_locations_for_date_less_than_n():
    # Test with empty data and custom top_n parameter
    result = get_top_locations_for_date({}, date(2024, 3, 15), top_n=3)
    assert isinstance(result, list)


def test_get_top_locations_for_date_no_matching_date():
    test_data = {
        "loc1": {
            "day_scores": {date(2024, 3, 14): "some_score"},
            "daily_forecasts": {date(2024, 3, 14): []},
        }
    }
    result = get_top_locations_for_date(test_data, date(2024, 3, 15))
    assert result == []


def test_normalize_score():
    """Test the score normalization logic."""
    # Test key thresholds based on piecewise linear mapping

    # Max score
    assert normalize_score(23) == 100
    assert normalize_score(25) == 100  # Cap at 100

    # Excellent threshold (18) -> 90
    assert normalize_score(18) == 90

    # Very Good threshold (13) -> 80
    assert normalize_score(13) == 80

    # Good threshold (7) -> 65
    assert normalize_score(7) == 65

    # Fair threshold (2) -> 50
    assert normalize_score(2) == 50

    # Zero/Negative
    # Score < 2: 50 + (score - 2) * 6
    # -2 -> 50 + (-4)*6 = 26
    assert normalize_score(-2) == 26

    # -10 -> 50 + (-12)*6 = -22 -> 0 (capped)
    assert normalize_score(-10) == 0

    # None
    assert normalize_score(None) == 0

    # Test user reported values with new logic
    # "17" (Very Good) -> 80 + (17-13)*2 = 88
    assert normalize_score(17) == 88

    # "3" (Fair) -> 50 + (3-2)*3 = 53
    assert normalize_score(3) == 53
