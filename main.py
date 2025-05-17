import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import argparse
import time
from colorama import init, Fore, Style

# Initialize colorama
init()

# Define locations in Asturias
LOCATIONS = {
    "gijon": {"name": "Gijón", "lat": 43.5322, "lon": -5.6611},
    "llanes": {"name": "Llanes", "lat": 43.4200, "lon": -4.7550},
    "ribadesella": {"name": "Ribadesella", "lat": 43.4675, "lon": -5.0553},
    "tapia": {"name": "Tapia de Casariego", "lat": 43.5700, "lon": -6.9436},
    "aviles": {"name": "Avilés", "lat": 43.5547, "lon": -5.9248},
    "cangas_de_onis": {"name": "Cangas de Onís", "lat": 43.3507, "lon": -5.1356},
    "lagos_covadonga": {"name": "Lagos de Covadonga", "lat": 43.2728, "lon": -4.9906},
    "somiedo": {"name": "Somiedo", "lat": 43.0981, "lon": -6.2550},
    "teverga": {"name": "Teverga", "lat": 43.1578, "lon": -6.0867},
    "taramundi": {"name": "Taramundi", "lat": 43.3583, "lon": -7.1083},
    "oviedo": {"name": "Oviedo", "lat": 43.3619, "lon": -5.8494}
}

# Weather rating system - positive scores for good outdoor conditions
weather_scores = {
    # Sunny/clear conditions (highest scores)
    "clearsky": 10,
    "fair": 8,

    # Partly cloudy conditions (medium scores)
    "partlycloudy": 6,

    # Cloudy but no precipitation (lower scores)
    "cloudy": 3,

    # Light precipitation (negative scores)
    "lightrain": -2,
    "lightrainshowers": -2,
    "lightsleet": -3,
    "lightsleetshowers": -3,
    "lightsnow": -3,
    "lightsnowshowers": -3,

    # Moderate precipitation (more negative)
    "rain": -5,
    "rainshowers": -5,
    "sleet": -6,
    "sleetshowers": -6,
    "snow": -6,
    "snowshowers": -6,

    # Heavy precipitation (most negative)
    "heavyrain": -10,
    "heavyrainshowers": -10,
    "heavysleet": -10,
    "heavysleetshowers": -10,
    "heavysnow": -10,
    "heavysnowshowers": -10,

    # Fog/poor visibility
    "fog": -4,

    # Thunderstorms (most negative)
    "thunderstorm": -15
}

# Temperature score factors
def temp_score(temp):
    """Rate temperature for outdoor comfort on a scale of -10 to 10"""
    if temp is None or not isinstance(temp, (int, float)):
        return 0

    # Optimal temperature range around 18-24°C
    if 18 <= temp <= 24:
        return 10
    elif 15 <= temp < 18 or 24 < temp <= 28:
        return 8
    elif 10 <= temp < 15 or 28 < temp <= 32:
        return 5
    elif 5 <= temp < 10 or 32 < temp <= 35:
        return 0
    elif 0 <= temp < 5 or 35 < temp <= 38:
        return -5
    else:
        return -10  # Too cold (< 0°C) or too hot (> 38°C)

# Wind speed factor
def wind_score(wind_speed):
    """Rate wind speed comfort on a scale of -10 to 0"""
    if wind_speed is None or not isinstance(wind_speed, (int, float)):
        return 0

    if wind_speed < 2:
        return 0
    elif 2 <= wind_speed < 4:
        return -2
    elif 4 <= wind_speed < 6:
        return -4
    elif 6 <= wind_speed < 10:
        return -6
    else:
        return -10  # Very windy, not pleasant for outdoor activities

