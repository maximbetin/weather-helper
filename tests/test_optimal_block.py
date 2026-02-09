from datetime import datetime, timedelta

from src.core.evaluation import find_optimal_weather_block


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
    result = find_optimal_weather_block(hours)
    assert result is not None
    # With new consistent block logic, algorithm selects blocks with good consistency
    # Test that it selects a reasonable block with good scores
    assert result["avg_score"] >= 8  # Should select reasonably good hours
    assert result["duration"] >= 1  # Should have at least 1 hour
    assert result["combined_score"] > result["avg_score"]  # Should have duration boost

    # Test with minimum duration of 2 hours
    result = find_optimal_weather_block(hours, min_duration=2)
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
    result = find_optimal_weather_block(hours)
    assert result is not None
    # Should select a good block, possibly favoring higher individual scores
    # over longer duration due to reduced duration boost
    assert result["avg_score"] >= 8  # Should select reasonably good hours
    assert result["duration"] >= 1  # Should have at least 1 hour
    assert result["combined_score"] >= result["avg_score"]  # Should have some boost

    # Test with minimum duration of 3 hours
    result = find_optimal_weather_block(hours, min_duration=3)
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
    result = find_optimal_weather_block(hours)
    assert result is None

    # Test with minimum duration
    result = find_optimal_weather_block(hours, min_duration=2)
    assert result is None  # Should still return None as no good blocks exist


def test_find_optimal_block_with_single_best_hour(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [
        create_hour(base_time, 2),
        create_hour(base_time + timedelta(hours=1), -5),
        create_hour(base_time + timedelta(hours=2), 8),  # The single best hour
        create_hour(base_time + timedelta(hours=3), -2),
    ]
    result = find_optimal_weather_block(hours)
    assert result is not None
    assert result["duration"] == 1
    assert result["start"].hour == 12

    # Test with minimum duration of 2 hours
    result = find_optimal_weather_block(hours, min_duration=2)
    assert result is None  # Should return None as no 2-hour block exists


def test_find_optimal_block_empty_input():
    result = find_optimal_weather_block([])
    assert result is None

    result = find_optimal_weather_block([], min_duration=2)
    assert result is None


def test_find_optimal_block_short_good_block(create_hour):
    base_time = datetime(2023, 1, 1, 10)
    hours = [create_hour(base_time, 8), create_hour(base_time + timedelta(hours=1), 9)]
    result = find_optimal_weather_block(hours)
    assert result is not None
    assert result["duration"] == 2

    # Test with minimum duration of 3 hours
    result = find_optimal_weather_block(hours, min_duration=3)
    assert result is None  # Should return None as block is too short
