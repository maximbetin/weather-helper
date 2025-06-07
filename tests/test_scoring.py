import pytest
from src.core.evaluation import (
    temp_score,
    wind_score,
    cloud_score,
    precip_probability_score,
)

# Test cases for temperature scoring


@pytest.mark.parametrize("temp, expected_score", [
    (20, 8),   # Ideal
    (17, 6),   # Slightly cool
    (25, 6),   # Slightly warm
    (12, 4),   # Cool
    (28, 3),   # Warm
    (8, 0),    # Cold
    (32, -2),  # Hot
    (2, -5),   # Very cold
    (35, -5),  # Very hot
    (-2, -8),  # Extremely cold
    (38, -8),  # Extremely hot
    (50, -10),  # Beyond extreme
    (None, 0),  # No value
])
def test_temp_score(temp, expected_score):
  assert temp_score(temp) == expected_score

# Test cases for wind speed scoring


@pytest.mark.parametrize("wind, expected_score", [
    (0.5, 0),  # Calm
    (1.5, -1),  # Light air
    (3, -2),   # Light breeze
    (4, -3),   # Gentle breeze
    (7, -5),   # Moderate breeze
    (9, -7),   # Fresh breeze
    (12, -8),  # Strong breeze
    (14, -9),  # Near gale
    (16, -10),  # Gale
    (None, 0),  # No value
])
def test_wind_score(wind, expected_score):
  assert wind_score(wind) == expected_score

# Test cases for cloud coverage scoring


@pytest.mark.parametrize("clouds, expected_score", [
    (5, 5),    # Clear
    (15, 3),   # Few clouds
    (30, 1),   # Partly cloudy
    (60, -2),  # Mostly cloudy
    (80, -3),  # Very cloudy
    (95, -5),  # Overcast
    (None, 0),  # No value
])
def test_cloud_score(clouds, expected_score):
  assert cloud_score(clouds) == expected_score

# Test cases for precipitation probability scoring


@pytest.mark.parametrize("precip, expected_score", [
    (2, 0),    # Very unlikely
    (10, -1),  # Unlikely
    (20, -3),  # Slight chance
    (40, -5),  # Moderate chance
    (60, -7),  # Likely
    (80, -9),  # Very likely
    (90, -10),  # Almost certain
    (None, 0),  # No value
])
def test_precip_probability_score(precip, expected_score):
  assert precip_probability_score(precip) == expected_score