# Cloud coverage factor
def cloud_score(cloud_coverage):
    """Rate cloud coverage for outdoor activities on a scale of -5 to 5"""
    if cloud_coverage is None or not isinstance(cloud_coverage, (int, float)):
        return 0

    # Lower cloud coverage is better for most outdoor activities
    if cloud_coverage < 20:
        return 5  # Nearly clear skies
    elif cloud_coverage < 40:
        return 3  # Mostly clear
    elif cloud_coverage < 60:
        return 1  # Partly cloudy
    elif cloud_coverage < 80:
        return -2  # Mostly cloudy
    else:
        return -5  # Overcast

# UV index factor
def uv_score(uv_index):
    """Rate UV index for comfort/safety on a scale of -5 to 5"""
    if uv_index is None or not isinstance(uv_index, (int, float)):
        return 0

    # Moderate UV (3-5) is generally pleasant without excessive sun exposure risk
    if 2 <= uv_index <= 5:
        return 5  # Ideal for outdoor activities
    elif uv_index <= 2:
        return 3  # Low UV, safe but less warmth/light
    elif 5 < uv_index <= 7:
        return 0  # Higher UV, need sun protection
    elif 7 < uv_index <= 10:
        return -3  # Very high, risk of sunburn
    else:
        return -5  # Extreme, avoid midday sun

# Precipitation probability factor
def precip_probability_score(probability):
    """Rate precipitation probability on a scale of -10 to 0"""
    if probability is None or not isinstance(probability, (int, float)):
        return 0

    # Lower probability is better for outdoor activities
    if probability < 10:
        return 0  # Very unlikely to rain
    elif probability < 30:
        return -2  # Slight chance of rain
    elif probability < 50:
        return -5  # Moderate chance of rain
    elif probability < 70:
        return -7  # High chance of rain
    else:
        return -10  # Very likely to rain

# Function to find weather blocks with similar conditions
def find_weather_blocks(hours):
    """Find blocks of hours with similar weather conditions"""
    if not hours:
        return []

    # Sort hours by time
    sorted_hours = sorted(hours, key=lambda x: x["hour"])

    blocks = []
    current_block = [sorted_hours[0]]
    current_type = "sunny" if sorted_hours[0]["symbol"] in ["clearsky", "fair"] else "rainy" if "rain" in sorted_hours[0]["symbol"] else "cloudy"

    for hour in sorted_hours[1:]:
        hour_type = "sunny" if hour["symbol"] in ["clearsky", "fair"] else "rainy" if "rain" in hour["symbol"] else "cloudy"

        # If same type, extend the current block
        if hour_type == current_type and hour["hour"] == current_block[-1]["hour"] + 1:
            current_block.append(hour)
        else:
            # Save the completed block and start a new one
            blocks.append((current_block, current_type))
            current_block = [hour]
            current_type = hour_type

    # Add the last block
    blocks.append((current_block, current_type))

    return blocks

def fetch_weather_data(location):
    """Fetch weather data for a specific location"""
    lat = location["lat"]
    lon = location["lon"]

    # Request headers - required by Met.no API
    headers = {
        "User-Agent": "DailyHelper/1.0"
    }

    # API URL
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}"

    # Fetch data with error handling
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error fetching weather data for {location['name']}: {e}{Style.RESET_ALL}")
        return None
    except ValueError as e:
        print(f"{Fore.RED}Error parsing JSON response for {location['name']}: {e}{Style.RESET_ALL}")
        return None

def process_forecast(forecast_data, location_name):
    """Process weather forecast data into daily summaries"""
    if not forecast_data:
        return None

    forecast = forecast_data['properties']['timeseries']

    # Organize forecasts by day and hour
    madrid_tz = pytz.timezone("Europe/Madrid")
    daily_forecasts = defaultdict(list)
    today = datetime.now(madrid_tz).date()
    end_date = today + timedelta(days=7)

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
                "weather_score": weather_scores.get(symbol, 0) if symbol != "n/a" else 0,
                "temp_score": temp_score(temp),
                "wind_score": wind_score(wind),
                "cloud_score": cloud_score(cloud_coverage),
                "uv_score": uv_score(uv_index),
                "precip_prob_score": precip_probability_score(precipitation_prob)
            })

    # Calculate daily scores for outdoor activities
    day_scores = {}
    for date, hours in daily_forecasts.items():
        # Focus on daylight hours (typically 8:00-20:00)
        daylight_hours = [h for h in hours if 8 <= h["hour"] <= 20]

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

