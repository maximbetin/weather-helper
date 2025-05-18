"""Functions for analyzing and processing weather forecast data."""

from datetime import datetime, timedelta
import pytz
from collections import defaultdict

from config import LOCATIONS, TIMEZONE, DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR
from weather_utils import find_weather_blocks

def process_forecast(forecast_data, location_name):
    """Process weather forecast data into daily summaries."""
    if not forecast_data:
        return None

    forecast = forecast_data['properties']['timeseries']

    # Organize forecasts by day and hour
    madrid_tz = pytz.timezone(TIMEZONE)
    daily_forecasts = defaultdict(list)
    today = datetime.now(madrid_tz).date()
    end_date = today + timedelta(days=7)

    from weather_utils import temp_score, wind_score, cloud_score, uv_score, precip_probability_score
    from config import WEATHER_SCORES

    for entry in forecast:
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)
        forecast_date = local_time.date()

        # Only include forecasts for the next 7 days
        if forecast_date >= today and forecast_date < end_date:
            # Extract instant details with proper error handling
            instant_details = entry["data"]["instant"]["details"]
            temp = instant_details.get("air_temperature", "n/a")
            wind = instant_details.get("wind_speed", "n/a")
            humidity = instant_details.get("relative_humidity", "n/a")
            cloud_coverage = instant_details.get("cloud_area_fraction", "n/a")
            fog = instant_details.get("fog_area_fraction", "n/a")
            wind_direction = instant_details.get("wind_from_direction", "n/a")
            wind_gust = instant_details.get("wind_speed_of_gust", "n/a")

            # Get next 1 hour forecast details if available
            next_1h = entry["data"].get("next_1_hours", {})
            next_1h_details = next_1h.get("details", {})
            precipitation_1h = next_1h_details.get("precipitation_amount", "n/a")
            precipitation_prob_1h = next_1h_details.get("probability_of_precipitation", "n/a")

            # Get next 6 hour forecast details if available
            next_6h = entry["data"].get("next_6_hours", {})
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

            daily_forecasts[forecast_date].append({
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
                # Calculate outdoor score for this hour
                "weather_score": WEATHER_SCORES.get(symbol, 0) if symbol != "n/a" else 0,
                "temp_score": temp_score(temp),
                "wind_score": wind_score(wind),
                "cloud_score": cloud_score(cloud_coverage),
                "uv_score": uv_score(uv_index),
                "precip_prob_score": precip_probability_score(precipitation_prob)
            })

    # Calculate daily scores for outdoor activities
    day_scores = {}
    for date, hours in daily_forecasts.items():
        # Focus on daylight hours
        daylight_hours = [h for h in hours if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR]

        if not daylight_hours:
            continue

        # Calculate total scores
        total_weather_score = sum(h["weather_score"] for h in daylight_hours)
        total_temp_score = sum(h["temp_score"] for h in daylight_hours)
        total_wind_score = sum(h["wind_score"] for h in daylight_hours)
        total_cloud_score = sum(h["cloud_score"] for h in daylight_hours if isinstance(h["cloud_score"], (int, float)))
        total_uv_score = sum(h["uv_score"] for h in daylight_hours if isinstance(h["uv_score"], (int, float)))
        total_precip_prob_score = sum(h["precip_prob_score"] for h in daylight_hours if isinstance(h["precip_prob_score"], (int, float)))

        # Count sunny/fair hours
        sunny_hours = sum(1 for h in daylight_hours if h["symbol"] in ["clearsky", "fair"])
        partly_cloudy_hours = sum(1 for h in daylight_hours if h["symbol"] == "partlycloudy")
        rainy_hours = sum(1 for h in daylight_hours if "rain" in h["symbol"] or "shower" in h["symbol"])

        # Get precipitation hours with probability > 30%
        likely_rain_hours = sum(1 for h in daylight_hours if isinstance(h["precipitation_probability"], (int, float)) and h["precipitation_probability"] > 30)

        # Average precipitation probability
        precip_probs = [h["precipitation_probability"] for h in daylight_hours if isinstance(h["precipitation_probability"], (int, float))]
        avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else None

        # Calculate average scores
        num_hours = len(daylight_hours)
        total_available_factors = 3  # Weather, temp and wind always available

        if any(isinstance(h["cloud_score"], (int, float)) for h in daylight_hours):
            total_available_factors += 1
        if any(isinstance(h["uv_score"], (int, float)) for h in daylight_hours):
            total_available_factors += 1
        if any(isinstance(h["precip_prob_score"], (int, float)) for h in daylight_hours):
            total_available_factors += 1

        # Get min/max temps
        temps = [h["temp"] for h in daylight_hours if isinstance(h["temp"], (int, float))]
        min_temp = min(temps) if temps else None
        max_temp = max(temps) if temps else None
        avg_temp = sum(temps) / len(temps) if temps else None

        # Calculate average for all available scores
        total_score = (total_weather_score + total_temp_score + total_wind_score +
                      total_cloud_score + total_uv_score + total_precip_prob_score)

        avg_score = total_score / (num_hours * total_available_factors) if num_hours > 0 and total_available_factors > 0 else 0

        day_scores[date] = {
            "avg_score": avg_score,
            "sunny_hours": sunny_hours,
            "partly_cloudy_hours": partly_cloudy_hours,
            "rainy_hours": rainy_hours,
            "likely_rain_hours": likely_rain_hours,
            "avg_precip_prob": avg_precip_prob,
            "total_score": total_score,
            "day_name": date.strftime("%A"),
            "daylight_hours": daylight_hours,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "avg_temp": avg_temp,
            "location": location_name
        }

    return {
        "daily_forecasts": daily_forecasts,
        "day_scores": day_scores
    }

