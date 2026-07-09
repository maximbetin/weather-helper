"""
Scoring logic and configuration for weather conditions.
"""

from typing import Any, List, Optional, Tuple, Union

from src.core.config import NumericType

# Type definition for ranges: ((min, max), score)
RangeType = Tuple[Optional[Tuple[Optional[float], Optional[float]]], Any]
RangeBounds = Tuple[float, float]

NORMALIZED_POOR_THRESHOLD = 50
NORMALIZED_FAIR_THRESHOLD = 50
NORMALIZED_GOOD_THRESHOLD = 65
NORMALIZED_VERY_GOOD_THRESHOLD = 80
NORMALIZED_EXCELLENT_THRESHOLD = 90
NORMALIZED_MIN_SCORE = 0
NORMALIZED_MAX_SCORE = 100


def _is_numeric(value: Any) -> bool:
    """Return True when the value can be scored as a number."""
    return isinstance(value, (int, float))


def _normalize_range_bounds(
    range_tuple: Tuple[Optional[float], Optional[float]]
) -> RangeBounds:
    """Convert open-ended range bounds to infinities."""
    low, high = range_tuple
    return (
        float("-inf") if low is None else low,
        float("inf") if high is None else high,
    )


def _value_in_range(value: NumericType, bounds: RangeBounds, inclusive: bool) -> bool:
    """Return True when a value falls inside a configured range."""
    low, high = bounds
    if inclusive:
        return low <= value <= high
    return low <= value < high


def _get_value_from_ranges(
    value: Optional[NumericType], ranges: List[RangeType], inclusive: bool = False
) -> Optional[Any]:
    """Get a value from a list of ranges."""
    if value is None or not _is_numeric(value):
        return None

    for range_tuple, result_value in ranges:
        if range_tuple is None:
            return result_value
        if _value_in_range(value, _normalize_range_bounds(range_tuple), inclusive):
            return result_value

    if _has_default_range(ranges):
        return ranges[-1][1]

    return None


def _has_default_range(ranges: List[RangeType]) -> bool:
    """Return True when the final range is the default fallback."""
    return bool(ranges and ranges[-1][0] is None)


def calculate_score(
    value: Optional[NumericType], ranges: List[RangeType], inclusive: bool = False
) -> int:
    """Calculate score based on a value and a list of ranges."""
    return _get_value_from_ranges(value, ranges, inclusive) or 0


# --- Activity Profiles ---

ACTIVITY_HIKING = "hiking"
ACTIVITY_BEACH_DAY = "beach_day"
DEFAULT_ACTIVITY_PROFILE = ACTIVITY_HIKING

ACTIVITY_PROFILE_LABELS = {
    ACTIVITY_HIKING: "Hiking",
    ACTIVITY_BEACH_DAY: "Beach",
}


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

BEACH_TEMP_RANGES: List[RangeType] = [
    ((24, 30), 8),   # Ideal beach warmth for swimming and sunbathing
    ((22, 24), 6),   # Warm enough for a pleasant beach day
    ((30, 32), 6),   # Hot, but still good near water
    ((20, 22), 4),   # Mild but usable
    ((32, 34), 4),   # Hot, manageable with shade and water
    ((18, 20), 2),   # Cool for lingering after swimming
    ((34, 36), 0),   # Very hot
    ((16, 18), -2),  # Chilly for beach comfort
    ((36, 39), -5),  # Heat risk starts to dominate
    ((12, 16), -6),  # Too cool for most beach plans
    (None, -10),     # Uncomfortable or unsafe extremes
]

BEACH_WIND_RANGES: List[RangeType] = [
    ((1, 4), 4),      # Light breeze, comfortable on the beach
    ((0, 1), 3),      # Calm, good for water but can feel hotter
    ((4, 6), 1),      # Noticeable but still workable
    ((6, 8), -3),     # Choppy and less comfortable for open-water swimming
    ((8, 11), -8),    # Strong beach and swim penalty
    ((11, None), -14),  # Very poor open-water conditions
    (None, -14),
]

BEACH_CLOUD_RANGES: List[RangeType] = [
    ((0, 20), 6),    # Clear to lightly cloudy: best for getting sun
    ((20, 45), 4),   # Some cloud, still good sun
    ((45, 65), 1),   # Mixed sun and cloud
    ((65, 85), -2),  # Mostly cloudy
    (None, -5),      # Overcast
]

BEACH_PRECIP_AMOUNT_RANGES: List[RangeType] = [
    ((0, 0), 5),       # Dry is best
    ((0, 0.1), 3),     # Trace amounts
    ((0.1, 0.5), -2),  # Light showers disrupt beach plans
    ((0.5, 1.0), -5),  # Wet enough to matter
    ((1.0, None), -10),  # Rain is a strong no for sunbathing/swimming plans
    (None, -10),
]

