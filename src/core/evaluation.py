"""
Evaluation and scoring logic for weather forecasts.
Provides functions to process forecasts, evaluate blocks, and rank locations.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from src.core.config import (
    DAYLIGHT_END_HOUR,
    DAYLIGHT_START_HOUR,
    FORECAST_DAYS,
    NumericType,
    get_current_date,
    get_timezone,
    safe_average,
)
from src.core.models import DailyReport, HourlyWeather
from src.core.scoring import (
    DEFAULT_ACTIVITY_PROFILE,
    cloud_score,
    get_activity_score,
    humidity_score,
    precip_amount_score,
    temp_score,
    wind_score,
)

HOURLY_COVERAGE_HOURS = 1
SIX_HOURLY_COVERAGE_HOURS = 6
ADJACENT_TOLERANCE_MINUTES = 10
CURRENT_HOUR_RELEVANCE_MINUTE = 30
DEFAULT_MAX_SCORE_VARIANCE = 7.0
OPTIMAL_MAX_SCORE_VARIANCE = 8.0
SINGLE_HOUR_MIN_AVG_SCORE = -1
MULTI_HOUR_MIN_AVG_SCORE = 0
VARIANCE_THRESHOLD_PER_EXTRA_HOUR = 0.8
MAX_DURATION_BONUS = 5.0
DURATION_BONUS_SATURATION_RATE = 0.35
CONSISTENCY_BONUS_WEIGHT = 2.0
WEAK_HOUR_PENALTY_WEIGHT = 0.2
DAY_SCORE_CHANGE_TOLERANCE = 4.0
DAY_SCORE_VOLATILITY_WEIGHT = 0.35
MAX_DAY_VOLATILITY_PENALTY = 10.0


def _calculate_weather_averages(
    hours: list[HourlyWeather],
) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """Calculate average temperature, wind, humidity, and precipitation."""
    return (
        _average_hour_attribute(hours, "temp"),
        _average_hour_attribute(hours, "wind"),
        _average_hour_attribute(hours, "relative_humidity"),
        _average_hour_attribute(hours, "precipitation_amount"),
    )


def _average_hour_attribute(
    hours: list[HourlyWeather], attribute_name: str
) -> Optional[float]:
    """Average numeric values for a single HourlyWeather attribute."""
    values = [
        getattr(hour, attribute_name)
        for hour in hours
        if getattr(hour, attribute_name) is not None
    ]
    return safe_average(values)


def _calculate_block_details(hours: list[HourlyWeather]) -> dict[str, Any]:
    """Calculate display and risk details for a weather block."""
    clouds = [h.cloud_coverage for h in hours if h.cloud_coverage is not None]
    precip_probs = [h.precipitation_probability for h in hours if h.precipitation_probability is not None]
    symbols = sorted({h.symbol_code for h in hours if h.symbol_code})
    return {
        "cloud": safe_average(clouds),
        "precip_probability": safe_average(precip_probs),
        "symbols": symbols,
    }


def _are_adjacent_forecast_hours(
    previous_hour: HourlyWeather,
    next_hour: HourlyWeather,
) -> bool:
    """Return True when one forecast entry continues directly into the next.

    Entries are adjacent when the next one starts where the previous one stops,
    which keeps hourly and six-hourly data on the same footing and refuses to
    bridge a gap between two different resolutions.
    """
    if previous_hour.coverage_hours != next_hour.coverage_hours:
        return False
    gap = abs(next_hour.time - previous_hour.end_time)
    return gap <= timedelta(minutes=ADJACENT_TOLERANCE_MINUTES)


def _get_period_data(
    entry: dict[str, Any], period_key: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return summary and detail dictionaries for a forecast period."""
    period = entry["data"].get(period_key, {})
    return period.get("summary", {}), period.get("details", {})