# Create a standardized weather description function to ensure consistency across all display modes
def get_standardized_weather_desc(symbol):
    """Return standardized weather description from symbol code"""
    if not symbol or not isinstance(symbol, str):
        return "Unknown"

    if symbol == "clearsky":
        return "Sunny"
    elif symbol == "fair":
        return "Mostly Sunny"
    elif symbol == "partlycloudy":
        return "P.Cloudy"
    elif symbol == "cloudy":
        return "Cloudy"
    elif "lightrain" in symbol:
        return "Light Rain"
    elif "heavyrain" in symbol:
        return "Heavy Rain"
    elif "rain" in symbol:
        return "Rain"
    elif "lightsnow" in symbol:
        return "Light Snow"
    elif "snow" in symbol:
        return "Snow"
    elif "fog" in symbol:
        return "Foggy"
    elif "thunder" in symbol:
        return "Thunderstorm"
    else:
        # Fallback: Capitalize and replace underscores
        return symbol.replace("_", " ").capitalize()

def display_forecast(forecast_data, location_name, compare_mode=False):
    """Display weather forecast for a location"""
    if not forecast_data:
        return

    daily_forecasts = forecast_data["daily_forecasts"]
    day_scores = forecast_data["day_scores"]

    # Consistently color location names
    print(f"\n{Fore.CYAN}{location_name}{Style.RESET_ALL}")

    # Sort days chronologically
    for date in sorted(daily_forecasts.keys()):
        if date not in day_scores:
            continue

        scores = day_scores[date]
        date_str = date.strftime("%a, %d %b")

        # Determine rating description and color
        if scores["avg_score"] >= 6:
            rating = "Excellent"
            color = Fore.LIGHTGREEN_EX
        elif scores["avg_score"] >= 3:
            rating = "Good"
            color = Fore.GREEN
        elif scores["avg_score"] >= 0:
            rating = "Fair"
            color = Fore.YELLOW
        elif scores["avg_score"] >= -3:
            rating = "Poor"
            color = Fore.LIGHTRED_EX
        else:
            rating = "Avoid"
            color = Fore.RED

        # Determine overall weather description - standardized naming
        precip_warning = ""
        if scores["avg_precip_prob"] is not None and scores["avg_precip_prob"] > 40:
            precip_warning = f" - {scores['avg_precip_prob']:.0f}% rain"

        if scores["sunny_hours"] > scores["partly_cloudy_hours"] and scores["sunny_hours"] > scores["rainy_hours"]:
            weather_desc = "Sunny" + precip_warning
        elif scores["partly_cloudy_hours"] > scores["sunny_hours"] and scores["partly_cloudy_hours"] > scores["rainy_hours"]:
            weather_desc = "P.Cloudy" + precip_warning
        elif scores["rainy_hours"] > 0:
            weather_desc = f"Rain ({scores['rainy_hours']}h)"
        else:
            weather_desc = "Mixed" + precip_warning

        # Use min-max temperature range
        temp_str = ""
        if scores["min_temp"] is not None and scores["max_temp"] is not None:
          temp_str = f"{scores['min_temp']:>4.1f}°C - {scores['max_temp']:>4.1f}°C"
        else:
          temp_str = "N/A"

        # Print the day summary with color and weather description
        print(f"{date_str} {color}[{rating}]{Style.RESET_ALL} {temp_str} - {weather_desc}")

        # In comparison mode, don't show hourly details
        if compare_mode:
            continue

        # Sort and identify best and worst blocks
        daylight_hours = sorted([h for h in daily_forecasts[date] if 8 <= h["hour"] <= 20],
                               key=lambda x: x["hour"])

        # Score each hour for outdoor activity
        for hour in daylight_hours:
            hour["total_score"] = sum(score for score_name, score in hour.items()
                                   if score_name.endswith("_score") and isinstance(score, (int, float)))

        # Find consecutive hours with similar weather
        weather_blocks = find_weather_blocks(daylight_hours)

        # Get best and worst times (highest and lowest scoring blocks)
        best_block = None
        worst_block = None
        best_score = float('-inf')
        worst_score = float('inf')

        # Identify blocks with consistently good or bad weather scores
        for block, weather_type in weather_blocks:
            if len(block) < 2:  # Skip single hour blocks
                continue

            avg_block_score = sum(h["total_score"] for h in block) / len(block)

            # Find single best block
            if avg_block_score > best_score and (weather_type in ["sunny", "cloudy"] or avg_block_score >= 0):
                best_score = avg_block_score
                best_block = (block, weather_type)

            # Find single worst block
            if avg_block_score < worst_score and (weather_type == "rainy" or avg_block_score < 0):
                worst_score = avg_block_score
                worst_block = (block, weather_type)

        # Display best time (only the single best block) without details
        if best_block:
            block, weather_type = best_block
            start_time = block[0]["time"].strftime("%H:%M")
            end_time = block[-1]["time"].strftime("%H:%M")
            print(f"  Best: {Fore.GREEN}{start_time}-{end_time}{Style.RESET_ALL}")

        # Display worst time only if a good day and there's a specific bad period, without details
        if worst_block and scores["avg_score"] >= 0:
            block, weather_type = worst_block
            start_time = block[0]["time"].strftime("%H:%M")
            end_time = block[-1]["time"].strftime("%H:%M")
            print(f"  Avoid: {Fore.RED}{start_time}-{end_time}{Style.RESET_ALL}")

