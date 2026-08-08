from datetime import datetime

import pytest

from src.core.scoring import (
    ACTIVITY_BEACH_DAY,
    ACTIVITY_HIKING,
    BEACH_CLOUD_RANGES,
    BEACH_HUMIDITY_RANGES,
    MAX_BEACH_SCORE,
    MAX_HIKING_SCORE,
    CLOUD_RANGES,
    NORMALIZATION_CONFIG_BY_PROFILE,
    _rating_thresholds,
    humidity_score,
    beach_precip_amount_score,
    rain_risk_score,
    beach_day_score,
    beach_precip_probability_score,
    get_activity_profile_key,
    get_activity_profile_label,
    get_activity_score,
    get_rating_info,
    cloud_score,
    normalize_score,
    precip_amount_score,
    precip_probability_score,
    symbol_risk_score,
    temp_score,
    wind_score,
)


@pytest.mark.parametrize(
    "temp, expected_score",
    [
        # Calibrated for walking, where you generate your own heat: the ideal
        # band is cool and wide, and heat costs more than chill.
        (19, 7),  # Ideal on foot
        (16, 7),  # Also ideal
        (22, 6),  # Warm but very pleasant
        (12, 5),  # Cool, fine once moving
        (25, 4),  # Warm enough to slow you down
        (8, 3),  # Brisk
        (28, 1),  # Hot for climbing
        (31, -3),  # Uncomfortably hot on foot
        (2, -3),  # Near freezing
        (34, -7),  # Heat becomes the hazard
        (-2, -7),  # Freezing
        (38, -11),  # Dangerous heat
        (50, -15),  # Beyond extreme
        (None, 0),  # No value
    ],
)
def test_temp_score(temp, expected_score):
    assert temp_score(temp) == expected_score


@pytest.mark.parametrize(
    "wind, expected_score",
    [
        (2, 2),  # Light breeze - ideal
        (0.5, 1),  # Calm - good
        (4, 0),  # Gentle breeze - neutral
        (6, -2),  # Moderate breeze - noticeable
        (10, -4),  # Fresh breeze - challenging
        (14, -6),  # Strong breeze - difficult
        (18, -7),  # Near gale - very challenging
        (25, -8),  # Gale - dangerous
        (None, 0),  # No value
    ],
)
def test_wind_score(wind, expected_score):
    assert wind_score(wind) == expected_score


@pytest.mark.parametrize(
    "clouds, expected_score",
    [
        # Cloud barely decides whether a walk is worth taking here.
        (20, 2),  # Bright through to mostly grey
        (45, 2),  # Partly cloudy
        (5, 1),  # Clear: pleasant, but no shade
        (85, 1),  # Grey, which is most days
        (100, 0),  # Overcast: the views go, the walk does not
        (None, 0),  # No value
    ],
)
def test_cloud_score(clouds, expected_score):
    assert cloud_score(clouds) == expected_score


@pytest.mark.parametrize(
    "precip, expected_score",
    [
        (0, 5),  # Dry
        (0.05, 4),  # Trace amounts - barely noticeable
        (0.3, 3),  # Orbayu - you would still go
        (0.7, 1),  # Light drizzle - a jacket handles it
        (1.5, -2),  # Light rain - needs preparation
        (3.5, -5),  # Moderate rain - you will get wet
        (7.5, -9),  # Heavy rain - major impact
        (15, -12),  # Very heavy rain - severe impact
        (25, -15),  # Extreme precipitation - dangerous
        (None, 0),  # No value
    ],
)
def test_precip_amount_score(precip, expected_score):
    assert precip_amount_score(precip) == expected_score


def test_beach_day_score_rewards_calm_sunny_warm_weather():
    # The best a beach hour can be. Humidity contributes only a nudge, so the
    # ceiling is the sum of temperature, wind, sun and a dry forecast.
    assert beach_day_score(
        temp=27,
        wind_speed=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
    ) == MAX_BEACH_SCORE


def test_beach_day_score_penalizes_windy_overcast_weather():
    assert beach_day_score(
        temp=20,
        wind_speed=10,
        cloud_coverage=100,
        precipitation_amount=0,
        relative_humidity=60,
    ) == -2


def test_beach_day_score_penalizes_rain_risk_and_symbols():
    assert beach_day_score(
        temp=27,
        wind_speed=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
        precipitation_probability=70,
        symbol_code="rainshowers_day",
    ) == 19  # one risk deduction, and the symbol no longer re-prices intensity


def test_precipitation_probability_is_profile_aware():
    # A 45% chance is an ordinary day for a walk here, and a real risk to a
    # beach plan, so the same number costs the two profiles differently.
    assert precip_probability_score(45) == -1
    assert beach_precip_probability_score(45) == -4