def _is_daylight_hour(hour: HourlyWeather) -> bool:
    """Return True when an entry overlaps the configured daytime window.

    Six-hourly entries are kept when any part of them falls inside the window,
    so a 06:00-12:00 entry still counts towards a morning recommendation.
    """
    starts_before_window_ends = hour.hour <= DAYLIGHT_END_HOUR
    ends_after_window_starts = (
        hour.hour + hour.coverage_hours > DAYLIGHT_START_HOUR
    )
    return starts_before_window_ends and ends_after_window_starts


def daylight_bounds(hour: HourlyWeather) -> tuple[datetime, datetime]:
    """Return the part of an entry that falls inside the daylight window.

    A six-hour entry starting at 04:00 counts towards the morning, but telling
    someone their best window begins at 04:00 would be nonsense. Only the
    daylight part of an entry is ever presented as time to go out.
    """
    day_start = hour.time.replace(
        hour=DAYLIGHT_START_HOUR, minute=0, second=0, microsecond=0
    )
    day_end = hour.time.replace(
        hour=DAYLIGHT_END_HOUR, minute=0, second=0, microsecond=0
    ) + timedelta(hours=1)
    start = max(hour.time, day_start)
    end = min(hour.end_time, day_end)
    return start, max(start, end)


def _is_future_or_current_hour(hour: HourlyWeather, now_local: datetime) -> bool:
    """Return True when an entry still has usable time left in it.

    An entry counts while it is running, but only if enough of it remains to be
    worth recommending, so a window is never suggested as it is ending.
    """
    if hour.time > now_local:
        return True
    remaining = hour.end_time - now_local
    return remaining >= timedelta(minutes=CURRENT_HOUR_RELEVANCE_MINUTE)


def _filter_hours_for_recommendations(
    hours: list[HourlyWeather],
    forecast_date: date,
    now_local: datetime,
) -> list[HourlyWeather]:
    """Filter hours to the daytime rows still relevant for a selected date."""
    daylight_hours = [hour for hour in hours if _is_daylight_hour(hour)]
    if forecast_date != now_local.date():
        return daylight_hours
    return [hour for hour in daylight_hours if _is_future_or_current_hour(hour, now_local)]


