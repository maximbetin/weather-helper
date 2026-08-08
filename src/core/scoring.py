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
DEFAULT_ACTIVITY_PROFILE = ACTIVITY_BEACH_DAY

ACTIVITY_PROFILE_LABELS = {
    ACTIVITY_HIKING: "Hiking",
    ACTIVITY_BEACH_DAY: "Beach",
}


# --- Scoring Ranges ---

# Walking warms you up, so the ideal is cooler than for sitting outdoors, and
# the range that suits it is most of an Asturian year. Heat is the harder
# problem on foot: 30C uphill is worse than 12C, which the old ordering, built
# around a sunny-Mediterranean ideal of 20-24C, had backwards.
TEMP_RANGES: List[RangeType] = [
    ((13, 21), 7),   # Ideal on foot
    ((21, 24), 6),   # Warm but very pleasant
    ((10, 13), 5),   # Cool, and fine once moving
    ((24, 27), 4),   # Warm enough to slow you down
    ((7, 10), 3),    # Brisk
    ((27, 30), 1),   # Hot for climbing
    ((3, 7), 1),     # Cold but walkable
    ((30, 33), -3),  # Uncomfortably hot on foot
    ((0, 3), -3),    # Near freezing
    ((33, 36), -7),  # Heat becomes the hazard
    ((-5, 0), -7),   # Freezing
    ((36, 40), -11),  # Dangerous heat
    (None, -15),     # Beyond extremes
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

# Cloud hardly decides whether a walk is worth taking, and a grey sky is the
# default here. Overcast costs a little for the lost views, full sun costs a
# little for the exposure, and everything between is simply walking weather.
CLOUD_RANGES: List[RangeType] = [
    ((10, 70), 2),   # Anything from bright to mostly grey
    ((0, 10), 1),    # Clear: pleasant, but no shade
    ((70, 95), 1),   # Grey, which is most days
    (None, 0),       # Overcast: the views go, the walk does not
]

# Rainfall is the measured evidence and now carries the weight that used to be
# split with the symbol, so the wet end is steeper than it was. The light end
# is deliberately forgiving: orbayu does not call off a walk, and a scale that
# treats it as though it does is no use on this coast.
PRECIP_AMOUNT_RANGES: List[RangeType] = [
    ((0, 0), 5),         # Dry
    ((0, 0.1), 4),       # Trace amounts - barely noticeable
    ((0.1, 0.4), 3),     # Orbayu: you would still go
    ((0.4, 1.0), 1),     # Light drizzle - a jacket handles it
    ((1.0, 2.0), -2),    # Light rain - needs preparation
    ((2.0, 4.0), -5),    # Moderate rain - you will get wet
    ((4.0, 8.0), -9),    # Heavy rain - major impact
    ((8.0, 15.0), -12),  # Very heavy rain - severe impact
    (None, -15),         # Extreme precipitation - dangerous
]

# Damp air is only really unpleasant when it is also warm, and at the
# temperatures this coast actually offers it is just what the air is like. It
# nudges rather than decides, on the same reasoning as the beach profile.
HUMIDITY_RANGES: List[RangeType] = [
    ((30, 90), 1),   # Ordinary, including an Atlantic 85%
    ((90, 96), 0),   # Saturated: the air feels heavy
    ((20, 30), 0),   # Dry
    (None, -1),      # Extremes either way
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

# Humidity barely changes whether a beach day is worth having: you are beside
# the water, usually in it. It used to swing 7 points -- almost two thirds of
# what sunshine is worth -- which quietly penalised every Atlantic beach town
# for the humidity that comes with being on the coast. It now nudges rather
# than decides, and ordinary coastal humidity is treated as normal.
BEACH_HUMIDITY_RANGES: List[RangeType] = [
    ((35, 85), 2),   # Anything a coastal summer normally offers
    ((85, 92), 1),   # Sticky, but not what stops a beach day
    ((25, 35), 1),   # Dry but fine
    ((92, 100), 0),  # Oppressive
    (None, 0),       # Extremes: no credit, no penalty
]

# On the Atlantic coast a decent chance of rain is the baseline condition, not
# a warning. Charging a third of the scale for a 75% chance meant an ordinary
# Asturian day could never score well, which makes the app useless exactly
# where it is used. The chance of rain now shades a judgement rather than
# dominating it; the rain that actually falls is measured separately.
PRECIP_PROBABILITY_RANGES: List[RangeType] = [
    ((0, 40), 0),     # A normal day here: nothing to plan around
    ((40, 60), -1),   # Worth taking a jacket
    ((60, 80), -2),   # Likely enough to shape the timing
    (None, -4),       # Expect to get wet at some point
]

BEACH_PRECIP_PROBABILITY_RANGES: List[RangeType] = [
    ((0, 20), 0),     # Low enough not to change beach plans
    ((20, 40), -2),   # Small but relevant when you want sun
    ((40, 60), -4),   # Showers become a real beach risk
    ((60, 80), -6),   # Too uncertain for a strong recommendation
    (None, -8),       # High risk of a wet beach window
]



# What the symbol adds beyond the numbers. Rainfall is already measured in
# millimetres, so a rain symbol mostly repeats what the amount says and only
# needs to nudge. Thunder, snow, sleet and fog are different in kind -- they
# are hazards the rainfall figure cannot express -- so those keep their weight.
SYMBOL_RISK_TERMS = (
    ("thunder", -12, -16, -20),
    ("snow", -8, -14, -14),
    ("sleet", -8, -14, -14),
    ("fog", -3, -5, -6),
    ("heavyrain", -3, -6, -8),
    ("rain", -2, -4, -4),
    ("showers", -2, -4, -2),
)

# Which of those symbols are describing the same event as the precipitation
# probability. Anything absent from this list is a separate hazard and is
# counted in its own right rather than standing in for the rain risk.
PRECIPITATION_SYMBOL_TERMS = (
    "thunder",
    "snow",
    "sleet",
    "heavyrain",
    "rain",
    "showers",
)

# Where each rating begins, as a share of the best score the profile can award.
# Expressing them this way rather than as fixed numbers is what stops the two
# drifting apart: retuning a weather element changes the maximum, and absolute
# thresholds silently become unreachable when it does. Hiking is the more
# forgiving of the two, because a walk survives weather a beach day does not.
RATING_FRACTIONS_BY_PROFILE = {
    ACTIVITY_HIKING: (0.86, 0.62, 0.33, 0.10),
    ACTIVITY_BEACH_DAY: (0.88, 0.68, 0.44, 0.20),
}


def _rating_thresholds(profile_key: str, maximum: int) -> tuple:
    """Return the excellent/very good/good/fair cut-offs for a profile."""
    fractions = RATING_FRACTIONS_BY_PROFILE[profile_key]
    return tuple(round(fraction * maximum) for fraction in fractions)


def _rating_ranges(thresholds: tuple) -> List[RangeType]:
    """Build descending rating bands from four ascending cut-offs."""
    excellent, very_good, good, fair = thresholds
    return [
        ((float(excellent), float("inf")), "Excellent"),
        ((float(very_good), float(excellent)), "Very Good"),
        ((float(good), float(very_good)), "Good"),
        ((float(fair), float(good)), "Fair"),
        (None, "Poor"),
    ]

def _best_possible(*range_lists: List[RangeType]) -> int:
    """Return the highest score these ranges can award in total."""
    return sum(max(score for _, score in ranges) for ranges in range_lists)


# The best weather a profile can possibly describe. Deriving this rather than
# hardcoding it keeps 100 meaning "as good as this activity gets" for every
# profile; a stale constant previously capped perfect hiking weather at 96.
# Rain contributes through one combined term, whose best case is a dry hour.
MAX_HIKING_SCORE = _best_possible(
    TEMP_RANGES,
    WIND_RANGES,
    CLOUD_RANGES,
    PRECIP_AMOUNT_RANGES,
    HUMIDITY_RANGES,
)
MAX_BEACH_SCORE = _best_possible(
    BEACH_TEMP_RANGES,
    BEACH_WIND_RANGES,
    BEACH_CLOUD_RANGES,
    BEACH_PRECIP_AMOUNT_RANGES,
    BEACH_HUMIDITY_RANGES,
)

HIKING_THRESHOLDS = _rating_thresholds(ACTIVITY_HIKING, MAX_HIKING_SCORE)
BEACH_THRESHOLDS = _rating_thresholds(ACTIVITY_BEACH_DAY, MAX_BEACH_SCORE)

RATING_RANGES: List[RangeType] = _rating_ranges(HIKING_THRESHOLDS)
BEACH_RATING_RANGES: List[RangeType] = _rating_ranges(BEACH_THRESHOLDS)

RATING_RANGES_BY_PROFILE = {
    ACTIVITY_HIKING: RATING_RANGES,
    ACTIVITY_BEACH_DAY: BEACH_RATING_RANGES,
}

# The word and the number come from the same cut-offs, so a rating and its
# 0-100 score can never tell different stories.
# excellent, very_good, good, fair, max_expected, poor_slope
NORMALIZATION_CONFIG_BY_PROFILE = {
    ACTIVITY_HIKING: (*HIKING_THRESHOLDS, MAX_HIKING_SCORE, 6),
    ACTIVITY_BEACH_DAY: (*BEACH_THRESHOLDS, MAX_BEACH_SCORE, 5),
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
    for term, hiking_penalty, beach_penalty, _swim_penalty in SYMBOL_RISK_TERMS:
        if term in normalized_symbol:
            if profile_key == ACTIVITY_BEACH_DAY:
                return beach_penalty
            return hiking_penalty

    return 0


def rain_risk_score(
    precipitation_probability: Optional[NumericType],
    symbol_code: Optional[str],
    profile_key: str = DEFAULT_ACTIVITY_PROFILE,
) -> int:
    """Return one risk deduction per hazard, rather than one per signal.

    The chance of rain and a rain symbol are two descriptions of the same
    forecast, so the more severe of the two stands for both; adding them on top
    of the measured rainfall deducted a single shower three times over.

    A symbol that is not about rain describes a different hazard, though. Fog
    is not the rain the probability refers to, so it still counts on its own.
    """
    if profile_key == ACTIVITY_BEACH_DAY:
        probability = beach_precip_probability_score(precipitation_probability)
    else:
        probability = precip_probability_score(precipitation_probability)

    symbol = symbol_risk_score(symbol_code, profile_key)
    if _describes_precipitation(symbol_code):
        return min(probability, symbol)
    return probability + symbol


def _describes_precipitation(symbol_code: Optional[str]) -> bool:
    """Return True when a weather symbol is describing rain, snow or sleet."""
    if not symbol_code:
        return False
    normalized = symbol_code.lower()
    return any(term in normalized for term in PRECIPITATION_SYMBOL_TERMS)


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
        + beach_humidity_score(relative_humidity)
        + beach_precip_amount_score(precipitation_amount)
        + rain_risk_score(
            precipitation_probability, symbol_code, ACTIVITY_BEACH_DAY
        )
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


def _hourly_precipitation_rate(hour: Any) -> Optional[NumericType]:
    """Return an entry's precipitation as mm per hour.

    Later forecast days only carry six-hour totals; scoring those directly
    would treat a normal wet afternoon as a downpour.
    """
    rate = getattr(hour, "precipitation_rate", None)
    if rate is not None:
        return rate
    return getattr(hour, "precipitation_amount", None)


def get_activity_score(
    hour: Any, profile_key: str = DEFAULT_ACTIVITY_PROFILE
) -> NumericType:
    """Return an hour score using the requested activity profile."""
    if profile_key == ACTIVITY_BEACH_DAY:
        return beach_day_score(
            hour.temp,
            hour.wind,
            hour.cloud_coverage,
            _hourly_precipitation_rate(hour),
            hour.relative_humidity,
            getattr(hour, "precipitation_probability", None),
            getattr(hour, "symbol_code", None),
        )

    # The stored total already carries the measured rainfall, so only the risk
    # is added here -- and rain_risk_score counts each hazard once, however
    # many signals happen to describe it.
    return hour.total_score + rain_risk_score(
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