def test_symbol_risk_is_profile_aware():
    assert symbol_risk_score("thunderstorm", ACTIVITY_HIKING) == -12
    assert symbol_risk_score("thunderstorm", ACTIVITY_BEACH_DAY) == -16


def test_activity_profile_labels_round_trip():
    assert get_activity_profile_label(ACTIVITY_HIKING) == "Hiking"
    assert get_activity_profile_key("Beach") == ACTIVITY_BEACH_DAY
    assert get_activity_profile_key("Unknown") == ACTIVITY_BEACH_DAY


def test_activity_score_uses_selected_profile(create_hour):
    hour = create_hour(
        time=datetime(2024, 3, 15, 12),
        total_score=12,
        temp=27,
        wind=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
    )

    assert get_activity_score(hour, ACTIVITY_HIKING) == 12
    assert get_activity_score(hour, ACTIVITY_BEACH_DAY) == MAX_BEACH_SCORE


def test_activity_score_applies_risk_to_hiking(create_hour):
    hour = create_hour(
        time=datetime(2024, 3, 15, 12),
        total_score=12,
        precipitation_probability=60,
        symbol_code="rain",
    )

    # 60% chance and a rain symbol describe one risk, so one deduction applies,
    # and on this coast that deduction is a nudge rather than a verdict.
    assert get_activity_score(hour, ACTIVITY_HIKING) == 10


def test_beach_rating_and_normalization_use_beach_thresholds():
    assert get_rating_info(21, ACTIVITY_BEACH_DAY) == "Very Good"
    assert get_rating_info(22, ACTIVITY_BEACH_DAY) == "Excellent"
    assert normalize_score(22, ACTIVITY_BEACH_DAY) == 90
    assert normalize_score(26, ACTIVITY_BEACH_DAY) == 100


def test_perfect_conditions_reach_one_hundred_for_every_profile():
    """A 100 must mean the same thing whichever activity is selected."""
    assert normalize_score(MAX_HIKING_SCORE, ACTIVITY_HIKING) == 100
    assert normalize_score(MAX_BEACH_SCORE, ACTIVITY_BEACH_DAY) == 100


def test_the_normalisation_ceiling_matches_what_the_ranges_can_award():
    for profile, maximum in (
        (ACTIVITY_HIKING, MAX_HIKING_SCORE),
        (ACTIVITY_BEACH_DAY, MAX_BEACH_SCORE),
    ):
        assert NORMALIZATION_CONFIG_BY_PROFILE[profile][4] == maximum


def test_the_top_rating_is_reachable_for_every_profile():
    assert get_rating_info(MAX_HIKING_SCORE, ACTIVITY_HIKING) == "Excellent"
    assert get_rating_info(MAX_BEACH_SCORE, ACTIVITY_BEACH_DAY) == "Excellent"


# --- Rain is one event, not three ------------------------------------------

def test_rain_is_not_deducted_once_per_signal():
    """Amount, probability and symbol describe one shower between them."""
    dry = beach_day_score(26, 3, 20, 0.0, 60, 0, None)
    wet = beach_day_score(26, 3, 20, 0.7, 60, 50, "rain")

    amount_alone = beach_precip_amount_score(0.0) - beach_precip_amount_score(0.7)
    probability_alone = -beach_precip_probability_score(50)
    symbol_alone = -symbol_risk_score("rain", ACTIVITY_BEACH_DAY)

    # The old model summed all three; the drop must now be far short of that.
    assert dry - wet < amount_alone + probability_alone + symbol_alone


def test_the_worse_of_the_two_risk_signals_stands_for_both():
    probability_only = rain_risk_score(50, None, ACTIVITY_BEACH_DAY)
    symbol_only = rain_risk_score(None, "rain", ACTIVITY_BEACH_DAY)
    both = rain_risk_score(50, "rain", ACTIVITY_BEACH_DAY)

    assert both == min(probability_only, symbol_only)
    assert both > probability_only + symbol_only  # never the sum


def test_light_drizzle_does_not_score_like_a_storm():
    drizzle = beach_day_score(26, 3, 20, 0.2, 60, 30, "lightrainshowers_day")
    storm = beach_day_score(26, 3, 20, 8.0, 60, 90, "heavyrainandthunder")

    assert normalize_score(drizzle, ACTIVITY_BEACH_DAY) > normalize_score(
        storm, ACTIVITY_BEACH_DAY
    )
    # Drizzle is a worse hour, not a write-off.
    assert normalize_score(drizzle, ACTIVITY_BEACH_DAY) >= 50


