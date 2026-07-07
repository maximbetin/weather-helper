"""
Evaluation and scoring logic for weather forecasts.
Provides functions to process forecasts, evaluate time blocks, and rank locations for GUI use.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from src.core.config import (
    DAYLIGHT_END_HOUR,
    DAYLIGHT_START_HOUR,
    FORECAST_DAYS,
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


def _calculate_weather_averages(
    hours: list[HourlyWeather],
) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """Calculate average temperature, wind speed, humidity, and precipitation for a list of hours.

    Args:
        hours: List of HourlyWeather objects

    Returns:
        Tuple of (avg_temp, avg_wind, avg_humidity, avg_precip) or (None, None, None, None)
    """
    temps = [h.temp for h in hours if h.temp is not None]
    winds = [h.wind for h in hours if h.wind is not None]
    humidities = [h.relative_humidity for h in hours if h.relative_humidity is not None]
    precips = [
        h.precipitation_amount for h in hours if h.precipitation_amount is not None
    ]

    return (
        safe_average(temps),
        safe_average(winds),
        safe_average(humidities),
        safe_average(precips),
    )


def _calculate_block_details(hours: list[HourlyWeather]) -> dict[str, Any]:
    """Calculate display and risk details for a weather block."""
    clouds = [h.cloud_coverage for h in hours if h.cloud_coverage is not None]
    precip_probabilities = [
        h.precipitation_probability
        for h in hours
        if h.precipitation_probability is not None
    ]
    symbols = sorted({h.symbol_code for h in hours if h.symbol_code})

    return {
        "cloud": safe_average(clouds),
        "precip_probability": safe_average(precip_probabilities),
        "symbols": symbols,
    }


def _are_adjacent_forecast_hours(
    previous_hour: HourlyWeather,
    next_hour: HourlyWeather,
) -> bool:
    """Return True when two forecast entries represent adjacent hourly data."""
    delta = next_hour.time - previous_hour.time
    return timedelta(minutes=50) <= delta <= timedelta(minutes=70)


def _get_period_data(
    entry: dict[str, Any], period_key: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return summary and detail dictionaries for a forecast period."""
    period = entry["data"].get(period_key, {})
    return period.get("summary", {}), period.get("details", {})


def _is_daylight_hour(hour: HourlyWeather) -> bool:
    """Return True when an hour is inside the configured daytime window."""
    return DAYLIGHT_START_HOUR <= hour.hour <= DAYLIGHT_END_HOUR


def _is_future_or_current_hour(hour: HourlyWeather, now_local: datetime) -> bool:
    """Return True when an hour is still useful for today's recommendations."""
    return (
        hour.time > now_local
        or (hour.time.hour == now_local.hour and now_local.minute < 30)
    )


def _filter_hours_for_recommendations(
    hours: list[HourlyWeather],
    forecast_date: date,
    now_local: datetime,
) -> list[HourlyWeather]:
    """Filter hours to the daytime rows still relevant for a selected date."""
    daylight_hours = [hour for hour in hours if _is_daylight_hour(hour)]
    if forecast_date != now_local.date():
        return daylight_hours

    return [
        hour
        for hour in daylight_hours
        if _is_future_or_current_hour(hour, now_local)
    ]