def extract_best_blocks(forecast_data, location_name):
    """Extract best time blocks from forecast data for a specific location."""
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
        daylight_hours = sorted([h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
                              key=lambda x: x["hour"])

        # Score each hour for outdoor activity
        for hour in daylight_hours:
            hour["total_score"] = sum(score for score_name, score in hour.items()
                                  if score_name.endswith("_score") and isinstance(score, (int, float)))

        # Find consecutive hours with similar weather
        weather_blocks = find_weather_blocks(daylight_hours)

        # Find the best block
        best_block = None
        best_score = float('-inf')

        # Identify best block for this day
        for block, weather_type in weather_blocks:
            if len(block) < 2:  # Skip single hour blocks
                continue

            avg_block_score = sum(h["total_score"] for h in block) / len(block)

            # Identify best block
            if avg_block_score > best_score:
                best_score = avg_block_score
                best_block = (block, weather_type)

        # Add the best block to our extracted blocks
        if best_block:
            block, weather_type = best_block
            start_time = block[0]["time"]
            end_time = block[-1]["time"]

            # Get the average temperature during this period
            temps = [h["temp"] for h in block if isinstance(h["temp"], (int, float))]
            avg_temp = sum(temps) / len(temps) if temps else None

            # Get the dominant weather symbol
            symbols = [h["symbol"] for h in block if isinstance(h["symbol"], str)]
            symbol_counts = {}
            for symbol in symbols:
                if symbol in symbol_counts:
                    symbol_counts[symbol] += 1
                else:
                    symbol_counts[symbol] = 1

            # Find the symbol that appears most frequently
            dominant_symbol = ""
            max_count = 0
            for symbol, count in symbol_counts.items():
                if count > max_count:
                    dominant_symbol = symbol
                    max_count = count

            # Create a record for this period
            period = {
                "location": location_name,
                "date": date,
                "day_name": date.strftime("%A"),
                "start_time": start_time,
                "end_time": end_time,
                "duration": len(block),
                "score": avg_block_score,
                "weather_type": weather_type,
                "avg_temp": avg_temp,
                "dominant_symbol": dominant_symbol
            }
            extracted_blocks.append(period)

    return extracted_blocks

def recommend_best_times(location_data):
    """Analyze forecast data and recommend the best times to go out this week."""
    madrid_tz = pytz.timezone(TIMEZONE)
    today = datetime.now(madrid_tz).date()
    end_date = today + timedelta(days=7)

    # Store all acceptable periods
    all_periods = []

    # First, extract best blocks for each location
    for location_name, forecast in location_data.items():
        if not forecast:
            continue

        location_display_name = LOCATIONS[location_name]["name"]

        # Use the same approach as display_forecast to get best blocks
        best_blocks = extract_best_blocks(forecast, location_display_name)
        all_periods.extend(best_blocks)

    # If no periods found, use the more general approach
    if not all_periods:
        # Store the best outdoor periods for the week, organized by day
        day_periods = defaultdict(list)

        # Process each location
        for location_name, forecast in location_data.items():
            if not forecast or not forecast.get("day_scores"):
                continue

            location_display_name = LOCATIONS[location_name]["name"]

            # Process each day in the forecast
            for date, scores in sorted(forecast["day_scores"].items()):
                if date < today or date >= end_date:
                    continue

                # Extremely lenient threshold
                if scores["avg_score"] < -15:
                    continue

                # Get the daily forecast data
                daily_hours = forecast["daily_forecasts"].get(date, [])
                daylight_hours = sorted([h for h in daily_hours if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
                                      key=lambda x: x["hour"])

                # Calculate scores for each hour
                for hour in daylight_hours:
                    hour["total_score"] = sum(score for score_name, score in hour.items()
                                         if score_name.endswith("_score") and isinstance(score, (int, float)))

                # Find blocks of weather
                weather_blocks = find_weather_blocks(daylight_hours)

                # Identify blocks of at least 2 hours
                for block, weather_type in weather_blocks:
                    if len(block) < 2:  # Skip single hour blocks
                        continue

                    avg_block_score = sum(h["total_score"] for h in block) / len(block)

                    # Very low threshold for all locations
                    block_threshold = -10

                    # Only exclude severe weather
                    extremely_bad_weather = ["heavyrain", "heavyrainshowers", "thunderstorm"]
                    if (avg_block_score >= block_threshold and
                      not any(bad in block[0]["symbol"] for bad in extremely_bad_weather if isinstance(block[0]["symbol"], str))):
                        start_time = block[0]["time"]
                        end_time = block[-1]["time"]

                        # Get the average temperature during this period
                        temps = [h["temp"] for h in block if isinstance(h["temp"], (int, float))]
                        avg_temp = sum(temps) / len(temps) if temps else None

                        # Get the dominant weather symbol
                        symbols = [h["symbol"] for h in block if isinstance(h["symbol"], str)]
                        symbol_counts = {}
                        for symbol in symbols:
                            if symbol in symbol_counts:
                                symbol_counts[symbol] += 1
                            else:
                                symbol_counts[symbol] = 1

                        # Find the symbol that appears most frequently
                        dominant_symbol = ""
                        max_count = 0
                        for symbol, count in symbol_counts.items():
                            if count > max_count:
                                dominant_symbol = symbol
                                max_count = count

                        # Create a record for this period
                        period = {
                            "location": location_display_name,
                            "date": date,
                            "day_name": date.strftime("%A"),
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": len(block),
                            "score": avg_block_score,
                            "weather_type": weather_type,
                            "avg_temp": avg_temp,
                            "dominant_symbol": dominant_symbol
                        }
                        # Store by day
                        day_periods[date].append(period)

        # Collect top periods for each day
        for date in sorted(day_periods.keys()):
            # Sort by score (best first)
            day_periods[date].sort(key=lambda x: x["score"], reverse=True)

            # Take up to 3 best periods per day
            num_to_take = min(3, len(day_periods[date]))
            for i in range(num_to_take):
                all_periods.append(day_periods[date][i])

    # Sort all periods by date and then by score
    all_periods.sort(key=lambda x: (x["date"], -x["score"]))

    return all_periods