BEACH_HUMIDITY_RANGES: List[RangeType] = [
    ((45, 70), 3),  # Comfortable coastal humidity
    ((35, 45), 2),  # A little dry but pleasant
    ((70, 80), 0),  # Noticeably humid
    ((25, 35), 0),  # Dry but manageable
    ((80, 90), -2),  # Sticky and uncomfortable
    ((0, 25), -3),  # Very dry
    (None, -4),     # Oppressive humidity
]

PRECIP_PROBABILITY_RANGES: List[RangeType] = [
    ((0, 15), 0),     # Low enough not to change plans
    ((15, 35), -1),   # Some risk
    ((35, 55), -3),   # Meaningful risk
    ((55, 75), -5),   # Likely enough to plan around
    (None, -7),       # High rain risk
]

BEACH_PRECIP_PROBABILITY_RANGES: List[RangeType] = [
    ((0, 10), 0),     # Low enough not to change plans
    ((10, 25), -2),   # Small but relevant for beach plans
    ((25, 40), -4),   # Showers become a real beach risk
    ((40, 60), -7),   # Too uncertain for a strong recommendation
    (None, -10),      # High risk of a wet beach window
]

SYMBOL_RISK_TERMS = (
    ("thunder", -12, -16),
    ("snow", -8, -14),
    ("sleet", -8, -14),
    ("heavyrain", -7, -12),
    ("rain", -5, -9),
    ("showers", -4, -8),
    ("fog", -3, -5),
)

RATING_RANGES: List[RangeType] = [
    ((18.0, float("inf")), "Excellent"),  # >= 18
    ((13.0, 18.0), "Very Good"),          # 13 <= x < 18
    ((7.0, 13.0), "Good"),                # 7 <= x < 13
    ((2.0, 7.0), "Fair"),                 # 2 <= x < 7
    (None, "Poor"),                       # < 2
]

BEACH_RATING_RANGES: List[RangeType] = [
    ((22.0, float("inf")), "Excellent"),  # Excellent beach conditions
    ((17.0, 22.0), "Very Good"),
    ((11.0, 17.0), "Good"),
    ((5.0, 11.0), "Fair"),
    (None, "Poor"),
]

RATING_RANGES_BY_PROFILE = {
    ACTIVITY_HIKING: RATING_RANGES,
    ACTIVITY_BEACH_DAY: BEACH_RATING_RANGES,
}

# excellent, very_good, good, fair, max_expected, poor_slope
NORMALIZATION_CONFIG_BY_PROFILE = {
    ACTIVITY_HIKING: (18, 13, 7, 2, 23, 6),
    ACTIVITY_BEACH_DAY: (22, 17, 11, 5, 26, 5),
}


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


def beach_temp_score(temp: Optional[NumericType]) -> int:
    """Rate air temperature for a beach day."""
    return calculate_score(temp, BEACH_TEMP_RANGES, inclusive=True)


def beach_wind_score(wind_speed: Optional[NumericType]) -> int:
    """Rate wind speed for beach comfort and open-water swimming."""
    return calculate_score(wind_speed, BEACH_WIND_RANGES, inclusive=False)


def beach_cloud_score(cloud_coverage: Optional[NumericType]) -> int:
    """Rate cloud coverage for sunbathing conditions."""
    return calculate_score(cloud_coverage, BEACH_CLOUD_RANGES, inclusive=False)


def beach_precip_amount_score(amount: Optional[NumericType]) -> int:
    """Rate precipitation for a beach day."""
    return calculate_score(amount, BEACH_PRECIP_AMOUNT_RANGES, inclusive=True)


def beach_humidity_score(relative_humidity: Optional[NumericType]) -> int:
    """Rate humidity for a beach day."""
    return calculate_score(relative_humidity, BEACH_HUMIDITY_RANGES, inclusive=True)


def precip_probability_score(probability: Optional[NumericType]) -> int:
    """Rate precipitation probability for general outdoor plans."""
    return calculate_score(probability, PRECIP_PROBABILITY_RANGES, inclusive=True)


def beach_precip_probability_score(probability: Optional[NumericType]) -> int:
    """Rate precipitation probability for beach plans."""
    return calculate_score(probability, BEACH_PRECIP_PROBABILITY_RANGES, inclusive=True)


def symbol_risk_score(
    symbol_code: Optional[str],
    profile_key: str = DEFAULT_ACTIVITY_PROFILE,
) -> int:
    """Return a risk penalty based on the forecast symbol."""
    if not symbol_code:
        return 0

    normalized_symbol = symbol_code.lower()
    for term, hiking_penalty, beach_penalty in SYMBOL_RISK_TERMS:
        if term in normalized_symbol:
            if profile_key == ACTIVITY_BEACH_DAY:
                return beach_penalty
            return hiking_penalty

    return 0