def find_optimal_weather_block(
    hours: list[HourlyWeather],
    min_duration: int = 1,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> Optional[dict[str, Any]]:
    """Find the optimal weather block for outdoor activities."""
    if not hours:
        return None
    sorted_hours = sorted(hours, key=lambda x: x.time)
    optimal_block = _find_optimal_consistent_block(
        sorted_hours,
        activity_profile,
        min_duration=min_duration,
    )
    return _valid_minimum_duration_block(optimal_block, min_duration)


def _valid_minimum_duration_block(
    block: Optional[dict[str, Any]], min_duration: int
) -> Optional[dict[str, Any]]:
    """Return a block only when it satisfies the requested duration."""
    if not block or block["duration"] < min_duration:
        return None
    return block


def _create_hourly_weather(
    entry: dict[str, Any], timezone_name: Optional[str] = None
) -> HourlyWeather:
    """Create an HourlyWeather object from a forecast timeseries entry."""
    weather_values = _extract_hourly_weather_values(entry, timezone_name)
    return _build_hourly_weather(weather_values)


def _extract_hourly_weather_values(
    entry: dict[str, Any], timezone_name: Optional[str] = None
) -> dict[str, Any]:
    """Extract raw weather values from a timeseries entry."""
    instant_details = entry["data"]["instant"]["details"]
    precipitation_amount, precipitation_probability = _get_precipitation_values(entry)

    return {
        "coverage_hours": _get_coverage_hours(entry),
        "time": _parse_local_forecast_time(entry["time"], timezone_name),
        "temp": instant_details.get("air_temperature"),
        "wind": instant_details.get("wind_speed"),
        "cloud_coverage": instant_details.get("cloud_area_fraction"),
        "precipitation_amount": precipitation_amount,
        "precipitation_probability": precipitation_probability,
        "symbol_code": _get_symbol_code(entry),
        "relative_humidity": instant_details.get("relative_humidity"),
        "water_temp": None,
        "wave_height": None,
    }


def _parse_local_forecast_time(
    timestamp: str, timezone_name: Optional[str] = None
) -> datetime:
    """Parse an API timestamp into a location's local time."""
    time_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return time_utc.astimezone(get_timezone(timezone_name))


def _get_coverage_hours(entry: dict[str, Any]) -> int:
    """Return how many hours a timeseries entry describes.

    MET Norway publishes hourly entries for roughly the first two days and
    six-hourly entries after that. Treating a six-hour entry as a single hour
    would misreport both rain totals and the length of a recommended window.
    """
    next_1h_summary, next_1h_details = _get_period_data(entry, "next_1_hours")
    if next_1h_summary or next_1h_details:
        return HOURLY_COVERAGE_HOURS
    next_6h_summary, next_6h_details = _get_period_data(entry, "next_6_hours")
    if next_6h_summary or next_6h_details:
        return SIX_HOURLY_COVERAGE_HOURS
    return HOURLY_COVERAGE_HOURS


def _get_precipitation_values(
    entry: dict[str, Any]
) -> tuple[Optional[NumericType], Optional[NumericType]]:
    """Return amount and probability using 1-hour data with 6-hour fallback."""
    _, next_1h_details = _get_period_data(entry, "next_1_hours")
    _, next_6h_details = _get_period_data(entry, "next_6_hours")
    return (
        _first_available_detail(next_1h_details, next_6h_details, "precipitation_amount"),
        _first_available_detail(next_1h_details, next_6h_details, "probability_of_precipitation"),
    )


def _first_available_detail(
    primary_details: dict[str, Any], fallback_details: dict[str, Any], key: str
) -> Optional[NumericType]:
    """Return a detail from primary data, falling back to longer-period data."""
    primary_value = primary_details.get(key)
    if primary_value is not None:
        return primary_value
    return fallback_details.get(key)


def _get_symbol_code(entry: dict[str, Any]) -> Optional[str]:
    """Return the most specific available weather symbol code."""
    next_1h_summary, _ = _get_period_data(entry, "next_1_hours")
    next_6h_summary, _ = _get_period_data(entry, "next_6_hours")
    return next_1h_summary.get("symbol_code") or next_6h_summary.get("symbol_code")


def _build_hourly_weather(values: dict[str, Any]) -> HourlyWeather:
    """Build an HourlyWeather object with component scores."""
    return HourlyWeather(
        **values,
        temp_score=temp_score(values["temp"]),
        wind_score=wind_score(values["wind"]),
        cloud_score=cloud_score(values["cloud_coverage"]),
        precip_amount_score=precip_amount_score(_precipitation_rate(values)),
        humidity_score=humidity_score(values["relative_humidity"]),
    )


def _precipitation_rate(values: dict[str, Any]) -> Optional[NumericType]:
    """Return precipitation in mm per hour for an extracted entry."""
    amount = values["precipitation_amount"]
    if amount is None:
        return None
    return amount / max(1, values.get("coverage_hours", HOURLY_COVERAGE_HOURS))


def _process_timeseries(
    forecast_timeseries: list[dict[str, Any]],
    timezone_name: Optional[str] = None,
) -> dict[date, list[HourlyWeather]]:
    """Group a raw forecast timeseries by the location's local date."""
    daily_forecasts: dict[date, list[HourlyWeather]] = defaultdict(list)
    today = get_current_date(timezone_name)
    end_date = today + timedelta(days=FORECAST_DAYS)

    for entry in forecast_timeseries:
        _append_forecast_entry(entry, daily_forecasts, today, end_date, timezone_name)

    return dict(daily_forecasts)


def _append_forecast_entry(
    entry: dict[str, Any],
    daily_forecasts: dict[date, list[HourlyWeather]],
    today: date,
    end_date: date,
    timezone_name: Optional[str] = None,
) -> None:
    """Append a timeseries entry to the corresponding daily forecast list."""
    forecast_time = _parse_local_forecast_time(entry["time"], timezone_name)
    forecast_date = forecast_time.date()

    if today <= forecast_date <= end_date:
        daily_forecasts[forecast_date].append(
            _create_hourly_weather(entry, timezone_name)
        )


def process_forecast(
    forecast_data: dict,
    location_name: str,
    timezone_name: Optional[str] = None,
) -> Optional[dict]:
    """Process weather forecast data into daily summaries and hourly blocks.

    All times are converted to the location's own time zone, so the daylight
    window and "already passed" checks describe the place being forecast rather
    than wherever the app happens to be configured.
    """
    weather_data = forecast_data.get("weather", forecast_data)

    forecast_timeseries = _get_forecast_timeseries(weather_data)
    if forecast_timeseries is None:
        return None

    daily_forecasts = _process_timeseries(forecast_timeseries, timezone_name)
    day_scores_reports = _build_daily_reports(daily_forecasts, location_name)
    return {
        "daily_forecasts": daily_forecasts,
        "day_scores": day_scores_reports,
        "timezone": timezone_name,
    }


def _get_forecast_timeseries(forecast_data: dict) -> Optional[list[dict[str, Any]]]:
    """Return timeseries data when the forecast payload is valid."""
    if not forecast_data or "properties" not in forecast_data:
        return None
    return forecast_data["properties"].get("timeseries")


def _build_daily_reports(
    daily_forecasts: dict[date, list[HourlyWeather]], location_name: str
) -> dict[date, DailyReport]:
    """Create daily reports for dates with daylight forecast hours."""
    day_scores_reports = {}
    for forecast_date, hours_list in daily_forecasts.items():
        daylight_hours = [hour for hour in hours_list if _is_daylight_hour(hour)]
        if daylight_hours:
            day_scores_reports[forecast_date] = _daily_report(
                forecast_date, daylight_hours, location_name
            )
    return day_scores_reports


def _daily_report(
    forecast_date: date, daylight_hours: list[HourlyWeather], location_name: str
) -> DailyReport:
    """Create one DailyReport from a forecast date and daylight hours."""
    report_date = datetime.combine(forecast_date, datetime.min.time())
    return DailyReport(report_date, daylight_hours, location_name)


def get_available_dates(processed_forecast: dict) -> list[date]:
    """Return all available dates for a processed forecast."""
    if not processed_forecast or "daily_forecasts" not in processed_forecast:
        return []
    return sorted(processed_forecast["daily_forecasts"].keys())


def get_time_blocks_for_date(processed_forecast: dict, d: date) -> list[HourlyWeather]:
    """Return all HourlyWeather blocks for a given date."""
    if not processed_forecast or "daily_forecasts" not in processed_forecast:
        return []
    return sorted(processed_forecast["daily_forecasts"].get(d, []), key=lambda h: h.time)


def _find_consistent_blocks(
    sorted_hours: list[HourlyWeather],
    max_score_variance: float = DEFAULT_MAX_SCORE_VARIANCE,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> list[dict[str, Any]]:
    """Find blocks of hours with consistent scores."""
    blocks = []
    for block in _iter_contiguous_hour_blocks(sorted_hours):
        block_info = _create_consistent_block_info(
            block,
            max_score_variance,
            activity_profile,
        )
        if block_info:
            blocks.append(block_info)
    return blocks


def _iter_contiguous_hour_blocks(
    sorted_hours: list[HourlyWeather],
) -> list[list[HourlyWeather]]:
    """Return every contiguous forecast block."""
    blocks = []
    for start_idx in range(len(sorted_hours)):
        blocks.extend(_blocks_from_start(sorted_hours, start_idx))
    return blocks


def _blocks_from_start(
    sorted_hours: list[HourlyWeather], start_idx: int
) -> list[list[HourlyWeather]]:
    """Return contiguous blocks that begin at a given index."""
    blocks = []
    for end_idx in range(start_idx, len(sorted_hours)):
        if _has_forecast_gap(sorted_hours, start_idx, end_idx):
            break
        blocks.append(sorted_hours[start_idx : end_idx + 1])
    return blocks


def _has_forecast_gap(
    sorted_hours: list[HourlyWeather], start_idx: int, end_idx: int
) -> bool:
    """Return True if extending a block would bridge a forecast gap."""
    return end_idx > start_idx and not _are_adjacent_forecast_hours(
        sorted_hours[end_idx - 1],
        sorted_hours[end_idx],
    )


def _create_consistent_block_info(
    block: list[HourlyWeather],
    max_score_variance: float,
    activity_profile: str,
) -> Optional[dict[str, Any]]:
    """Return block metadata when the block passes consistency rules."""
    scores = [get_activity_score(hour, activity_profile) for hour in block]
    avg_score = sum(scores) / len(scores)
    std_dev = _score_standard_deviation(scores, avg_score)
    if not _is_acceptable_block(block, scores, avg_score, std_dev, max_score_variance):
        return None
    return _build_block_info(block, avg_score, std_dev, activity_profile)


def _score_standard_deviation(scores: list[NumericType], avg_score: float) -> float:
    """Calculate score standard deviation for a block."""
    if len(scores) <= 1:
        return 0
    variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
    return variance**0.5


def _is_acceptable_block(
    block: list[HourlyWeather],
    scores: list[NumericType],
    avg_score: float,
    std_dev: float,
    max_score_variance: float,
) -> bool:
    """Return True when a block passes score, data and variance thresholds."""
    if not all(hour.has_core_readings for hour in block):
        return False
    if avg_score < _minimum_average_score(len(block)):
        return False
    return std_dev <= _adjusted_variance_threshold(len(block), max_score_variance)


def _minimum_average_score(block_length: int) -> int:
    """Return the minimum average score allowed for a block length."""
    if block_length == 1:
        return SINGLE_HOUR_MIN_AVG_SCORE
    return MULTI_HOUR_MIN_AVG_SCORE


def _adjusted_variance_threshold(block_length: int, max_score_variance: float) -> float:
    """Return allowed variance adjusted for block length."""
    extra_hours = block_length - 1
    return max_score_variance + extra_hours * VARIANCE_THRESHOLD_PER_EXTRA_HOUR


def _build_block_info(
    block: list[HourlyWeather],
    avg_score: float,
    std_dev: float,
    activity_profile: str,
) -> dict[str, Any]:
    """Build display and ranking metadata for a consistent block."""
    return {
        **_base_block_info(block, avg_score, std_dev),
        **_weather_block_info(block),
        **_calculate_block_details(block),
        "activity_profile": activity_profile,
    }


def _base_block_info(
    block: list[HourlyWeather], avg_score: float, std_dev: float
) -> dict[str, Any]:
    """Return timing, score, and consistency fields for a block."""
    window_start, _ = daylight_bounds(block[0])
    _, window_end = daylight_bounds(block[-1])
    return {
        "block": block,
        "start": window_start,
        "end": block[-1].time,
        "end_time": window_end,
        "avg_score": avg_score,
        "duration": len(block),
        "duration_hours": _daylight_hours_in(block),
        "coverage_hours": block[0].coverage_hours,
        "consistency": 1 / (1 + std_dev),
        "variance": std_dev,
    }


def _daylight_hours_in(block: list[HourlyWeather]) -> int:
    """Return how many usable daylight hours a block really offers."""
    total = timedelta()
    for hour in block:
        start, end = daylight_bounds(hour)
        total += end - start
    return int(round(total.total_seconds() / 3600))


def _weather_block_info(block: list[HourlyWeather]) -> dict[str, Optional[float]]:
    """Return averaged weather fields for a block."""
    avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages(block)
    return {
        "temp": avg_temp,
        "wind": avg_wind,
        "humidity": avg_humidity,
        "precip": avg_precip,
    }


def _find_optimal_consistent_block(
    sorted_hours: list[HourlyWeather],
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
    min_duration: int = 1,
) -> Optional[dict[str, Any]]:
    """Find the optimal block that balances score, duration, and consistency."""
    consistent_blocks = _find_consistent_blocks(
        sorted_hours,
        max_score_variance=OPTIMAL_MAX_SCORE_VARIANCE,
        activity_profile=activity_profile,
    )
    candidates = _blocks_with_minimum_duration(consistent_blocks, min_duration)
    ranked_blocks = [_rank_block(block, activity_profile) for block in candidates]
    if not ranked_blocks:
        return None
    return max(ranked_blocks, key=lambda block: block["combined_score"])


def _blocks_with_minimum_duration(
    blocks: list[dict[str, Any]], min_duration: int
) -> list[dict[str, Any]]:
    """Return blocks that satisfy the minimum duration."""
    return [block for block in blocks if block["duration"] >= min_duration]


def _rank_block(block_info: dict[str, Any], activity_profile: str) -> dict[str, Any]:
    """Add ranking scores to a candidate block."""
    positive_hour_count = _positive_hour_count(block_info, activity_profile)
    duration_bonus = _duration_bonus(positive_hour_count)
    consistency_bonus = block_info["consistency"] * CONSISTENCY_BONUS_WEIGHT
    weak_hour_penalty = _weak_hour_penalty(block_info, activity_profile)
    combined_score = block_info["avg_score"] + duration_bonus
    combined_score += consistency_bonus - weak_hour_penalty
    return _block_with_rank(
        block_info,
        combined_score,
        duration_bonus,
        consistency_bonus,
        positive_hour_count,
    )


def _block_with_rank(
    block_info: dict[str, Any],
    combined_score: float,
    duration_bonus: float,
    consistency_bonus: float,
    positive_hour_count: int,
) -> dict[str, Any]:
    """Return a block dictionary with ranking metadata."""
    return {
        **block_info,
        "combined_score": combined_score,
        "duration_bonus": duration_bonus,
        "consistency_bonus": consistency_bonus,
        "positive_hour_count": positive_hour_count,
    }


def _duration_bonus(positive_hour_count: int) -> float:
    """Return a diminishing, strictly increasing bonus for usable hours."""
    extra_hours = max(0, positive_hour_count - 1)
    return MAX_DURATION_BONUS * (
        1 - math.exp(-DURATION_BONUS_SATURATION_RATE * extra_hours)
    )


def _positive_hour_count(
    block_info: dict[str, Any], activity_profile: str
) -> int:
    """Return how many hours inside a block score positively."""
    return sum(
        hour.coverage_hours
        for hour in block_info["block"]
        if get_activity_score(hour, activity_profile) > 0
    )


def _weak_hour_penalty(block_info: dict[str, Any], activity_profile: str) -> float:
    """Return the penalty for weak hours inside an otherwise good block."""
    scores = [get_activity_score(hour, activity_profile) for hour in block_info["block"]]
    penalty = (block_info["avg_score"] - min(scores)) * WEAK_HOUR_PENALTY_WEIGHT
    return max(0.0, penalty)


def get_top_locations_for_date(
    all_location_processed: dict[str, dict],
    d: date,
    top_n: int = 10,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> list[dict]:
    """Return the top N locations for a given date."""
    results = []
    for loc_key, processed in all_location_processed.items():
        location_result = _rank_location_for_date(
            loc_key, processed, d, _location_now(processed), activity_profile
        )
        if location_result:
            results.append(location_result)
    # Locations are ranked on the day as a whole, including a penalty for
    # volatile weather: a steady good day is a safer bet than one bright hour
    # in an unsettled one. The window's own score is reported separately.
    results.sort(key=lambda x: (x["score"], x["window_score"]), reverse=True)
    return results[:top_n]


def _location_now(processed: dict) -> datetime:
    """Return the current time in the time zone of a processed forecast."""
    return datetime.now(timezone.utc).astimezone(
        get_timezone(processed.get("timezone"))
    )


def _rank_location_for_date(
    loc_key: str,
    processed: dict,
    forecast_date: date,
    now_local: datetime,
    activity_profile: str,
) -> Optional[dict[str, Any]]:
    """Return a ranked location result for a date, if data is usable."""
    if not processed.get("day_scores", {}).get(forecast_date):
        return None
    filtered_hours = get_recommendation_hours(processed, forecast_date, now_local)
    if not filtered_hours:
        return None
    optimal_block = _find_optimal_consistent_block(filtered_hours, activity_profile)
    if not optimal_block:
        return None

    # Score the day on the same hours the window was drawn from, so a location
    # is never ranked highly on a morning that has already passed.
    report = _daily_report(forecast_date, filtered_hours, _location_name(processed))
    day_score = _calculate_day_activity_score(filtered_hours, activity_profile)
    return _build_location_result(
        loc_key,
        report,
        optimal_block,
        day_score,
        activity_profile,
    )


def _location_name(processed: dict) -> str:
    """Return the location name recorded on a processed forecast."""
    for report in processed.get("day_scores", {}).values():
        return report.location_name
    return ""


def get_recommendation_hours(
    processed: dict,
    forecast_date: date,
    now_local: Optional[datetime] = None,
) -> list[HourlyWeather]:
    """Return the forecast entries a recommendation for a date is based on.

    This is the single definition of "hours that count": daylight entries, and
    for today only those with usable time left. The ranking, the recommended
    window and the hourly breakdown shown to the user all read from here, so
    they can never disagree about which hours were considered.
    """
    daily_forecasts = processed.get("daily_forecasts", {})
    return _filter_hours_for_recommendations(
        sorted(daily_forecasts.get(forecast_date, []), key=lambda hour: hour.time),
        forecast_date,
        now_local if now_local is not None else _location_now(processed),
    )


def _build_location_result(
    loc_key: str,
    report: DailyReport,
    optimal_block: dict[str, Any],
    day_score: dict[str, float],
    activity_profile: str,
) -> dict[str, Any]:
    """Build the ranking result for one location on one date.

    Two different scores matter and they are kept distinct: the day score,
    which ranks locations and accounts for how settled the weather is, and the
    window score, which describes the specific hours being recommended. The
    interface labels both, because a single unlabelled number printed beside a
    time reads as a claim about that time.
    """
    return {
        "location_key": loc_key,
        "location_name": report.location_name,
        "score": day_score["score"],
        "raw_score": day_score["score"],
        "window_score": optimal_block["avg_score"],
        "day_avg_score": day_score["average"],
        "volatility_penalty": day_score["volatility_penalty"],
        "optimal_block": optimal_block,
        "weather_desc": report.weather_description,
        "activity_profile": activity_profile,
    }


def _calculate_day_activity_score(
    hours: list[HourlyWeather], activity_profile: str
) -> dict[str, float]:
    """Score the usable day as a whole and penalize abrupt weather changes."""
    sorted_hours = sorted(hours, key=lambda hour: hour.time)
    scores = [get_activity_score(hour, activity_profile) for hour in sorted_hours]
    average = sum(scores) / len(scores)
    volatility_penalty = _day_score_volatility_penalty(sorted_hours, scores)
    return {
        "score": average - volatility_penalty,
        "average": average,
        "volatility_penalty": volatility_penalty,
    }


def _day_score_volatility_penalty(
    sorted_hours: list[HourlyWeather], scores: list[NumericType]
) -> float:
    """Return an RMS penalty for meaningful adjacent-hour score changes."""
    excess_changes = [
        max(0.0, abs(scores[index] - scores[index - 1]) - DAY_SCORE_CHANGE_TOLERANCE)
        for index in range(1, len(scores))
        if _are_adjacent_forecast_hours(sorted_hours[index - 1], sorted_hours[index])
    ]
    if not excess_changes:
        return 0.0
    root_mean_square = math.sqrt(
        sum(change**2 for change in excess_changes) / len(excess_changes)
    )
    return min(
        root_mean_square * DAY_SCORE_VOLATILITY_WEIGHT,
        MAX_DAY_VOLATILITY_PENALTY,
    )
