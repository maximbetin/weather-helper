"""The ranking, the window and the hourly breakdown share one set of hours."""

from datetime import datetime, timedelta

import pytz

from src.core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, get_current_date
from src.core.evaluation import get_recommendation_hours, get_top_locations_for_date
from src.core.models import DailyReport, HourlyWeather
from src.core.scoring import (
    ACTIVITY_HIKING,
    cloud_score,
    humidity_score,
    precip_amount_score,
    temp_score,
    wind_score,
)

MADRID = pytz.timezone("Europe/Madrid")


def _hour(forecast_date, hour_of_day, temp=22):
    """Build an entry whose scores really follow from its weather."""
    return HourlyWeather(
        time=MADRID.localize(
            datetime.combine(forecast_date, datetime.min.time())
        ).replace(hour=hour_of_day),
        temp=temp,
        wind=2,
        cloud_coverage=20,
        precipitation_amount=0.0,
        precipitation_probability=5,
        relative_humidity=55,
        temp_score=temp_score(temp),
        cloud_score=cloud_score(20),
        precip_amount_score=precip_amount_score(0.0),
        humidity_score=humidity_score(55),
        wind_score=wind_score(2),
    )


def _processed(forecast_date, hours):
    return {
        "daily_forecasts": {forecast_date: hours},
        "day_scores": {
            forecast_date: DailyReport(
                datetime.combine(forecast_date, datetime.min.time()),
                hours,
                "Test",
            )
        },
        "timezone": "Europe/Madrid",
    }


def test_night_hours_are_never_part_of_a_recommendation():
    forecast_date = get_current_date() + timedelta(days=1)
    all_day = [_hour(forecast_date, hour) for hour in range(24)]

    considered = get_recommendation_hours(_processed(forecast_date, all_day), forecast_date)

    assert considered
    for hour in considered:
        assert DAYLIGHT_START_HOUR <= hour.time.hour <= DAYLIGHT_END_HOUR


def test_hours_that_have_already_passed_today_are_excluded():
    today = get_current_date()
    all_day = [_hour(today, hour) for hour in range(24)]
    midday = MADRID.localize(
        datetime.combine(today, datetime.min.time())
    ).replace(hour=13, minute=5)

    considered = get_recommendation_hours(_processed(today, all_day), today, midday)

    # 13:00 still has 55 minutes left, so it counts; everything earlier is gone.
    assert [hour.time.hour for hour in considered] == list(
        range(13, DAYLIGHT_END_HOUR + 1)
    )


def test_an_hour_that_is_nearly_over_is_not_recommended():
    today = get_current_date()
    all_day = [_hour(today, hour) for hour in range(24)]
    nearly_two = MADRID.localize(
        datetime.combine(today, datetime.min.time())
    ).replace(hour=13, minute=45)

    considered = get_recommendation_hours(_processed(today, all_day), today, nearly_two)

    assert considered[0].time.hour == 14


def test_a_future_day_keeps_its_whole_daylight_window():
    forecast_date = get_current_date() + timedelta(days=2)
    all_day = [_hour(forecast_date, hour) for hour in range(24)]

    considered = get_recommendation_hours(_processed(forecast_date, all_day), forecast_date)

    assert [hour.time.hour for hour in considered] == list(
        range(DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR + 1)
    )


def test_todays_rank_ignores_a_good_morning_that_has_already_passed(monkeypatch):
    """The rank must describe the time you can still act on, not the whole day."""
    today = get_current_date()
    afternoon = MADRID.localize(
        datetime.combine(today, datetime.min.time())
    ).replace(hour=15)
    monkeypatch.setattr(
        "src.core.evaluation._location_now", lambda processed: afternoon
    )

    # A glorious morning followed by a cold, grim rest of the day.
    hours = [_hour(today, hour, 22) for hour in range(DAYLIGHT_START_HOUR, 15)]
    hours += [_hour(today, hour, 3) for hour in range(15, DAYLIGHT_END_HOUR + 1)]
    remaining_only = [hour for hour in hours if hour.time.hour >= 15]

    ranked_full_day = get_top_locations_for_date(
        {"a": _processed(today, hours)}, today, activity_profile=ACTIVITY_HIKING
    )
    ranked_remaining = get_top_locations_for_date(
        {"a": _processed(today, remaining_only)},
        today,
        activity_profile=ACTIVITY_HIKING,
    )

    assert ranked_full_day and ranked_remaining
    assert ranked_full_day[0]["score"] == ranked_remaining[0]["score"]


def test_night_hours_never_change_a_rank():
    forecast_date = get_current_date() + timedelta(days=1)
    daylight = list(range(DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR + 1))
    warm_day = _processed(forecast_date, [_hour(forecast_date, h, 22) for h in daylight])
    warm_day_with_cold_night = _processed(
        forecast_date,
        [_hour(forecast_date, h, 22) for h in daylight]
        + [_hour(forecast_date, h, -20) for h in (0, 1, 2, 3, 22, 23)],
    )

    ranked_clean = get_top_locations_for_date(
        {"a": warm_day}, forecast_date, activity_profile=ACTIVITY_HIKING
    )
    ranked_with_night = get_top_locations_for_date(
        {"a": warm_day_with_cold_night}, forecast_date, activity_profile=ACTIVITY_HIKING
    )

    assert ranked_clean[0]["score"] == ranked_with_night[0]["score"]


def test_the_breakdown_shows_exactly_the_hours_the_ranking_used():
    forecast_date = get_current_date() + timedelta(days=1)
    all_day = [_hour(forecast_date, hour) for hour in range(24)]
    processed = _processed(forecast_date, all_day)

    ranked = get_top_locations_for_date(
        {"a": processed}, forecast_date, activity_profile=ACTIVITY_HIKING
    )
    considered = get_recommendation_hours(processed, forecast_date)
    window = ranked[0]["optimal_block"]

    assert window["start"] >= considered[0].time
    assert window["end_time"] <= considered[-1].end_time


def test_an_entry_missing_core_readings_is_never_recommended():
    """A gap in the data must not be scored as if it were mild weather."""
    forecast_date = get_current_date() + timedelta(days=1)
    complete = [_hour(forecast_date, hour) for hour in (10, 11, 12)]
    incomplete = [
        HourlyWeather(
            time=hour.time,
            temp=None,
            wind=None,
            cloud_coverage=None,
            precipitation_amount=None,
            relative_humidity=None,
        )
        for hour in complete
    ]

    ranked_complete = get_top_locations_for_date(
        {"a": _processed(forecast_date, complete)},
        forecast_date,
        activity_profile=ACTIVITY_HIKING,
    )
    ranked_incomplete = get_top_locations_for_date(
        {"a": _processed(forecast_date, incomplete)},
        forecast_date,
        activity_profile=ACTIVITY_HIKING,
    )

    assert ranked_complete
    assert ranked_incomplete == []


def test_the_window_score_describes_the_window_not_the_day():
    """A brilliant hour in a poor day must not be reported as a poor window."""
    forecast_date = get_current_date() + timedelta(days=1)
    hours = [_hour(forecast_date, 10, 22), _hour(forecast_date, 11, 22)]
    hours += [_hour(forecast_date, hour, 2) for hour in range(12, 21)]

    ranked = get_top_locations_for_date(
        {"a": _processed(forecast_date, hours)},
        forecast_date,
        activity_profile=ACTIVITY_HIKING,
    )

    result = ranked[0]
    assert result["window_score"] > result["score"]
    assert result["optimal_block"]["start"].hour == 10
