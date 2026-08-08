"""The ranked list must answer the question it is asked: where should I go.

These tests describe the judgements the ranking is meant to make, in the terms
someone deciding their afternoon would use, rather than the arithmetic that
happens to produce them.
"""

from datetime import datetime

import pytz

from src.core.evaluation import _duration_factor, get_top_locations_for_date
from src.core.models import DailyReport, HourlyWeather
from src.core.scoring import (
    ACTIVITY_BEACH_DAY,
    cloud_score,
    humidity_score,
    normalize_score,
    precip_amount_score,
    temp_score,
    wind_score,
)

MADRID = pytz.timezone("Europe/Madrid")
DAY = datetime(2026, 8, 20)


def _hour(hour_of_day, temp, cloud, precip=0.0, probability=0, symbol=None):
    return HourlyWeather(
        time=MADRID.localize(DAY).replace(hour=hour_of_day),
        temp=temp,
        wind=3,
        cloud_coverage=cloud,
        precipitation_amount=precip,
        precipitation_probability=probability,
        symbol_code=symbol,
        relative_humidity=60,
        temp_score=temp_score(temp),
        wind_score=wind_score(3),
        cloud_score=cloud_score(cloud),
        precip_amount_score=precip_amount_score(precip),
        humidity_score=humidity_score(60),
    )


def _location(hours, name):
    return {
        "daily_forecasts": {DAY.date(): hours},
        "day_scores": {DAY.date(): DailyReport(DAY, hours, name)},
        "timezone": "Europe/Madrid",
    }


def _rank(**locations):
    ranked = get_top_locations_for_date(
        {key: _location(hours, key) for key, hours in locations.items()},
        DAY.date(),
        activity_profile=ACTIVITY_BEACH_DAY,
    )
    return [item["location_key"] for item in ranked]


GREY_THEN_PERFECT = [
    _hour(h, 17 if h < 14 else 28, 100 if h < 14 else 5) for h in range(8, 21)
]
FLAT_AND_HAZY = [_hour(h, 21, 75) for h in range(8, 21)]
PLEASANT_NEVER_GREAT = [_hour(h, 22, 55) for h in range(8, 21)]
ONE_PERFECT_HOUR = [
    _hour(h, 28 if h == 14 else 19, 5 if h == 14 else 85) for h in range(8, 21)
]
SOLID_AFTERNOON = [
    _hour(h, 26 if 13 <= h <= 18 else 20, 20 if 13 <= h <= 18 else 80)
    for h in range(8, 21)
]


def test_a_perfect_afternoon_beats_a_day_that_is_never_actually_good():
    """A grey morning is not a reason to go somewhere duller: you sleep in."""
    order = _rank(perfect_pm=GREY_THEN_PERFECT, never_great=PLEASANT_NEVER_GREAT)

    assert order[0] == "perfect_pm"


def test_a_perfect_afternoon_beats_a_flat_hazy_day():
    order = _rank(perfect_pm=GREY_THEN_PERFECT, hazy=FLAT_AND_HAZY)

    assert order[0] == "perfect_pm"


def test_a_long_good_window_beats_a_single_perfect_hour():
    order = _rank(six_hours=SOLID_AFTERNOON, one_hour=ONE_PERFECT_HOUR)

    assert order == ["six_hours", "one_hour"]


def test_a_single_perfect_hour_keeps_its_honest_conditions_score():
    """The hour really is perfect; it is the day out that is not."""
    ranked = get_top_locations_for_date(
        {"one_hour": _location(ONE_PERFECT_HOUR, "One hour")},
        DAY.date(),
        activity_profile=ACTIVITY_BEACH_DAY,
    )
    result = ranked[0]

    assert normalize_score(result["window_score"], ACTIVITY_BEACH_DAY) == 100
    assert normalize_score(result["score"], ACTIVITY_BEACH_DAY) < 60


def test_the_whole_ordering_matches_how_a_person_would_choose():
    order = _rank(
        perfect_pm=GREY_THEN_PERFECT,
        six_hours=SOLID_AFTERNOON,
        never_great=PLEASANT_NEVER_GREAT,
        hazy=FLAT_AND_HAZY,
        one_hour=ONE_PERFECT_HOUR,
    )

    assert order == ["perfect_pm", "six_hours", "never_great", "hazy", "one_hour"]


def test_duration_credit_grows_with_length_and_then_stops():
    factors = [_duration_factor(hours) for hours in range(1, 9)]

    assert factors == sorted(factors)
    assert factors[0] < 0.5  # one hour is not a day out
    assert factors[-1] == 1.0  # a long window is not discounted
    assert _duration_factor(6) == _duration_factor(12)


def test_a_bad_window_is_not_flattered_by_being_long():
    """Scaling must not turn a negative score into a better one."""
    from src.core.evaluation import _sustained_quality

    assert _sustained_quality(-8, 1) == -8
    assert _sustained_quality(-8, 8) == -8


def test_a_wet_beach_day_offers_no_window_at_all():
    """Rain rules out a beach plan, so the screen should say so plainly."""
    from src.core.evaluation import find_optimal_weather_block

    wet = [
        _hour(h, 22, 50, precip=3.0, probability=80, symbol="rain")
        for h in range(10, 18)
    ]

    assert find_optimal_weather_block(wet, activity_profile=ACTIVITY_BEACH_DAY) is None


def test_a_marginal_hiking_window_is_surfaced_but_rated_poor():
    """Walking in drizzle is a choice; the rating has to make it an informed one.

    Counting rain once rather than three times means marginal conditions now
    produce a window where they previously produced nothing. That is useful
    when every option is wet and you still have to pick one, but only as long
    as the rating is honest about what is on offer.
    """
    from src.core.evaluation import find_optimal_weather_block
    from src.core.scoring import ACTIVITY_HIKING, get_rating_info

    drizzly = [
        _hour(h, 22, 50, precip=3.0, probability=80, symbol="rain")
        for h in range(10, 18)
    ]

    block = find_optimal_weather_block(drizzly, activity_profile=ACTIVITY_HIKING)

    assert block is not None
    assert get_rating_info(block["avg_score"], ACTIVITY_HIKING) == "Poor"
    assert normalize_score(block["avg_score"], ACTIVITY_HIKING) < 50
