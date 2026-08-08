"""Tests that forecasts are interpreted in each location's own time zone."""

from datetime import datetime, time, timedelta

import pytest
import pytz

from src.core.config import get_current_date, get_timezone
from src.core.evaluation import process_forecast
from src.core.locations import LOCATION_GROUPS, Location


def _timeseries_entry(timestamp: str) -> dict:
    return {
        "time": timestamp,
        "data": {
            "instant": {
                "details": {
                    "air_temperature": 20,
                    "wind_speed": 2,
                    "cloud_area_fraction": 20,
                    "relative_humidity": 55,
                }
            },
            "next_1_hours": {
                "summary": {"symbol_code": "clearsky_day"},
                "details": {
                    "precipitation_amount": 0,
                    "probability_of_precipitation": 0,
                },
            },
        },
    }


def test_every_known_location_declares_a_valid_timezone():
    for group in LOCATION_GROUPS.values():
        for location in group.values():
            assert pytz.timezone(location.timezone) is not None


def test_unknown_timezone_falls_back_to_the_default():
    assert get_timezone("Not/AZone").zone == get_timezone().zone


def _utc_timestamp_within_forecast_window(hour: int) -> datetime:
    """Return a UTC instant tomorrow, safely inside the processing window."""
    tomorrow = datetime.now(pytz.utc).date() + timedelta(days=1)
    return datetime.combine(tomorrow, time(hour=hour), tzinfo=pytz.utc)


def test_forecast_times_use_the_location_timezone():
    instant = _utc_timestamp_within_forecast_window(12)
    payload = {
        "properties": {
            "timeseries": [_timeseries_entry(instant.strftime("%Y-%m-%dT%H:%M:%SZ"))]
        }
    }

    madrid = process_forecast(payload, "Madrid", "Europe/Madrid")
    tokyo = process_forecast(payload, "Tokyo", "Asia/Tokyo")

    madrid_hour = next(iter(madrid["daily_forecasts"].values()))[0]
    tokyo_hour = next(iter(tokyo["daily_forecasts"].values()))[0]

    assert madrid_hour.time.hour == instant.astimezone(
        pytz.timezone("Europe/Madrid")
    ).hour
    assert tokyo_hour.time.hour == instant.astimezone(pytz.timezone("Asia/Tokyo")).hour
    assert madrid_hour.time.hour != tokyo_hour.time.hour


def test_a_late_utc_hour_lands_on_the_next_local_day_in_the_east():
    instant = _utc_timestamp_within_forecast_window(20)
    payload = {
        "properties": {
            "timeseries": [_timeseries_entry(instant.strftime("%Y-%m-%dT%H:%M:%SZ"))]
        }
    }

    tokyo = process_forecast(payload, "Tokyo", "Asia/Tokyo")
    madrid = process_forecast(payload, "Madrid", "Europe/Madrid")

    tokyo_date = next(iter(tokyo["daily_forecasts"]))
    madrid_date = next(iter(madrid["daily_forecasts"]))

    assert tokyo_date == instant.date() + timedelta(days=1)
    assert madrid_date == instant.date()


def test_processed_forecast_records_its_timezone():
    payload = {"properties": {"timeseries": []}}

    processed = process_forecast(payload, "London", "Europe/London")

    assert processed["timezone"] == "Europe/London"


@pytest.mark.parametrize("timezone_name", ["Pacific/Kiritimati", "Pacific/Midway"])
def test_current_date_follows_the_requested_timezone(timezone_name):
    expected = datetime.now(pytz.timezone(timezone_name)).date()

    assert get_current_date(timezone_name) == expected


def test_location_defaults_to_the_application_timezone():
    location = Location("x", "X", 0.0, 0.0)

    assert location.timezone == "Europe/Madrid"