def compare_locations(location_data, date_filter=None):
    """Compare weather conditions across multiple locations for planning purposes"""
    # If no date filter provided, use today
    if not date_filter:
        date_filter = datetime.now(pytz.timezone("Europe/Madrid")).date()

    print(f"\nBest locations for {date_filter.strftime('%A, %d %b')}")

    # Get data for the specified date across all locations
    date_data = []
    for location_name, forecast in location_data.items():
        if not forecast or not forecast["day_scores"]:
            continue

        for date, scores in forecast["day_scores"].items():
            if date == date_filter:
                date_data.append(scores)
                break

    # Sort locations by score (best to worst)
    date_data.sort(key=lambda x: x["avg_score"], reverse=True)

    # Find longest location name for proper formatting
    max_location_length = max(len(data["location"]) for data in date_data) if date_data else 15
    location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

    # Print table header with proper spacing - removed Rain column
    print(f"\n{'Location':<{location_width}} {'Rating':<10} {'Temp':<15} {'Weather':<13} {'Score':<6}")
    print(f"{'-'*location_width} {'-'*10} {'-'*15} {'-'*13} {'-'*6}")

    for data in date_data:
        location = data["location"]

        # Determine rating description and color
        if data["avg_score"] >= 6:
            rating = "Excellent"
            color = Fore.LIGHTGREEN_EX
        elif data["avg_score"] >= 3:
            rating = "Good"
            color = Fore.GREEN
        elif data["avg_score"] >= 0:
            rating = "Fair"
            color = Fore.YELLOW
        elif data["avg_score"] >= -3:
            rating = "Poor"
            color = Fore.LIGHTRED_EX
        else:
            rating = "Avoid"
            color = Fore.RED

        # Weather description - consistently use standardized naming
        if data["sunny_hours"] > data["partly_cloudy_hours"] and data["sunny_hours"] > data["rainy_hours"]:
            weather = "Sunny"
        elif data["partly_cloudy_hours"] > data["sunny_hours"] and data["partly_cloudy_hours"] > data["rainy_hours"]:
            weather = "P.Cloudy"
        elif data["rainy_hours"] > 0:
            weather = f"Rain ({data['rainy_hours']}h)"
        else:
            weather = "Mixed"

        # Temperature range
        temp = ""
        if data["min_temp"] is not None and data["max_temp"] is not None:
            temp = f"{data['min_temp']:.1f}°C - {data['max_temp']:.1f}°C"
        else:
            temp = "N/A"

        # Format score
        score_str = f"{data['avg_score']:.1f}"

        # Always color location with cyan, regardless of mode
        print(f"{Fore.CYAN}{location:<{location_width}}{Style.RESET_ALL} {color}{rating:<10}{Style.RESET_ALL} {temp:<15} {weather:<13} {score_str:>6}")

