"""Functions for analyzing and processing weather forecast data."""

from datetime import datetime, timedelta
import pytz
from collections import defaultdict

from config import LOCATIONS, TIMEZONE, DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR, FORECAST_DAYS, WEATHER_SCORES
from weather_utils import (
    find_weather_blocks, temp_score, wind_score, cloud_score,
    uv_score, precip_probability_score
)


def process_forecast(forecast_data, location_name):
    """Process weather forecast data into daily summaries.

    Args:
        forecast_data: Raw JSON data from the weather API
        location_name: Name of the location being processed

    Returns:
        dict: Processed forecast with daily_forecasts and day_scores
    """
    if not forecast_data:
        return None

    # Extract forecast timeseries
    forecast = forecast_data['properties']['timeseries']

    # Organize forecasts by day and hour
    madrid_tz = pytz.timezone(TIMEZONE)
    daily_forecasts = defaultdict(list)
    today = datetime.now(madrid_tz).date()
    end_date = today + timedelta(days=FORECAST_DAYS)

    # Process each forecast entry
    for entry in forecast:
        # Convert time to local timezone
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)
        forecast_date = local_time.date()

        # Only include forecasts for the specified forecast period
        if forecast_date >= today and forecast_date < end_date:
            hour_data = extract_hour_data(entry, local_time)
            daily_forecasts[forecast_date].append(hour_data)

    # Calculate daily scores for outdoor activities
    day_scores = calculate_day_scores(daily_forecasts, location_name)

    return {
        "daily_forecasts": daily_forecasts,
        "day_scores": day_scores
    }


def extract_hour_data(entry, local_time):
    """Extract and process data for a single hour from a forecast entry.

    Args:
        entry: Single forecast entry from API
        local_time: Datetime object in local timezone

    Returns:
        dict: Processed data for this hour
    """
    # Extract instant details with proper error handling
    instant_details = entry["data"]["instant"]["details"]
    temp = instant_details.get("air_temperature", "n/a")
    wind = instant_details.get("wind_speed", "n/a")
    humidity = instant_details.get("relative_humidity", "n/a")
    cloud_coverage = instant_details.get("cloud_area_fraction", "n/a")
    fog = instant_details.get("fog_area_fraction", "n/a")
    wind_direction = instant_details.get("wind_from_direction", "n/a")
    wind_gust = instant_details.get("wind_speed_of_gust", "n/a")

    # Get precipitation and symbol data
    precipitation_data = get_precipitation_data(entry["data"])
    precipitation_1h = precipitation_data["precipitation_1h"]
    precipitation_6h = precipitation_data["precipitation_6h"]
    precipitation_prob = precipitation_data["precipitation_prob"]
    uv_index = precipitation_data["uv_index"]
    symbol = precipitation_data["symbol"]

    # Calculate scores for this hour
    weather_score = WEATHER_SCORES.get(symbol, 0) if symbol != "n/a" else 0

    return {
        "hour": local_time.hour,
        "time": local_time,
        "temp": temp,
        "wind": wind,
        "humidity": humidity,
        "cloud_coverage": cloud_coverage,
        "fog": fog,
        "wind_direction": wind_direction,
        "wind_gust": wind_gust,
        "precipitation_amount": precipitation_1h if precipitation_1h != "n/a" else precipitation_6h,
        "precipitation_probability": precipitation_prob,
        "uv_index": uv_index,
        "symbol": symbol,
        # Calculate individual scores for this hour
        "weather_score": weather_score,
        "temp_score": temp_score(temp),
        "wind_score": wind_score(wind),
        "cloud_score": cloud_score(cloud_coverage),
        "uv_score": uv_score(uv_index),
        "precip_prob_score": precip_probability_score(precipitation_prob)
    }


