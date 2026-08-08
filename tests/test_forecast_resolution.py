"""Tests for six-hourly forecast data being reported and scored honestly."""

from datetime import datetime, timedelta

import pytz

from src.core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR
from src.core.evaluation import (
    _are_adjacent_forecast_hours,
    daylight_bounds,
    find_optimal_weather_block,
    process_forecast,
)
from src.core.models import HourlyWeather
from src.core.scoring import ACTIVITY_BEACH_DAY, get_activity_score

MADRID = pytz.timezone("Europe/Madrid")


def _entry(timestamp: str, period_key: str, precipitation: float) -> dict:
    return {
        "time": timestamp,
        "data": {
            "instant": {
                "details": {
                    "air_temperature": 22,
                    "wind_speed": 2,
                    "cloud_area_fraction": 15,
                    "relative_humidity": 55,
                }
            },
            period_key: {
                "summary": {"symbol_code": "rain"},
                "details": {
                    "precipitation_amount": precipitation,
                    "probability_of_precipitation": 20,
                },
            },
        },
    }


def _hour(hour: int, coverage_hours: int = 1, **kwargs) -> HourlyWeather:
    base = datetime.now(MADRID).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    return HourlyWeather(
        time=base + timedelta(hours=hour),
        coverage_hours=coverage_hours,
        temp=22,
        wind=2,
        cloud_coverage=15,
        relative_humidity=55,
        **kwargs,
    )


def _tomorrow_utc(hour: int) -> str:
    instant = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1, hours=hour)
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_hourly_entries_are_marked_as_one_hour():
    payload = {
        "properties": {"timeseries": [_entry(_tomorrow_utc(10), "next_1_hours", 0.2)]}
    }

    processed = process_forecast(payload, "Test", "Europe/Madrid")
    hour = next(iter(processed["daily_forecasts"].values()))[0]

    assert hour.coverage_hours == 1
    assert hour.is_hourly
    assert hour.precipitation_rate == 0.2


def test_six_hourly_entries_record_their_span_and_rate():
    payload = {
        "properties": {"timeseries": [_entry(_tomorrow_utc(10), "next_6_hours", 3.0)]}
    }

    processed = process_forecast(payload, "Test", "Europe/Madrid")
    hour = next(iter(processed["daily_forecasts"].values()))[0]

    assert hour.coverage_hours == 6
    assert not hour.is_hourly
    # 3 mm spread over six hours is light drizzle, not heavy rain.
    assert hour.precipitation_amount == 3.0
    assert hour.precipitation_rate == 0.5
    assert hour.end_time == hour.time + timedelta(hours=6)


def test_a_six_hour_total_is_not_scored_as_one_hour_of_rain():
    six_hourly = _hour(10, coverage_hours=6, precipitation_amount=3.0)
    hourly = _hour(10, coverage_hours=1, precipitation_amount=3.0)

    assert get_activity_score(six_hourly, ACTIVITY_BEACH_DAY) > get_activity_score(
        hourly, ACTIVITY_BEACH_DAY
    )


def test_entries_are_adjacent_when_one_ends_where_the_next_starts():
    assert _are_adjacent_forecast_hours(_hour(10), _hour(11))
    assert _are_adjacent_forecast_hours(
        _hour(6, coverage_hours=6), _hour(12, coverage_hours=6)
    )


def test_entries_of_different_resolutions_are_never_adjacent():
    assert not _are_adjacent_forecast_hours(_hour(10), _hour(11, coverage_hours=6))


def test_entries_with_a_gap_between_them_are_not_adjacent():
    assert not _are_adjacent_forecast_hours(_hour(10), _hour(13))


def test_a_block_reports_the_hours_it_actually_covers():
    block = find_optimal_weather_block(
        [_hour(8, coverage_hours=6, precipitation_amount=0.0)],
        activity_profile=ACTIVITY_BEACH_DAY,
    )

    assert block is not None
    assert block["duration"] == 1
    assert block["duration_hours"] == 6
    assert block["end_time"] == block["end"] + timedelta(hours=6)


def test_a_window_is_never_reported_as_starting_before_dawn():
    """A six-hour entry can start at 04:00; a recommendation cannot."""
    pre_dawn = _hour(4, coverage_hours=6, precipitation_amount=0.0)

    block = find_optimal_weather_block(
        [pre_dawn], activity_profile=ACTIVITY_BEACH_DAY
    )

    assert block is not None
    assert block["start"].hour == DAYLIGHT_START_HOUR
    # Only the daylight part of the entry counts as time you can use.
    assert block["duration_hours"] == 2


def test_a_window_is_never_reported_as_running_past_dusk():
    late = _hour(18, coverage_hours=6, precipitation_amount=0.0)

    block = find_optimal_weather_block([late], activity_profile=ACTIVITY_BEACH_DAY)

    assert block is not None
    assert block["end_time"].hour == DAYLIGHT_END_HOUR + 1
    assert block["duration_hours"] == 3


def test_daylight_bounds_leave_an_ordinary_hour_alone():
    midday = _hour(12)

    start, end = daylight_bounds(midday)

    assert start == midday.time
    assert end == midday.end_time
