from datetime import datetime, timedelta

from src.core.evaluation import find_optimal_weather_block
from src.core.models import HourlyWeather
from src.core.scoring import ACTIVITY_BEACH_DAY, ACTIVITY_HIKING


# Test cases for find_optimal_weather_block


def test_find_optimal_block_with_clear_winner(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, 5),
        create_hour(base_time + timedelta(hours=1), 8),
        create_hour(base_time + timedelta(hours=2), 10),
        create_hour(base_time + timedelta(hours=3), 12),
        create_hour(base_time + timedelta(hours=4), 9),
        create_hour(base_time + timedelta(hours=5), 2),
    ]
    result = find_optimal_weather_block(hours, activity_profile='hiking')
    assert result is not None
    # With new consistent block logic, algorithm selects blocks with good consistency
    # Test that it selects a reasonable block with good scores
    assert result["avg_score"] >= 8  # Should select reasonably good hours
    assert result["duration"] >= 1  # Should have at least 1 hour
    assert result["combined_score"] > result["avg_score"]  # Should have duration boost

    # Test with minimum duration of 2 hours
    result = find_optimal_weather_block(hours, min_duration=2, activity_profile='hiking')
    assert result is not None
    assert result["duration"] >= 2  # Should respect minimum duration
    assert (
        result["avg_score"] >= 8
    )  # May select different block due to duration requirement


def test_find_optimal_block_with_long_good_block(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, 8),
        create_hour(base_time + timedelta(hours=1), 9),
        create_hour(base_time + timedelta(hours=2), 10),
        create_hour(base_time + timedelta(hours=3), 11),
        create_hour(base_time + timedelta(hours=4), 12),
        create_hour(base_time + timedelta(hours=5), 5),
    ]
    result = find_optimal_weather_block(hours, activity_profile='hiking')
    assert result is not None
    # Should select a good block, possibly favoring higher individual scores
    # over longer duration due to reduced duration boost
    assert result["avg_score"] >= 8  # Should select reasonably good hours
    assert result["duration"] >= 1  # Should have at least 1 hour
    assert result["combined_score"] >= result["avg_score"]  # Should have some boost

    # Test with minimum duration of 3 hours
    result = find_optimal_weather_block(hours, min_duration=3, activity_profile='hiking')
    assert result is not None
    assert result["duration"] >= 3  # Should respect minimum duration
    assert result["avg_score"] >= 9  # Should still select good quality hours


def test_find_optimal_block_with_no_good_blocks(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, -2),
        create_hour(base_time + timedelta(hours=1), -5),
        create_hour(base_time + timedelta(hours=2), -3),
    ]
    result = find_optimal_weather_block(hours, activity_profile='hiking')
    assert result is None

    # Test with minimum duration
    result = find_optimal_weather_block(hours, min_duration=2, activity_profile='hiking')
    assert result is None  # Should still return None as no good blocks exist


def test_find_optimal_block_with_single_best_hour(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, -20),
        create_hour(base_time + timedelta(hours=1), -20),
        create_hour(base_time + timedelta(hours=2), 8),  # The single best hour
        create_hour(base_time + timedelta(hours=3), -20),
    ]
    result = find_optimal_weather_block(hours, activity_profile='hiking')
    assert result is not None
    assert result["duration"] == 1
    assert result["start"].hour == 12

    # Test with minimum duration of 2 hours
    result = find_optimal_weather_block(hours, min_duration=2, activity_profile='hiking')
    assert result is None  # Should return None as no 2-hour block exists


def test_find_optimal_block_empty_input():
    result = find_optimal_weather_block([], activity_profile='hiking')
    assert result is None

    result = find_optimal_weather_block([], min_duration=2, activity_profile='hiking')
    assert result is None