def find_optimal_weather_block(
    hours: list[HourlyWeather],
    min_duration: int = 1,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> Optional[dict[str, Any]]:
    """Find the optimal weather block for outdoor activities.

    This function identifies the highest scoring continuous block of weather,
    considering both quality and duration.

    Args:
        hours: List of HourlyWeather objects for a given date
        min_duration: Minimum duration in hours for a valid block (default: 1)
        activity_profile: Activity profile used for scoring the block

    Returns:
        A dictionary containing the best weather block, or None.
    """
    if not hours:
        return None

    sorted_hours = sorted(hours, key=lambda x: x.time)

    # Use the more sophisticated consistent block logic
    optimal_block = _find_optimal_consistent_block(
        sorted_hours,
        activity_profile,
        min_duration=min_duration,
    )

    # If no consistent block found or duration is too short, return None
    if not optimal_block or optimal_block["duration"] < min_duration:
        return None

    return optimal_block


def _create_hourly_weather(entry: dict[str, Any]) -> HourlyWeather:
    """Create an HourlyWeather object from a forecast timeseries entry."""
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    time_local = time_utc.astimezone(get_timezone())

    instant_details = entry["data"]["instant"]["details"]
    temp = instant_details.get("air_temperature")
    wind = instant_details.get("wind_speed")
    cloud_coverage = instant_details.get("cloud_area_fraction")
    relative_humidity = instant_details.get("relative_humidity")

    next_1h_summary, next_1h_details = _get_period_data(entry, "next_1_hours")
    precipitation_1h = next_1h_details.get("precipitation_amount")
    precipitation_probability_1h = next_1h_details.get("probability_of_precipitation")

    next_6h_summary, next_6h_details = _get_period_data(entry, "next_6_hours")

    final_precipitation_amount = precipitation_1h
    if final_precipitation_amount is None and next_6h_details:
        final_precipitation_amount = next_6h_details.get("precipitation_amount")

    final_precipitation_probability = precipitation_probability_1h
    if final_precipitation_probability is None and next_6h_details:
        final_precipitation_probability = next_6h_details.get(
            "probability_of_precipitation"
        )

    symbol_code = next_1h_summary.get("symbol_code") or next_6h_summary.get(
        "symbol_code"
    )

    return HourlyWeather(
        time=time_local,
        temp=temp,
        wind=wind,
        cloud_coverage=cloud_coverage,
        precipitation_amount=final_precipitation_amount,
        precipitation_probability=final_precipitation_probability,
        symbol_code=symbol_code,
        relative_humidity=relative_humidity,
        temp_score=temp_score(temp),
        wind_score=wind_score(wind),
        cloud_score=cloud_score(cloud_coverage),
        precip_amount_score=precip_amount_score(final_precipitation_amount),
        humidity_score=humidity_score(relative_humidity),
    )


def _process_timeseries(
    forecast_timeseries: list[dict[str, Any]],
) -> dict[date, list[HourlyWeather]]:
    """Process forecast timeseries data into a dictionary of daily forecasts."""
    daily_forecasts = defaultdict(list)
    today = get_current_date()
    end_date = today + timedelta(days=FORECAST_DAYS)

    for entry in forecast_timeseries:
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        forecast_date = time_utc.astimezone(get_timezone()).date()
        if not (today <= forecast_date < end_date):
            continue

        hourly_weather = _create_hourly_weather(entry)
        daily_forecasts[forecast_date].append(hourly_weather)

    return daily_forecasts


def process_forecast(forecast_data: dict, location_name: str) -> Optional[dict]:
    """Process weather forecast data into daily summaries and hourly blocks."""
    if (
        not forecast_data
        or "properties" not in forecast_data
        or "timeseries" not in forecast_data["properties"]
    ):
        return None

    forecast_timeseries = forecast_data["properties"]["timeseries"]
    daily_forecasts = _process_timeseries(forecast_timeseries)

    day_scores_reports = {}
    for forecast_date, hours_list in daily_forecasts.items():
        daylight_h = [h for h in hours_list if _is_daylight_hour(h)]
        if not daylight_h:
            continue
        day_report = DailyReport(
            datetime.combine(forecast_date, datetime.min.time()),
            daylight_h,
            location_name,
        )
        day_scores_reports[forecast_date] = day_report

    return {"daily_forecasts": daily_forecasts, "day_scores": day_scores_reports}


def get_available_dates(processed_forecast: dict) -> list[date]:
    """Return all available dates for a processed forecast."""
    if not processed_forecast or "daily_forecasts" not in processed_forecast:
        return []
    return sorted(processed_forecast["daily_forecasts"].keys())


def get_time_blocks_for_date(processed_forecast: dict, d: date) -> list[HourlyWeather]:
    """Return all HourlyWeather blocks for a given date."""
    if not processed_forecast or "daily_forecasts" not in processed_forecast:
        return []
    return sorted(
        processed_forecast["daily_forecasts"].get(d, []), key=lambda h: h.time
    )


def _find_consistent_blocks(
    sorted_hours: list[HourlyWeather],
    max_score_variance: float = 7.0,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> list[dict[str, Any]]:
    """Find blocks of hours with consistent scores (without drastic changes).

    Args:
        sorted_hours: List of HourlyWeather objects sorted by time
        max_score_variance: Maximum allowed variance in scores within a block
        activity_profile: Activity profile used for scoring the block

    Returns:
        List of consistent blocks with their stats
    """
    if not sorted_hours:
        return []

    blocks = []

    # Try different starting points and lengths
    for start_idx in range(len(sorted_hours)):
        for end_idx in range(start_idx, len(sorted_hours)):
            if end_idx > start_idx and not _are_adjacent_forecast_hours(
                sorted_hours[end_idx - 1],
                sorted_hours[end_idx],
            ):
                break

            block = sorted_hours[start_idx : end_idx + 1]

            # Calculate score statistics for this block
            scores = [get_activity_score(h, activity_profile) for h in block]
            if len(scores) > 1 and min(scores) < 0:
                continue

            avg_score = sum(scores) / len(scores)

            # Be more lenient with shorter blocks, stricter with longer ones
            min_avg_score = -1 if len(block) == 1 else 0
            if avg_score < min_avg_score:
                continue

            # Calculate variance (how much scores fluctuate)
            if len(scores) > 1:
                variance = sum((score - avg_score) ** 2 for score in scores) / len(
                    scores
                )
                std_dev = variance**0.5
            else:
                std_dev = 0

            # Adjust variance threshold based on block length - longer blocks can have more variance
            adjusted_variance_threshold = max_score_variance + (len(block) - 1) * 0.8

            # Check if block is consistent (low variance)
            if std_dev <= adjusted_variance_threshold:
                # Calculate additional stats for the block
                avg_temp, avg_wind, avg_humidity, avg_precip = (
                    _calculate_weather_averages(block)
                )
                block_details = _calculate_block_details(block)

                blocks.append(
                    {
                        "block": block,
                        "start": block[0].time,
                        "end": block[-1].time,
                        "avg_score": avg_score,
                        "duration": len(block),
                        "consistency": 1 / (1 + std_dev),  # Higher is more consistent
                        "variance": std_dev,
                        "temp": avg_temp,
                        "wind": avg_wind,
                        "humidity": avg_humidity,
                        "precip": avg_precip,
                        **block_details,
                        "activity_profile": activity_profile,
                    }
                )

    return blocks


def _find_optimal_consistent_block(
    sorted_hours: list[HourlyWeather],
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
    min_duration: int = 1,
) -> Optional[dict[str, Any]]:
    """Find the optimal block that balances score, duration, and consistency.

    Args:
        sorted_hours: List of HourlyWeather objects sorted by time
        activity_profile: Activity profile used for scoring the block

    Returns:
        The best block considering score, duration, and consistency
    """
    if not sorted_hours:
        return None

    # Find all consistent blocks with more lenient variance threshold
    # Adjusted for new scoring range that includes humidity (-42 to 23)
    consistent_blocks = _find_consistent_blocks(
        sorted_hours,
        max_score_variance=8.0,
        activity_profile=activity_profile,
    )

    if not consistent_blocks:
        return None

    # Score each block with quality as the dominant factor, then reward useful length.
    best_block = None
    best_combined_score = -float("inf")

    for block_info in consistent_blocks:
        avg_score = block_info["avg_score"]
        duration = block_info["duration"]
        consistency = block_info["consistency"]
        if duration < min_duration:
            continue

        scores = [get_activity_score(h, activity_profile) for h in block_info["block"]]
        min_score = min(scores)
        duration_bonus = min(((duration - 1) * 1.0) + (math.log1p(duration) * 0.8), 4.0)
        consistency_bonus = consistency * 2.0
        weak_hour_penalty = max(0.0, (avg_score - min_score) * 0.2)
        combined_score = (
            avg_score
            + duration_bonus
            + consistency_bonus
            - weak_hour_penalty
        )

        if combined_score > best_combined_score:
            best_combined_score = combined_score
            best_block = {
                **block_info,
                "combined_score": combined_score,
                "duration_bonus": duration_bonus,
                "consistency_bonus": consistency_bonus,
            }

    return best_block


def get_top_locations_for_date(
    all_location_processed: dict[str, dict],
    d: date,
    top_n: int = 10,
    activity_profile: str = DEFAULT_ACTIVITY_PROFILE,
) -> list[dict]:
    """Return the top N locations for a given date, prioritizing consistent score blocks."""
    results = []
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(get_timezone())

    for loc_key, processed in all_location_processed.items():
        day_scores = processed.get("day_scores", {})
        daily_forecasts = processed.get("daily_forecasts", {})
        if d not in day_scores:
            continue

        report = day_scores[d]
        filtered_hours = _filter_hours_for_recommendations(
            daily_forecasts.get(d, []),
            d,
            now_local,
        )
        if not filtered_hours:
            continue

        optimal_block = _find_optimal_consistent_block(
            filtered_hours,
            activity_profile=activity_profile,
        )
        if not optimal_block:
            continue

        location_score = optimal_block["avg_score"]
        duration_bonus = min(math.log1p(optimal_block["duration"]), 2.0)
        final_score = location_score + duration_bonus + optimal_block.get(
            "consistency", 1.0
        )

        results.append(
            {
                "location_key": loc_key,
                "location_name": report.location_name,
                "score": final_score,
                "raw_score": location_score,
                "optimal_block": optimal_block,
                "weather_desc": report.weather_description,
                "activity_profile": activity_profile,
            }
        )

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    return results[:top_n]
