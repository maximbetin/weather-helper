"""
Scoring logic and configuration for weather conditions.
"""

from typing import Any, List, Optional, Tuple, Union

from src.core.config import NumericType

# Type definition for ranges: ((min, max), score)
RangeType = Tuple[Optional[Tuple[Optional[float], Optional[float]]], Any]


def _get_value_from_ranges(
    value: Optional[NumericType], ranges: List[RangeType], inclusive: bool = False
) -> Optional[Any]:
    """Get a value from a list of ranges."""
    if value is None or not isinstance(value, (int, float)):
        return None

    for range_tuple, result_value in ranges:
        if range_tuple is None:  # Default case
            return result_value
        low, high = range_tuple

        # Handle None boundaries (open-ended ranges)
        if low is None:
            low = float("-inf")
        if high is None:
            high = float("inf")

        if inclusive:
            if low <= value <= high:
                return result_value
        else:
            if low <= value < high:
                return result_value

    # Return default value if found at end of list
    if ranges and ranges[-1][0] is None:
        return ranges[-1][1]

    return None


def calculate_score(
    value: Optional[NumericType], ranges: List[RangeType], inclusive: bool = False
) -> int:
    """Calculate score based on a value and a list of ranges."""
    return _get_value_from_ranges(value, ranges, inclusive) or 0


# --- Scoring Ranges ---

TEMP_RANGES: List[RangeType] = [
    ((20, 24), 7),   # Ideal temperature range
    ((17, 20), 6),   # Cool but very pleasant
    ((24, 27), 6),   # Warm but very pleasant
    ((15, 17), 4),   # Cool but comfortable
    ((27, 30), 4),   # Warm but comfortable
    ((10, 15), 2),   # Cool but acceptable
    ((30, 33), 1),   # Hot but manageable
    ((5, 10), -1),   # Cold
    ((33, 36), -3),  # Very hot
    ((0, 5), -6),    # Very cold
    ((36, 40), -9),  # Extremely hot
    ((-5, 0), -9),   # Extremely cold
    (None, -15),     # Beyond extreme temperatures
]

WIND_RANGES: List[RangeType] = [
    ((1, 3), 2),    # Light breeze - ideal for outdoor activities
    ((0, 1), 1),    # Calm - good but can feel stuffy
    ((3, 5), 0),    # Gentle breeze - neutral
    ((5, 8), -2),   # Moderate breeze - noticeable but acceptable
    ((8, 12), -4),  # Fresh breeze - can be challenging
    ((12, 16), -6), # Strong breeze - difficult for many activities
    ((16, 20), -7), # Near gale - very challenging
    (None, -8),     # Gale and above - dangerous
]

CLOUD_RANGES: List[RangeType] = [
    ((10, 30), 4),  # Few to scattered clouds - ideal
    ((0, 10), 3),   # Clear skies - very good but can be hot
    ((30, 60), 2),  # Partly cloudy - good conditions
    ((60, 80), 0),  # Mostly cloudy - neutral
    ((80, 95), -1), # Very cloudy - slightly gloomy
    (None, -3),     # Overcast - gloomy
]

PRECIP_AMOUNT_RANGES: List[RangeType] = [
    ((0, 0), 5),         # No precipitation - best
    ((0, 0.1), 4),       # Trace amounts - barely noticeable
    ((0.1, 0.5), 2),     # Very light - minimal impact
    ((0.5, 1.0), 0),     # Light drizzle - manageable
    ((1.0, 2.5), -2),    # Light rain - needs preparation
    ((2.5, 5.0), -4),    # Moderate rain - significant impact
    ((5.0, 10.0), -6),   # Heavy rain - major impact
    ((10.0, 20.0), -8),  # Very heavy rain - severe impact
    (None, -12),         # Extreme precipitation - dangerous
]