def test_find_optimal_block_short_good_block(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [create_hour(base_time, 8), create_hour(base_time + timedelta(hours=1), 9)]
    result = find_optimal_weather_block(hours, activity_profile='hiking')
    assert result is not None
    assert result["duration"] == 2

    # Test with minimum duration of 3 hours
    result = find_optimal_weather_block(hours, min_duration=3, activity_profile='hiking')
    assert result is None  # Should return None as block is too short


def test_find_optimal_block_uses_activity_profile(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    windy_hiking_hour = create_hour(
        base_time,
        total_score=20,
        temp=20,
        wind=10,
        cloud_coverage=100,
        precipitation_amount=0,
        relative_humidity=60,
    )
    beach_hour = create_hour(
        base_time + timedelta(hours=1),
        total_score=5,
        temp=27,
        wind=2,
        cloud_coverage=5,
        precipitation_amount=0,
        relative_humidity=60,
    )

    hiking_result = find_optimal_weather_block(
        [windy_hiking_hour, beach_hour],
        activity_profile=ACTIVITY_HIKING,
    )
    beach_result = find_optimal_weather_block(
        [windy_hiking_hour, beach_hour],
        activity_profile=ACTIVITY_BEACH_DAY,
    )

    assert hiking_result is not None
    assert beach_result is not None
    assert hiking_result["start"].hour == 10
    assert beach_result["start"].hour == 11


def test_find_optimal_block_does_not_bridge_forecast_gaps(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, total_score=8),
        create_hour(base_time + timedelta(hours=2), total_score=9),
    ]

    result = find_optimal_weather_block(hours, min_duration=2, activity_profile='hiking')

    assert result is None


def _beach_hour(hour_of_day, temp, cloud, precip=0.0, probability=0, symbol=None):
    """An hour whose scores follow from its weather, for calibration tests."""
    from src.core.scoring import (
        cloud_score, humidity_score, precip_amount_score, temp_score, wind_score,
    )
    return HourlyWeather(
        time=datetime(2026, 8, 20, hour_of_day),
        temp=temp, wind=3, cloud_coverage=cloud, precipitation_amount=precip,
        precipitation_probability=probability, symbol_code=symbol,
        relative_humidity=60,
        temp_score=temp_score(temp), wind_score=wind_score(3),
        cloud_score=cloud_score(cloud), precip_amount_score=precip_amount_score(precip),
        humidity_score=humidity_score(60),
    )


def test_one_cloudy_hour_does_not_cut_a_long_sunny_window_short():
    """The length of the good spell is most of the point of the recommendation."""
    hours = [_beach_hour(h, 27, 10 if h != 14 else 80) for h in range(11, 19)]

    block = find_optimal_weather_block(hours, activity_profile=ACTIVITY_BEACH_DAY)

    assert block["start"].hour == 11
    assert block["duration_hours"] == 8


def test_an_hour_of_actual_rain_still_splits_a_window():
    """Cloud is an inconvenience; rain is a reason to be somewhere else."""
    hours = [
        _beach_hour(h, 27, 10) if h != 14
        else _beach_hour(14, 22, 100, 8.0, 90, "heavyrainandthunder")
        for h in range(11, 19)
    ]

    block = find_optimal_weather_block(hours, activity_profile=ACTIVITY_BEACH_DAY)

    assert block["duration_hours"] < 8
    assert not (block["start"].hour <= 14 < block["end_time"].hour)


def test_a_longer_good_window_beats_a_shorter_flawless_one():
    six_good = [_beach_hour(h, 26, 25) for h in range(12, 18)]
    two_perfect = [_beach_hour(h, 27, 5) for h in range(12, 14)]

    long_block = find_optimal_weather_block(six_good, activity_profile=ACTIVITY_BEACH_DAY)
    short_block = find_optimal_weather_block(two_perfect, activity_profile=ACTIVITY_BEACH_DAY)

    assert short_block["avg_score"] > long_block["avg_score"]  # better conditions
    assert long_block["combined_score"] > short_block["combined_score"]  # better plan