def get_precipitation_data(data):
    """Extract precipitation data from forecast data.

    Args:
        data: Data section from forecast entry

    Returns:
        dict: Dictionary with precipitation and UV data
    """
    # Get next 1 hour forecast details if available
    next_1h = data.get("next_1_hours", {})
    next_1h_details = next_1h.get("details", {})
    precipitation_1h = next_1h_details.get("precipitation_amount", "n/a")
    precipitation_prob_1h = next_1h_details.get("probability_of_precipitation", "n/a")

    # Get next 6 hour forecast details if available
    next_6h = data.get("next_6_hours", {})
    next_6h_details = next_6h.get("details", {})
    precipitation_6h = next_6h_details.get("precipitation_amount", "n/a")
    precipitation_prob_6h = next_6h_details.get("probability_of_precipitation", "n/a")
    uv_index = next_6h_details.get("ultraviolet_index_clear_sky_max", "n/a")

    # Use 1h precipitation probability if available, otherwise use 6h
    precipitation_prob = precipitation_prob_1h if precipitation_prob_1h != "n/a" else precipitation_prob_6h

    # Get weather symbol with fallbacks
    symbol = next_1h.get("summary", {}).get("symbol_code",
             next_6h.get("summary", {}).get("symbol_code", "n/a"))

    # Clean up the symbol code by removing day/night suffix if present
    if symbol != "n/a" and "_" in symbol:
        symbol = symbol.split("_")[0]

    return {
        "precipitation_1h": precipitation_1h,
        "precipitation_6h": precipitation_6h,
        "precipitation_prob": precipitation_prob,
        "uv_index": uv_index,
        "symbol": symbol
    }


def calculate_day_scores(daily_forecasts, location_name):
    """Calculate scores for each day based on hourly forecasts.

    Args:
        daily_forecasts: Dictionary of hourly forecasts grouped by day
        location_name: Name of the location

    Returns:
        dict: Day scores indexed by date
    """
    day_scores = {}

    for date, hours in daily_forecasts.items():
        # Focus on daylight hours
        daylight_hours = [h for h in hours if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR]

        if not daylight_hours:
            continue

        # Calculate metric counts and scores
        metrics = calculate_day_metrics(daylight_hours)

        # Store day scores
        day_scores[date] = {
            "avg_score": metrics["avg_score"],
            "sunny_hours": metrics["sunny_hours"],
            "partly_cloudy_hours": metrics["partly_cloudy_hours"],
            "rainy_hours": metrics["rainy_hours"],
            "likely_rain_hours": metrics["likely_rain_hours"],
            "avg_precip_prob": metrics["avg_precip_prob"],
            "total_score": metrics["total_score"],
            "day_name": date.strftime("%A"),
            "daylight_hours": daylight_hours,
            "min_temp": metrics["min_temp"],
            "max_temp": metrics["max_temp"],
            "avg_temp": metrics["avg_temp"],
            "location": location_name
        }

    return day_scores


def calculate_day_metrics(daylight_hours):
    """Calculate various weather metrics based on hourly forecasts.

    Args:
        daylight_hours: List of hourly forecasts during daylight hours

    Returns:
        dict: Dictionary of calculated metrics
    """
    # Calculate total scores for each factor
    total_scores = {
        "weather_score": sum(h["weather_score"] for h in daylight_hours),
        "temp_score": sum(h["temp_score"] for h in daylight_hours),
        "wind_score": sum(h["wind_score"] for h in daylight_hours),
        "cloud_score": sum(h["cloud_score"] for h in daylight_hours if isinstance(h["cloud_score"], (int, float))),
        "uv_score": sum(h["uv_score"] for h in daylight_hours if isinstance(h["uv_score"], (int, float))),
        "precip_prob_score": sum(h["precip_prob_score"] for h in daylight_hours if isinstance(h["precip_prob_score"], (int, float)))
    }

    # Count hours by weather type
    sunny_hours = sum(1 for h in daylight_hours if h["symbol"] in ["clearsky", "fair"])
    partly_cloudy_hours = sum(1 for h in daylight_hours if h["symbol"] == "partlycloudy")
    rainy_hours = sum(1 for h in daylight_hours if "rain" in h["symbol"] or "shower" in h["symbol"])

    # Get precipitation hours with probability > 30%
    likely_rain_hours = sum(1 for h in daylight_hours
                           if isinstance(h["precipitation_probability"], (int, float))
                           and h["precipitation_probability"] > 30)

    # Calculate average precipitation probability
    precip_probs = [h["precipitation_probability"] for h in daylight_hours
                   if isinstance(h["precipitation_probability"], (int, float))]
    avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else None

    # Count available factors for scoring
    num_hours = len(daylight_hours)
    available_factors = 3  # Weather, temp and wind always available

    if any(isinstance(h["cloud_score"], (int, float)) for h in daylight_hours):
        available_factors += 1
    if any(isinstance(h["uv_score"], (int, float)) for h in daylight_hours):
        available_factors += 1
    if any(isinstance(h["precip_prob_score"], (int, float)) for h in daylight_hours):
        available_factors += 1

    # Get min/max temps
    temps = [h["temp"] for h in daylight_hours if isinstance(h["temp"], (int, float))]
    min_temp = min(temps) if temps else None
    max_temp = max(temps) if temps else None
    avg_temp = sum(temps) / len(temps) if temps else None

    # Calculate total and average scores
    total_score = sum(total_scores.values())
    avg_score = total_score / (num_hours * available_factors) if num_hours > 0 and available_factors > 0 else 0

    return {
        "total_scores": total_scores,
        "sunny_hours": sunny_hours,
        "partly_cloudy_hours": partly_cloudy_hours,
        "rainy_hours": rainy_hours,
        "likely_rain_hours": likely_rain_hours,
        "avg_precip_prob": avg_precip_prob,
        "min_temp": min_temp,
        "max_temp": max_temp,
        "avg_temp": avg_temp,
        "total_score": total_score,
        "avg_score": avg_score
    }


