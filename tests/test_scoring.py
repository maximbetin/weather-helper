import pytest

from src.core.evaluation import cloud_score, temp_score, wind_score


@pytest.mark.parametrize("temp, expected_score", [
    (20, 6),   # Ideal
    (17, 4),   # Slightly cool
    (25, 4),   # Slightly warm
    (12, 2),   # Cool
    (28, 1),   # Warm
    (8, -1),   # Cold
    (32, -3),  # Hot
    (2, -6),   # Very cold
    (35, -6),  # Very hot
    (-2, -9),  # Extremely cold
    (38, -9),  # Extremely hot
    (50, -12),  # Beyond extreme
    (None, 0),  # No value
])
def test_temp_score(temp, expected_score):
  assert temp_score(temp) == expected_score

# Test cases for wind speed scoring


@pytest.mark.parametrize("wind, expected_score", [
    (0.5, 0),  # Calm
    (1.5, 0),  # Light air
    (3, -1),   # Light breeze
    (4, -1),   # Gentle breeze
    (6, -3),   # Moderate breeze
    (9, -5),   # Fresh breeze
    (12, -7),  # Strong breeze
    (14, -8),  # Near gale
    (16, -10),  # Gale
    (None, 0),  # No value
])
def test_wind_score(wind, expected_score):
  assert wind_score(wind) == expected_score

# Test cases for cloud coverage scoring


@pytest.mark.parametrize("clouds, expected_score", [
    (5, 4),    # Clear
    (15, 3),   # Few clouds
    (30, 2),   # Partly cloudy
    (60, 0),   # Mostly cloudy
    (80, -2),  # Very cloudy
    (95, -4),  # Overcast
    (None, 0),  # No value
])
def test_cloud_score(clouds, expected_score):
  assert cloud_score(clouds) == expected_score