def list_locations():
    """List all available locations"""
    print(f"\n{Fore.CYAN}Available locations:{Style.RESET_ALL}")
    for key, loc in LOCATIONS.items():
        print(f"  {key} - {Fore.CYAN}{loc['name']}{Style.RESET_ALL}")

def extract_best_blocks(forecast_data, location_name):
    """Extract best time blocks from forecast data for a specific location"""
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
        daylight_hours = sorted([h for h in daily_forecasts[date] if 8 <= h["hour"] <= 20],
                               key=lambda x: x["hour"])

        # Score each hour for outdoor activity
        for hour in daylight_hours:
            hour["total_score"] = sum(score for score_name, score in hour.items()
                               if score_name.endswith("_score") and isinstance(score, (int, float)))

        # Find consecutive hours with similar weather
        weather_blocks = find_weather_blocks(daylight_hours)

        # Find the best and worst blocks
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
    """Analyze forecast data and recommend the best times to go out this week"""
    madrid_tz = pytz.timezone("Europe/Madrid")
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
                daylight_hours = sorted([h for h in daily_hours if 8 <= h["hour"] <= 20],
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

                        # Get the dominant weather symbol using a type-safe approach
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

def display_best_times_recommendation(location_data):
    """Display a simple recommendation for when to go out this week"""
    all_periods = recommend_best_times(location_data)

    if not all_periods:
        print(f"\n{Fore.YELLOW}No ideal outdoor times found for this week.{Style.RESET_ALL}")
        print("Try checking individual locations for more details.")
        return

    print(f"\n{Fore.CYAN}BEST TIMES TO GO OUT IN THE NEXT 7 DAYS:{Style.RESET_ALL}")

    # Group periods by date
    days = defaultdict(list)
    for period in all_periods:
        days[period["date"]].append(period)

    # Extract more options per day, including those with lower scores
    filtered_periods = []
    for date, periods in sorted(days.items()):
        # Sort all periods by score
        periods.sort(key=lambda x: x["score"], reverse=True)

        # Take up to 5 periods for each day to show more options
        for p in periods[:5]:
            filtered_periods.append(p)

    # Find the longest location name for proper alignment
    max_location_length = max(len(period["location"]) for period in filtered_periods) if filtered_periods else 15
    location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

    # Print a header row for better readability
    print(f"{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{location_width}} {'Weather':<20} {'Score':>6}")
    print(f"{'-'*3} {'-'*16} {'-'*15} {'-'*10} {'-'*location_width} {'-'*20} {'-'*6}")

    # Format and display the filtered results
    current_date = None

    for i, period in enumerate(filtered_periods, 1):
        # Add extra line between days
        if current_date and current_date != period["date"]:
            print()
        current_date = period["date"]

        date_str = period["date"].strftime("%d %b")
        day_name = period["day_name"][:3]  # First three chars of day name
        day_date = f"{day_name}, {date_str}"

        start_str = period["start_time"].strftime("%H:%M")
        end_str = period["end_time"].strftime("%H:%M")
        time_range = f"{start_str}-{end_str}"

        # Determine color based on score
        if period["score"] >= 25:
            color = Fore.LIGHTGREEN_EX
        elif period["score"] >= 15:
            color = Fore.GREEN
        elif period["score"] >= 5:
            color = Fore.GREEN
        elif period["score"] >= 0:
            color = Fore.YELLOW
        else:
            color = Fore.YELLOW

        duration_str = f"{period['duration']} hours"

        # Use standardized weather description function
        weather_desc = get_standardized_weather_desc(period["dominant_symbol"])

        # Add temperature if available
        temp_desc = ""
        if period["avg_temp"] is not None:
            temp_desc = f", {period['avg_temp']:.1f}°C"

        weather_with_temp = f"{weather_desc}{temp_desc}"

        # Show the score to understand the ranking
        score_str = f"{period['score']:.1f}"

        # Create a properly aligned recommendation
        print(f"{i:<3} {color}{day_date:<16}{Style.RESET_ALL} {time_range:<15} {duration_str:<10} {Fore.CYAN}{period['location']:<{location_width}}{Style.RESET_ALL} {weather_with_temp:<20} {score_str:>6}")

def main():
    """Main function to process command-line arguments and display weather forecasts"""
    parser = argparse.ArgumentParser(description="Weather forecast for outdoor activities in Asturias")

    location_group = parser.add_mutually_exclusive_group()
    location_group.add_argument("--location", "-l", choices=LOCATIONS.keys(),
                               help="Specific location to check")
    location_group.add_argument("--all", "-a", action="store_true",
                               help="Show all locations")
    location_group.add_argument("--compare", "-c", action="store_true",
                               help="Compare all locations for best weather")
    location_group.add_argument("--list", action="store_true",
                               help="List all available locations")

    parser.add_argument("--date", "-d", type=str,
                       help="Date to compare locations (format: YYYY-MM-DD)")
    parser.add_argument("--no-clear", action="store_true",
                       help="Don't clear the screen before displaying results")
    parser.add_argument("--recommend", "-r", action="store_true",
                       help="Show direct recommendations for when to go out this week")

    args = parser.parse_args()

    # Just list locations and exit
    if args.list:
        list_locations()
        return

    # Parse comparison date if provided
    comparison_date = None
    if args.date:
        try:
            comparison_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"{Fore.RED}Invalid date format. Use YYYY-MM-DD.{Style.RESET_ALL}")
            return

    # Default to Oviedo if no location specified
    selected_locations = {}
    if args.location:
        selected_locations[args.location] = LOCATIONS[args.location]
    elif args.all or args.compare or args.recommend:
        selected_locations = LOCATIONS
    else:
        selected_locations["oviedo"] = LOCATIONS["oviedo"]

    # Clear screen unless disabled
    if not args.no_clear:
        print("\033[2J\033[H")  # ANSI escape sequence to clear screen

    # Fetch and process data for all selected locations
    location_data = {}
    for loc_key, location in selected_locations.items():
        print(f"Fetching data for {location['name']}...")
        data = fetch_weather_data(location)
        if data:
            location_data[loc_key] = process_forecast(data, location['name'])
            # Add a small delay between API calls to avoid rate limiting
            time.sleep(0.5)

    print()  # Add a blank line for better readability

    # Display recommendations if requested
    if args.recommend:
        display_best_times_recommendation(location_data)
        return

    # Display mode depends on arguments
    if args.compare:
        if comparison_date:
            compare_locations(location_data, comparison_date)
        else:
            # Compare for today
            compare_locations(location_data)

        # Show location summaries for each city in comparison mode
        for loc_key, forecast in location_data.items():
            display_forecast(forecast, LOCATIONS[loc_key]["name"], compare_mode=True)
    else:
        # Display each location's forecast in detail
        for loc_key, forecast in location_data.items():
            display_forecast(forecast, LOCATIONS[loc_key]["name"])

if __name__ == "__main__":
    main()