def beach_day_score(
    temp: Optional[NumericType],
    wind_speed: Optional[NumericType],
    cloud_coverage: Optional[NumericType],
    precipitation_amount: Optional[NumericType],
    relative_humidity: Optional[NumericType],
    precipitation_probability: Optional[NumericType] = None,
    symbol_code: Optional[str] = None,
) -> int:
    """Score an hour for swimming and sunbathing."""
    return (
        beach_temp_score(temp)
        + beach_wind_score(wind_speed)
        + beach_cloud_score(cloud_coverage)
        + beach_precip_amount_score(precipitation_amount)
        + beach_humidity_score(relative_humidity)
        + beach_precip_probability_score(precipitation_probability)
        + symbol_risk_score(symbol_code, ACTIVITY_BEACH_DAY)
    )


def activity_risk_score(
    precipitation_probability: Optional[NumericType],
    symbol_code: Optional[str],
    profile_key: str = DEFAULT_ACTIVITY_PROFILE,
) -> int:
    """Return forecast risk adjustments for the selected profile."""
    if profile_key == ACTIVITY_BEACH_DAY:
        return (
            beach_precip_probability_score(precipitation_probability)
            + symbol_risk_score(symbol_code, profile_key)
        )

    return (
        precip_probability_score(precipitation_probability)
        + symbol_risk_score(symbol_code, profile_key)
    )


def get_activity_profile_label(profile_key: str) -> str:
    """Return a display label for an activity profile."""
    return ACTIVITY_PROFILE_LABELS.get(
        profile_key, ACTIVITY_PROFILE_LABELS[DEFAULT_ACTIVITY_PROFILE]
    )


def get_activity_profile_key(label: str) -> str:
    """Return an activity profile key from its display label."""
    for key, profile_label in ACTIVITY_PROFILE_LABELS.items():
        if profile_label == label:
            return key
    return DEFAULT_ACTIVITY_PROFILE


def get_activity_score(
    hour: Any, profile_key: str = DEFAULT_ACTIVITY_PROFILE
) -> NumericType:
    """Return an hour score using the requested activity profile."""
    if profile_key == ACTIVITY_BEACH_DAY:
        return beach_day_score(
            hour.temp,
            hour.wind,
            hour.cloud_coverage,
            hour.precipitation_amount,
            hour.relative_humidity,
            getattr(hour, "precipitation_probability", None),
            getattr(hour, "symbol_code", None),
        )

    return hour.total_score + activity_risk_score(
        getattr(hour, "precipitation_probability", None),
        getattr(hour, "symbol_code", None),
        profile_key,
    )


def get_rating_info(
    score: Union[int, float, None],
    profile_key: str = DEFAULT_ACTIVITY_PROFILE,
) -> str:
    """Return standardized rating description based on score."""
    if score is None:
        return "N/A"
    ranges = RATING_RANGES_BY_PROFILE.get(profile_key, RATING_RANGES)
    return _get_value_from_ranges(score, ranges, inclusive=False) or "N/A"


def normalize_score(
    score: Union[int, float, None],
    profile_key: str = DEFAULT_ACTIVITY_PROFILE,
) -> int:
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

    config = _get_normalization_config(profile_key)
    normalized = _calculate_normalized_score(score, config)
    return _clamp_normalized_score(normalized)


def _get_normalization_config(profile_key: str) -> tuple[int, int, int, int, int, int]:
    """Return normalization thresholds for a profile."""
    return NORMALIZATION_CONFIG_BY_PROFILE.get(
        profile_key,
        NORMALIZATION_CONFIG_BY_PROFILE[DEFAULT_ACTIVITY_PROFILE],
    )


def _calculate_normalized_score(score: Union[int, float], config: tuple) -> float:
    """Apply the piecewise score normalization formula."""
    excellent, very_good, good, fair, max_expected, poor_slope = config
    if score >= excellent:
        return _scale_score(score, excellent, max_expected, 90, 100)
    if score >= very_good:
        return _scale_score(score, very_good, excellent, 80, 90)
    if score >= good:
        return _scale_score(score, good, very_good, 65, 80)
    if score >= fair:
        return _scale_score(score, fair, good, 50, 65)
    return NORMALIZED_POOR_THRESHOLD + (score - fair) * poor_slope


def _scale_score(
    score: Union[int, float],
    lower_raw: Union[int, float],
    upper_raw: Union[int, float],
    lower_normalized: int,
    upper_normalized: int,
) -> float:
    """Scale a score between raw and normalized thresholds."""
    span = upper_normalized - lower_normalized
    return lower_normalized + (score - lower_raw) * (span / (upper_raw - lower_raw))


def _clamp_normalized_score(normalized: float) -> int:
    """Round and clamp normalized score to the display range."""
    rounded = int(round(normalized))
    return max(NORMALIZED_MIN_SCORE, min(NORMALIZED_MAX_SCORE, rounded))
