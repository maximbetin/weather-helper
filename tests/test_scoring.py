import pytest

from src.core.evaluation import cloud_score, precip_amount_score, temp_score, wind_score


@pytest.mark.parametrize("temp, expected_score", [
    (22, 7),   # Ideal temperature
    (19, 6),   # Cool but very pleasant
    (25, 6),   # Warm but very pleasant
    (16, 4),   # Cool but comfortable
    (28, 4),   # Warm but comfortable
    (12, 2),   # Cool but acceptable
    (31, 1),   # Hot but manageable
    (8, -1),   # Cold
    (34, -3),  # Very hot
    (2, -6),   # Very cold
    (38, -9),  # Extremely hot
    (-2, -9),  # Extremely cold
    (50, -15),  # Beyond extreme
    (None, 0),  # No value
])
def test_temp_score(temp, expected_score):
    assert temp_score(temp) == expected_score


@pytest.mark.parametrize("wind, expected_score", [
    (2, 2),    # Light breeze - ideal
    (0.5, 1),  # Calm - good
    (4, 0),    # Gentle breeze - neutral
    (6, -2),   # Moderate breeze - noticeable
    (10, -4),  # Fresh breeze - challenging
    (14, -6),  # Strong breeze - difficult
    (18, -7),  # Near gale - very challenging
    (25, -8),  # Gale - dangerous
    (None, 0),  # No value
])
def test_wind_score(wind, expected_score):
    assert wind_score(wind) == expected_score


@pytest.mark.parametrize("clouds, expected_score", [
    (20, 4),   # Few to scattered clouds - ideal
    (5, 3),    # Clear skies - very good
    (45, 2),   # Partly cloudy - good
    (70, 0),   # Mostly cloudy - neutral
    (85, -1),  # Very cloudy - gloomy
    (100, -3),  # Overcast - gloomy
    (None, 0),  # No value
])
def test_cloud_score(clouds, expected_score):
    assert cloud_score(clouds) == expected_score


@pytest.mark.parametrize("precip, expected_score", [
    (0, 5),     # No precipitation - best
    (0.05, 4),  # Trace amounts - barely noticeable
    (0.3, 2),   # Very light - minimal impact
    (0.7, 0),   # Light drizzle - manageable
    (1.5, -2),  # Light rain - needs preparation
    (3.5, -4),  # Moderate rain - significant impact
    (7.5, -6),  # Heavy rain - major impact
    (15, -8),   # Very heavy rain - severe impact
    (25, -12),  # Extreme precipitation - dangerous
    (None, 0),  # No value
])
def test_precip_amount_score(precip, expected_score):
    assert precip_amount_score(precip) == expected_score