def extract_best_blocks(forecast_data, location_name):
    """Extract best time blocks from forecast data for a specific location.

    Args:
        forecast_data: Processed forecast data
        location_name: Name of the location

    Returns:
        list: Best time blocks for outdoor activities
    """
    if not forecast_data:
        return []

    extracted_blocks = []
    daily_forecasts = forecast_data["daily_forecasts"]
    day_scores = forecast_data["day_scores"]

    # Get all days with reasonable scores
    for date, scores in day_scores.items():
        # Skip days with very poor scores
        if scores["avg_score"] < -8:
            continue

        # Get daylight hours and calculate scores
        daylight_hours = sorted(
            [h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
            key=lambda x: x["hour"]
        )

        # Score each hour for outdoor activity
        for hour in daylight_hours:
            hour["total_score"] = sum(
                score for score_name, score in hour.items()
                if score_name.endswith("_score") and isinstance(score, (int, float))
            )

        # Find consecutive hours with similar weather
        weather_blocks = find_weather_blocks(daylight_hours)

        # Find the best block for this day
        best_block = find_best_block(weather_blocks)

        # If a good block was found, add it to the results
        if best_block and best_block[0] >= 0:
            avg_score, block, weather_type = best_block
            if len(block) >= 2:  # Only include blocks of at least 2 hours
                extracted_blocks.append({
                    "date": date,
                    "location": location_name,
                    "hours": block,
                    "weather_type": weather_type,
                    "avg_score": avg_score,
                    "day_name": date.strftime("%A")
                })

    # Sort blocks by score (best first)
    extracted_blocks.sort(key=lambda x: x["avg_score"], reverse=True)
    return extracted_blocks


def find_best_block(weather_blocks):
    """Find the best time block from a list of weather blocks.

    Args:
        weather_blocks: List of (block, weather_type) tuples

    Returns:
        tuple: (avg_score, block, weather_type) of the best block, or None if no good blocks
    """
    best_block = None
    best_score = float('-inf')

    # Identify best block based on average score
    for block, weather_type in weather_blocks:
        if len(block) < 2:  # Skip single hour blocks
            continue

        avg_block_score = sum(h["total_score"] for h in block) / len(block)

        # Find best block that's at least neutral or sunny/cloudy
        if avg_block_score > best_score and (weather_type in ["sunny", "cloudy"] or avg_block_score >= 0):
            best_score = avg_block_score
            best_block = (avg_block_score, block, weather_type)

    return best_block


def recommend_best_times(location_data):
    """Find and recommend the best times for outdoor activities across all locations.

    Args:
        location_data: Dictionary of processed forecasts by location

    Returns:
        list: Sorted list of recommended time periods for outdoor activities
    """
    all_periods = []

    # Extract best blocks from each location
    for location_name, forecast_data in location_data.items():
        location_blocks = extract_best_blocks(forecast_data, LOCATIONS[location_name]["name"])
        all_periods.extend(location_blocks)

    # Sort by score (best first)
    all_periods.sort(key=lambda x: x["avg_score"], reverse=True)

    return all_periods