"""
Evaluation and scoring logic for weather forecasts.
Provides functions to process forecasts, evaluate time blocks, and rank locations for GUI use.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional, Union

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
    precips = [h.precipitation_amount for h in hours if h.precipitation_amount is not None]

    return (
        safe_average(temps),
        safe_average(winds),
        safe_average(humidities),
        safe_average(precips)
    )


def _get_value_from_ranges(
    value: Optional[NumericType], ranges: list[tuple], inclusive: bool = False
) -> Optional[Any]:
    """Get a value from a list of ranges."""
    if value is None or not isinstance(value, (int, float)):
        return None

    for range_tuple, result_value in ranges:
        if range_tuple is None:  # Default case
            return result_value
        low, high = range_tuple
        if inclusive:
            if low <= value <= high:
                return result_value
        else:
            if low <= value < high:
                return result_value
    return ranges[-1][1] if ranges and ranges[-1][0] is None else None


def _calculate_score(
    value: Optional[NumericType], ranges: list[tuple], inclusive: bool = False
) -> int:
    """Calculate score based on a value and a list of ranges."""
    return _get_value_from_ranges(value, ranges, inclusive) or 0


def temp_score(temp: Optional[NumericType]) -> int:
    """Rate temperature for outdoor comfort on a scale of -15 to 8.

    Args:
        temp: Temperature in Celsius

    Returns:
        Integer score representing temperature comfort
    """
    temp_ranges = [
        ((20, 24), 7),  # Ideal temperature range
        ((17, 20), 6),  # Cool but very pleasant
        ((24, 27), 6),  # Warm but very pleasant
        ((15, 17), 4),  # Cool but comfortable
        ((27, 30), 4),  # Warm but comfortable
        ((10, 15), 2),  # Cool but acceptable
        ((30, 33), 1),  # Hot but manageable
        ((5, 10), -1),  # Cold
        ((33, 36), -3),  # Very hot
        ((0, 5), -6),  # Very cold
        ((36, 40), -9),  # Extremely hot
        ((-5, 0), -9),  # Extremely cold
        (None, -15),  # Beyond extreme temperatures
    ]
    return _calculate_score(temp, temp_ranges, inclusive=True)


def wind_score(wind_speed: Optional[NumericType]) -> int:
    """Rate wind speed comfort on a scale of -8 to 2.

    Args:
        wind_speed: Wind speed in m/s

    Returns:
        Integer score representing wind comfort
    """
    wind_ranges = [
        ((1, 3), 2),  # Light breeze - ideal for outdoor activities
        ((0, 1), 1),  # Calm - good but can feel stuffy
        ((3, 5), 0),  # Gentle breeze - neutral
        ((5, 8), -2),  # Moderate breeze - noticeable but acceptable
        ((8, 12), -4),  # Fresh breeze - can be challenging
        ((12, 16), -6),  # Strong breeze - difficult for many activities
        ((16, 20), -7),  # Near gale - very challenging
        (None, -8),  # Gale and above - dangerous
    ]
    return _calculate_score(wind_speed, wind_ranges)


def cloud_score(cloud_coverage: Optional[NumericType]) -> int:
    """Rate cloud coverage for outdoor activities on a scale of -3 to 4.

    Args:
        cloud_coverage: Cloud coverage percentage (0-100)

    Returns:
        Integer score representing cloud cover impact
    """
    cloud_ranges = [
        (
            (10, 30),
            4,
        ),  # Few to scattered clouds - ideal (protection from sun, good visibility)
        ((0, 10), 3),  # Clear skies - very good but can be hot
        ((30, 60), 2),  # Partly cloudy - good conditions
        ((60, 80), 0),  # Mostly cloudy - neutral
        ((80, 95), -1),  # Very cloudy - slightly gloomy
        (None, -3),  # Overcast - gloomy
    ]
    return _calculate_score(cloud_coverage, cloud_ranges)


def precip_amount_score(amount: Optional[NumericType]) -> int:
    """Rate precipitation amount on a scale of -15 to 5.

    Args:
        amount: Precipitation amount in millimeters

    Returns:
        Integer score representing precipitation amount impact
    """
    amount_ranges = [
        ((0, 0), 5),  # No precipitation - best
        ((0, 0.1), 4),  # Trace amounts - barely noticeable
        ((0.1, 0.5), 2),  # Very light - minimal impact
        ((0.5, 1.0), 0),  # Light drizzle - manageable
        ((1.0, 2.5), -2),  # Light rain - needs preparation
        ((2.5, 5.0), -4),  # Moderate rain - significant impact
        ((5.0, 10.0), -6),  # Heavy rain - major impact
        ((10.0, 20.0), -8),  # Very heavy rain - severe impact
        (None, -12),  # Extreme precipitation - dangerous
    ]
    return _calculate_score(amount, amount_ranges, inclusive=True)


def humidity_score(relative_humidity: Optional[NumericType]) -> int:
    """Rate relative humidity for outdoor comfort on a scale of -4 to 3.

    Designed for Asturias' humid maritime climate where moderate humidity is common
    and expected, but extreme humidity can significantly impact comfort.

    Args:
        relative_humidity: Relative humidity percentage (0-100)

    Returns:
        Integer score representing humidity comfort
    """
    humidity_ranges = [
        ((40, 60), 3),  # Ideal humidity range - very comfortable
        ((30, 40), 2),  # Low humidity - good but can feel dry
        ((60, 70), 1),  # Moderate humidity - acceptable, typical for Asturias
        ((20, 30), 0),  # Very low humidity - neutral
        ((70, 80), 0),  # High humidity - neutral, common in maritime climates
        ((80, 85), -1),  # Very high humidity - noticeable discomfort
        ((15, 20), -1),  # Very low humidity - can cause dryness
        ((85, 90), -2),  # Extremely high humidity - significant discomfort
        ((10, 15), -2),  # Extremely low humidity - can cause irritation
        ((90, 95), -3),  # Near saturation - very uncomfortable
        ((5, 10), -3),  # Near zero - very uncomfortable
        (None, -4),  # Beyond extreme humidity levels
    ]
    return _calculate_score(relative_humidity, humidity_ranges, inclusive=True)


def get_rating_info(score: Union[int, float, None]) -> str:
    """Return standardized rating description based on score.

    Args:
        score: Numeric score to convert to rating

    Returns:
        Rating text (e.g., 'Excellent', 'Good', etc.)
    """
    if score is None:
        return "N/A"

    rating_ranges = [
        (
            (18.0, float("inf")),
            "Excellent",
        ),  # 78% of max (23 points) - truly exceptional
        ((13.0, 18.0), "Very Good"),  # 57-78% of max - genuinely good
        ((7.0, 13.0), "Good"),  # 30-57% of max - decent conditions
        ((2.0, 7.0), "Fair"),  # 9-30% of max - marginal conditions
        (None, "Poor"),  # Below 2.0 is poor
    ]
    return _get_value_from_ranges(score, rating_ranges, inclusive=False) or "N/A"


def normalize_score(score: Union[int, float, None]) -> int:
    """Normalize a raw score to a 0-100 scale.

    Mapping based on rating thresholds:
    - Raw 23 (Max) -> 100
    - Raw 18 (Excellent start) -> 80
    - Raw 13 (Very Good start) -> 60
    - Raw 7 (Good start) -> 36
    - Raw 2 (Fair start) -> 16
    - Raw < -2 -> 0

    Formula approximation: score * 4 + 8

    Args:
        score: Raw numeric score

    Returns:
        Normalized integer score (0-100)
    """
    if score is None:
        return 0
    
    # Linear approximation: score * 4 + 8
    # 18 * 4 + 8 = 80
    # 23 * 4 + 8 = 100
    normalized = (score * 4) + 8
    
    return max(0, min(100, int(round(normalized))))



def find_optimal_weather_block(
    hours: list[HourlyWeather], min_duration: int = 1
) -> Optional[dict[str, Any]]:
    """Find the optimal weather block for outdoor activities.

    This function identifies the highest scoring continuous block of weather,
    considering both quality and duration.

    Args:
        hours: List of HourlyWeather objects for a given date
        min_duration: Minimum duration in hours for a valid block (default: 1)

    Returns:
        A dictionary containing the best weather block, or None.
    """
    if not hours:
        return None

    sorted_hours = sorted(hours, key=lambda x: x.time)

    # Use the more sophisticated consistent block logic
    optimal_block = _find_optimal_consistent_block(sorted_hours)

    # If no consistent block found or duration is too short, return None
    if not optimal_block or optimal_block["duration"] < min_duration:
        return None

    return optimal_block


def _create_hourly_weather(entry: dict[str, Any]) -> HourlyWeather:
    """Create an HourlyWeather object from a forecast timeseries entry."""
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))

    instant_details = entry["data"]["instant"]["details"]
    temp = instant_details.get("air_temperature")
    wind = instant_details.get("wind_speed")
    cloud_coverage = instant_details.get("cloud_area_fraction")
    relative_humidity = instant_details.get("relative_humidity")

    next_1h = entry["data"].get("next_1_hours", {})
    next_1h_details = next_1h.get("details", {})
    precipitation_1h = next_1h_details.get("precipitation_amount")

    next_6h = entry["data"].get("next_6_hours", {})
    next_6h_details = next_6h.get("details", {})

    final_precipitation_amount = precipitation_1h
    if final_precipitation_amount is None and next_6h_details:
        final_precipitation_amount = next_6h_details.get("precipitation_amount")

    return HourlyWeather(
        time=time_utc,
        temp=temp,
        wind=wind,
        cloud_coverage=cloud_coverage,
        precipitation_amount=final_precipitation_amount,
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
        forecast_date = time_utc.date()
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
        daylight_h = [
            h for h in hours_list if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR
        ]
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
        processed_forecast["daily_forecasts"].get(d, []), key=lambda h: h.hour
    )


def _find_consistent_blocks(
    sorted_hours: list[HourlyWeather], max_score_variance: float = 7.0
) -> list[dict[str, Any]]:
    """Find blocks of hours with consistent scores (without drastic changes).

    Args:
        sorted_hours: List of HourlyWeather objects sorted by time
        max_score_variance: Maximum allowed variance in scores within a block

    Returns:
        List of consistent blocks with their stats
    """
    if not sorted_hours:
        return []

    blocks = []

    # Try different starting points and lengths
    for start_idx in range(len(sorted_hours)):
        for end_idx in range(start_idx, len(sorted_hours)):
            block = sorted_hours[start_idx : end_idx + 1]

            if len(block) < 1:
                continue

            # Calculate score statistics for this block
            scores = [h.total_score for h in block]
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
                avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages(block)

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
                    }
                )

    return blocks


def _find_optimal_consistent_block(
    sorted_hours: list[HourlyWeather],
) -> Optional[dict[str, Any]]:
    """Find the optimal block that balances score, duration, and consistency.

    Args:
        sorted_hours: List of HourlyWeather objects sorted by time

    Returns:
        The best block considering score, duration, and consistency
    """
    if not sorted_hours:
        return None

    # Find all consistent blocks with more lenient variance threshold
    # Adjusted for new scoring range that includes humidity (-42 to 23)
    consistent_blocks = _find_consistent_blocks(sorted_hours, max_score_variance=8.0)

    if not consistent_blocks:
        return None

    # Score each block based on: average_score * duration_factor * consistency_factor
    best_block = None
    best_combined_score = -float("inf")

    for block_info in consistent_blocks:
        avg_score = block_info["avg_score"]
        duration = block_info["duration"]
        consistency = block_info["consistency"]

        # Moderate preference for longer blocks - balance quality and duration
        if duration >= 5:
            duration_factor = (
                2.2 + math.log(duration) / 3.0
            )  # Good preference for 5+ hour blocks
        elif duration == 4:
            duration_factor = 2.0  # Solid preference for 4-hour blocks
        elif duration == 3:
            duration_factor = 1.7  # Good preference for 3-hour blocks
        elif duration == 2:
            duration_factor = 1.4  # Moderate preference for 2-hour blocks
        else:
            duration_factor = 1.0  # Base case for single hours

        duration_factor = min(duration_factor, 2.5)  # Reasonable cap

        # Consistency factor: reward more consistent blocks, but don't penalize too much
        consistency_factor = 0.7 + (consistency * 0.3)  # Scale from 0.7 to 1.0

        # Combined score balances quality and duration more evenly
        combined_score = avg_score * duration_factor * consistency_factor

        # Add a moderate bonus for longer blocks to break ties
        combined_score += (duration - 1) * 0.8  # Reduced from 1.5 to 0.8

        if combined_score > best_combined_score:
            best_combined_score = combined_score
            best_block = {
                **block_info,
                "combined_score": combined_score,
                "duration_factor": duration_factor,
                "consistency_factor": consistency_factor,
            }

    return best_block


def get_top_locations_for_date(
    all_location_processed: dict[str, dict], d: date, top_n: int = 10
) -> list[dict]:
    """Return the top N locations for a given date, prioritizing consistent score blocks."""
    results = []
    # Get current time for filtering
    local_tz = get_timezone()
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(local_tz)

    for loc_key, processed in all_location_processed.items():
        day_scores = processed.get("day_scores", {})
        daily_forecasts = processed.get("daily_forecasts", {})

        if d in day_scores:
            report = day_scores[d]

            # Get hourly data for the day - use same filtering as main table
            hours_for_day = daily_forecasts.get(d, [])

            # Apply consistent time filtering
            if d == now_local.date():
                # Show future hours, plus current hour if we're in the first half of it
                filtered_hours = [
                    h
                    for h in hours_for_day
                    if (
                        DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR
                        and (
                            h.time.astimezone(local_tz) > now_local
                            or (
                                h.time.astimezone(local_tz).hour == now_local.hour
                                and now_local.minute < 30
                            )
                        )
                    )
                ]
            else:
                filtered_hours = [
                    h
                    for h in hours_for_day
                    if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR
                ]

            if not filtered_hours:
                continue

            # Find optimal consistent block
            optimal_block = _find_optimal_consistent_block(filtered_hours)

            # Calculate the location's score based on the optimal block
            if optimal_block:
                # Use the average score of the optimal block
                location_score = optimal_block["avg_score"]
                duration = optimal_block["duration"]
                consistency = optimal_block.get("consistency", 1.0)

                # Apply more moderate duration bonus at the location level
                duration_bonus_multiplier = 1.0
                if duration >= 4:
                    duration_bonus_multiplier = 1.3  # Moderate bonus for 4+ hour blocks
                elif duration == 3:
                    duration_bonus_multiplier = 1.2  # Small bonus for 3-hour blocks
                elif duration == 2:
                    duration_bonus_multiplier = (
                        1.1  # Very small bonus for 2-hour blocks
                    )

                # Apply the duration bonus to the location score for ranking
                final_location_score = location_score * duration_bonus_multiplier

            else:
                # Fallback: use simple average if no consistent block found
                location_score = sum(h.total_score for h in filtered_hours) / len(
                    filtered_hours
                )
                duration = len(filtered_hours)
                consistency = 0.5
                final_location_score = location_score  # No bonus for fallback case

                # Create fallback optimal_block for details
                avg_temp, avg_wind, avg_humidity, avg_precip = _calculate_weather_averages(
                    filtered_hours
                )

                optimal_block = {
                    "block": filtered_hours,
                    "start": filtered_hours[0].time,
                    "end": filtered_hours[-1].time,
                    "avg_score": location_score,
                    "duration": duration,
                    "consistency": consistency,
                    "temp": avg_temp,
                    "wind": avg_wind,
                    "humidity": avg_humidity,
                    "precip": avg_precip,
                }

            results.append(
                {
                    "location_key": loc_key,
                    "location_name": getattr(report, "location_name", loc_key),
                    "avg_score": final_location_score,  # Use the duration-boosted score for ranking
                    "combined_score": final_location_score,  # Same as avg for consistency
                    "min_temp": getattr(report, "min_temp", None),
                    "max_temp": getattr(report, "max_temp", None),
                    "weather_description": getattr(report, "weather_description", ""),
                    "optimal_block": optimal_block,
                    "duration": duration,
                    "consistency": consistency,
                }
            )

    # Sort by the final location score (which includes duration bonuses)
    results.sort(key=lambda x: x["avg_score"], reverse=True)
    return results[:top_n]
