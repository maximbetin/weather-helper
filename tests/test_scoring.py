from datetime import datetime

import pytest

from src.core.scoring import (
    ACTIVITY_BEACH_DAY,
    ACTIVITY_HIKING,
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
        (22, 7),  # Ideal temperature
        (19, 6),  # Cool but very pleasant
        (25, 6),  # Warm but very pleasant
        (16, 4),  # Cool but comfortable
        (28, 4),  # Warm but comfortable
        (12, 2),  # Cool but acceptable
        (31, 1),  # Hot but manageable
        (8, -1),  # Cold
        (34, -3),  # Very hot
        (2, -6),  # Very cold
        (38, -9),  # Extremely hot
        (-2, -9),  # Extremely cold
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
        (20, 4),  # Few to scattered clouds - ideal
        (5, 3),  # Clear skies - very good
        (45, 2),  # Partly cloudy - good
        (70, 0),  # Mostly cloudy - neutral
        (85, -1),  # Very cloudy - gloomy
        (100, -3),  # Overcast - gloomy
        (None, 0),  # No value
    ],
)
def test_cloud_score(clouds, expected_score):
    assert cloud_score(clouds) == expected_score


@pytest.mark.parametrize(
    "precip, expected_score",
    [
        (0, 5),  # No precipitation - best
        (0.05, 4),  # Trace amounts - barely noticeable
        (0.3, 2),  # Very light - minimal impact
        (0.7, 0),  # Light drizzle - manageable
        (1.5, -2),  # Light rain - needs preparation
        (3.5, -4),  # Moderate rain - significant impact
        (7.5, -6),  # Heavy rain - major impact
        (15, -8),  # Very heavy rain - severe impact
        (25, -12),  # Extreme precipitation - dangerous
        (None, 0),  # No value
    ],
)
def test_precip_amount_score(precip, expected_score):
    assert precip_amount_score(precip) == expected_score


def test_beach_day_score_rewards_calm_sunny_warm_weather():
    assert beach_day_score(
        temp=27,
        wind_speed=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
    ) == 26


def test_beach_day_score_penalizes_windy_overcast_weather():
    assert beach_day_score(
        temp=20,
        wind_speed=10,
        cloud_coverage=100,
        precipitation_amount=0,
        relative_humidity=60,
    ) == -1


def test_beach_day_score_penalizes_rain_risk_and_symbols():
    assert beach_day_score(
        temp=27,
        wind_speed=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
        precipitation_probability=70,
        symbol_code="rainshowers_day",
    ) == 7


def test_precipitation_probability_is_profile_aware():
    assert precip_probability_score(45) == -3
    assert beach_precip_probability_score(45) == -7


def test_symbol_risk_is_profile_aware():
    assert symbol_risk_score("thunderstorm", ACTIVITY_HIKING) == -12
    assert symbol_risk_score("thunderstorm", ACTIVITY_BEACH_DAY) == -16


def test_activity_profile_labels_round_trip():
    assert get_activity_profile_label(ACTIVITY_HIKING) == "Hiking"
    assert get_activity_profile_key("Beach") == ACTIVITY_BEACH_DAY
    assert get_activity_profile_key("Unknown") == ACTIVITY_HIKING


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
    assert get_activity_score(hour, ACTIVITY_BEACH_DAY) == 26


def test_activity_score_applies_risk_to_hiking(create_hour):
    hour = create_hour(
        time=datetime(2024, 3, 15, 12),
        total_score=12,
        precipitation_probability=60,
        symbol_code="rain",
    )

    assert get_activity_score(hour, ACTIVITY_HIKING) == 2


def test_beach_rating_and_normalization_use_beach_thresholds():
    assert get_rating_info(21, ACTIVITY_BEACH_DAY) == "Very Good"
    assert get_rating_info(22, ACTIVITY_BEACH_DAY) == "Excellent"
    assert normalize_score(22, ACTIVITY_BEACH_DAY) == 90
    assert normalize_score(26, ACTIVITY_BEACH_DAY) == 100