# --- Humidity is a nudge on a beach day ------------------------------------

def test_normal_coastal_humidity_is_not_a_beach_penalty():
    """An Atlantic beach town should not be marked down for being coastal."""
    scores = {
        humidity: beach_day_score(27, 3, 10, 0.0, humidity, 0)
        for humidity in (45, 60, 70, 75, 80, 85)
    }

    assert len(set(scores.values())) == 1


def test_humidity_matters_less_than_sunshine_on_a_beach_day():
    humidity_swing = max(v for _, v in BEACH_HUMIDITY_RANGES) - min(
        v for _, v in BEACH_HUMIDITY_RANGES
    )
    cloud_swing = max(v for _, v in BEACH_CLOUD_RANGES) - min(
        v for _, v in BEACH_CLOUD_RANGES
    )

    assert humidity_swing * 3 <= cloud_swing


def test_heavier_rain_always_scores_worse_than_lighter_rain():
    """When every option is wet, the ranking must still say which is least bad."""
    scores = [
        beach_day_score(26, 3, 20, mm, 60, probability, symbol)
        for mm, probability, symbol in (
            (0.2, 30, "lightrainshowers_day"),
            (0.7, 50, "rain"),
            (3.0, 80, "heavyrain"),
            (20.0, 95, "heavyrainandthunder"),
        )
    ]

    assert scores == sorted(scores, reverse=True)
    assert len(set(scores)) == len(scores)


def test_a_wet_hour_is_still_too_poor_to_recommend():
    """Softening the rain penalty must not make a rainy day recommendable."""
    soaked = beach_day_score(22, 3, 50, 3.0, 70, 80, "rain")

    assert normalize_score(soaked, ACTIVITY_BEACH_DAY) < 25
    assert get_rating_info(soaked, ACTIVITY_BEACH_DAY) == "Poor"


def test_fog_is_a_separate_hazard_from_the_chance_of_rain():
    """Fog is not the rain the probability is describing, so it still counts."""
    rain_only = rain_risk_score(80, None, ACTIVITY_HIKING)
    with_fog = rain_risk_score(80, "fog", ACTIVITY_HIKING)

    assert with_fog < rain_only


def test_a_rain_symbol_does_not_stack_with_the_chance_of_rain():
    probability_only = rain_risk_score(50, None, ACTIVITY_BEACH_DAY)
    with_rain_symbol = rain_risk_score(50, "rain", ACTIVITY_BEACH_DAY)

    assert with_rain_symbol == min(
        probability_only, symbol_risk_score("rain", ACTIVITY_BEACH_DAY)
    )


# --- Hiking is calibrated for this coast, not a sunny-Mediterranean ideal ---

def test_a_grey_dry_asturian_day_is_good_walking_weather():
    """17C and overcast is the standard good walk here, not a mediocre one."""
    score = (
        temp_score(17)
        + wind_score(4)
        + cloud_score(100)
        + humidity_score(82)
        + precip_amount_score(0.0)
    )

    assert get_rating_info(score, ACTIVITY_HIKING) in ("Very Good", "Excellent")


def test_walking_prefers_cool_over_hot():
    """You make your own heat on foot, so 30C is worse than 12C."""
    assert temp_score(12) > temp_score(30)
    assert temp_score(17) > temp_score(28)


def test_cloud_barely_moves_a_walk_but_still_decides_a_beach_day():
    hiking_swing = max(v for _, v in CLOUD_RANGES) - min(v for _, v in CLOUD_RANGES)
    beach_swing = max(v for _, v in BEACH_CLOUD_RANGES) - min(
        v for _, v in BEACH_CLOUD_RANGES
    )

    assert hiking_swing * 3 <= beach_swing


def test_atlantic_humidity_is_not_a_penalty_for_either_activity():
    for humidity in (70, 80, 85):
        assert humidity_score(humidity) == humidity_score(50)


def test_rating_thresholds_follow_the_best_score_a_profile_can_award():
    """Retuning an element must never make a rating unreachable."""
    for profile, maximum in (
        (ACTIVITY_HIKING, MAX_HIKING_SCORE),
        (ACTIVITY_BEACH_DAY, MAX_BEACH_SCORE),
    ):
        thresholds = _rating_thresholds(profile, maximum)
        assert thresholds == tuple(sorted(thresholds, reverse=True))
        assert thresholds[0] <= maximum
        assert get_rating_info(maximum, profile) == "Excellent"
        # The word and the number are cut from the same cloth.
        assert NORMALIZATION_CONFIG_BY_PROFILE[profile][:4] == thresholds