HUMIDITY_RANGES: List[RangeType] = [
    ((40, 60), 3),   # Ideal humidity range - very comfortable
    ((30, 40), 2),   # Low humidity - good but can feel dry
    ((60, 70), 1),   # Moderate humidity - acceptable
    ((20, 30), 0),   # Very low humidity - neutral
    ((70, 80), 0),   # High humidity - neutral
    ((80, 85), -1),  # Very high humidity - noticeable discomfort
    ((15, 20), -1),  # Very low humidity - can cause dryness
    ((85, 90), -2),  # Extremely high humidity - significant discomfort
    ((10, 15), -2),  # Extremely low humidity - can cause irritation
    ((90, 95), -3),  # Near saturation - very uncomfortable
    ((5, 10), -3),   # Near zero - very uncomfortable
    (None, -4),      # Beyond extreme humidity levels
]

RATING_RANGES: List[RangeType] = [
    ((18.0, float("inf")), "Excellent"),  # >= 18
    ((13.0, 18.0), "Very Good"),          # 13 <= x < 18
    ((7.0, 13.0), "Good"),                # 7 <= x < 13
    ((2.0, 7.0), "Fair"),                 # 2 <= x < 7
    (None, "Poor"),                       # < 2
]


# --- Scoring Functions ---

def temp_score(temp: Optional[NumericType]) -> int:
    """Rate temperature for outdoor comfort on a scale of -15 to 8."""
    return calculate_score(temp, TEMP_RANGES, inclusive=True)


def wind_score(wind_speed: Optional[NumericType]) -> int:
    """Rate wind speed comfort on a scale of -8 to 2."""
    return calculate_score(wind_speed, WIND_RANGES, inclusive=False)


def cloud_score(cloud_coverage: Optional[NumericType]) -> int:
    """Rate cloud coverage for outdoor activities on a scale of -3 to 4."""
    return calculate_score(cloud_coverage, CLOUD_RANGES, inclusive=False)


def precip_amount_score(amount: Optional[NumericType]) -> int:
    """Rate precipitation amount on a scale of -15 to 5."""
    return calculate_score(amount, PRECIP_AMOUNT_RANGES, inclusive=True)


def humidity_score(relative_humidity: Optional[NumericType]) -> int:
    """Rate relative humidity for outdoor comfort on a scale of -4 to 3."""
    return calculate_score(relative_humidity, HUMIDITY_RANGES, inclusive=True)


def get_rating_info(score: Union[int, float, None]) -> str:
    """Return standardized rating description based on score."""
    if score is None:
        return "N/A"
    return _get_value_from_ranges(score, RATING_RANGES, inclusive=False) or "N/A"


def normalize_score(score: Union[int, float, None]) -> int:
    """Normalize a raw score to a 0-100 scale using piecewise linear mapping.

    Mapping based on rating thresholds:
    - Excellent (>= 18) -> 90-100
    - Very Good (13-18) -> 80-90
    - Good (7-13) -> 65-80
    - Fair (2-7) -> 50-65
    - Poor (< 2) -> < 50
    """
    if score is None:
        return 0

    if score >= 18:
        # Map 18..23 to 90..100
        # Slope: 10 / 5 = 2
        normalized = 90 + (score - 18) * 2
    elif score >= 13:
        # Map 13..18 to 80..90
        # Slope: 10 / 5 = 2
        normalized = 80 + (score - 13) * 2
    elif score >= 7:
        # Map 7..13 to 65..80
        # Slope: 15 / 6 = 2.5
        normalized = 65 + (score - 7) * 2.5
    elif score >= 2:
        # Map 2..7 to 50..65
        # Slope: 15 / 5 = 3
        normalized = 50 + (score - 2) * 3
    else:
        # Map < 2 to < 50
        # Slope: 50 / 8 = 6.25 (approx, mapping -6 to 0)
        # Let's use 6 to be safe
        normalized = 50 + (score - 2) * 6

    return max(0, min(100, int(round(normalized))))
