"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""
import argparse
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import pytz
import requests
from colorama import Fore, Style, init

# Configuration constants
# Define locations in Asturias
LOCATIONS = {
  "oviedo": {"name": "Oviedo", "lat": 43.3619, "lon": -5.8494},
  "llanes": {"name": "Llanes", "lat": 43.4200, "lon": -4.7550},
  "aviles": {"name": "Avilés", "lat": 43.5547, "lon": -5.9248},
  "somiedo": {"name": "Somiedo", "lat": 43.0981, "lon": -6.2550},
  "teverga": {"name": "Teverga", "lat": 43.1578, "lon": -6.0867},
  "gijonsaswe": {"name": "Gijón", "lat": 43.5322, "lon": -5.6611},
  "taramundi": {"name": "Taramundi", "lat": 43.3583, "lon": -7.1083},
  "ribadesella": {"name": "Ribadesella", "lat": 43.4675, "lon": -5.0553},
  "tapia": {"name": "Tapia de Casariego", "lat": 43.5700, "lon": -6.9436},
  "cangas_de_onis": {"name": "Cangas de Onís", "lat": 43.3507, "lon": -5.1356},
  "lagos_covadonga": {"name": "Lagos de Covadonga", "lat": 43.2728, "lon": -4.9906},
}


# Weather rating system - positive scores for good outdoor conditions
WEATHER_SCORES = {
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

# API settings
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
DAYLIGHT_START_HOUR = 8
DAYLIGHT_END_HOUR = 20
FORECAST_DAYS = 7


def fetch_weather_data(location):
  """Fetch weather data for a specific location.

  Args:
      location: Dictionary containing lat/lon coordinates

  Returns:
      JSON response from API or None if request failed
  """
  lat = location["lat"]
  lon = location["lon"]

  # Request headers - required by Met.no API
  headers = {
      "User-Agent": "DailyHelper/1.0"
  }

  # Construct API URL
  url = f"{API_URL}?lat={lat}&lon={lon}"

  # Fetch data with error handling
  try:
      response = requests.get(url, headers=headers)
      response.raise_for_status()  # Raise an exception for HTTP errors
      return response.json()
  except requests.exceptions.RequestException as e:
      print(
          f"{Fore.RED}Error fetching weather data for {location['name']}: {e}{Style.RESET_ALL}")
      return None
  except ValueError as e:
      print(
          f"{Fore.RED}Error parsing JSON response for {location['name']}: {e}{Style.RESET_ALL}")
      return None

# Weather utility functions


def temp_score(temp):
  """Rate temperature for outdoor comfort on a scale of -10 to 10."""
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


def wind_score(wind_speed):
  """Rate wind speed comfort on a scale of -10 to 0."""
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


def cloud_score(cloud_coverage):
  """Rate cloud coverage for outdoor activities on a scale of -5 to 5."""
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


def uv_score(uv_index):
  """Rate UV index for comfort/safety on a scale of -5 to 5."""
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


def precip_probability_score(probability):
  """Rate precipitation probability on a scale of -10 to 0."""
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


def get_standardized_weather_desc(symbol):
  """Return standardized weather description from symbol code."""
  if not symbol or not isinstance(symbol, str):
      return "Unknown"

  # Prioritize specific, common symbols
  symbol_map = {
      "clearsky": "Sunny",
      "fair": "M.Sunny",
      "partlycloudy": "P.Cloudy",
      "cloudy": "Cloudy",
      "lightrain": "L.Rain",
      "lightrainshowers": "L.Rain Shwrs",
      "rain": "Rain",
      "rainshowers": "Rain Shwrs",
      "heavyrain": "H.Rain",
      "heavyrainshowers": "H.Rain Shwrs",
      "lightsnow": "L.Snow",
      "lightsnowshowers": "L.Snow Shwrs",
      "snow": "Snow",
      "snowshowers": "Snow Shwrs",
      "heavysnow": "H.Snow",
      "heavysnowshowers": "H.Snow Shwrs",
      "fog": "Foggy",
      "sleet": "Sleet",
      "lightsleet": "L.Sleet",
      "heavysleet": "H.Sleet",
      "thunder": "Thunder",  # Catches variants like lightrainandthunder
      "thunderstorm": "Thunderstorm"
  }

  # Check for direct matches first
  if symbol in symbol_map:
      return symbol_map[symbol]

  # Handle compound symbols or less common ones by checking keywords
  if "thunder" in symbol:  # Must be before rain/snow if combined
      return "Thunder"
  elif "lightrain" in symbol:
      return "L.Rain"
  elif "heavyrain" in symbol:
      return "H.Rain"
  elif "rain" in symbol:
      return "Rain"
  elif "lightsnow" in symbol:
      return "L.Snow"
  elif "heavysnow" in symbol:
      return "H.Snow"
  elif "snow" in symbol:
      return "Snow"
  elif "sleet" in symbol:  # General sleet after specific variants
      return "Sleet"
  else:
      # Fallback: Capitalize and replace underscores for any other unmapped symbols
      return symbol.replace("_", " ").capitalize()


def find_weather_blocks(hours):
  """Find blocks of hours with similar weather conditions."""
  if not hours:
      return []

  # Sort hours by time
  sorted_hours = sorted(hours, key=lambda x: x["hour"])

  blocks = []
  current_block = [sorted_hours[0]]
  current_type = "sunny" if sorted_hours[0]["symbol"] in [
      "clearsky", "fair"] else "rainy" if "rain" in sorted_hours[0]["symbol"] else "cloudy"

  for hour in sorted_hours[1:]:
      hour_type = "sunny" if hour["symbol"] in [
          "clearsky", "fair"] else "rainy" if "rain" in hour["symbol"] else "cloudy"

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


def _get_dominant_symbol(symbols):
  """Get the most frequent symbol from a list of symbols."""
  if not symbols:
      return "N/A"
  # Ensure all elements are strings before counting
  valid_symbols = [s for s in symbols if isinstance(s, str) and s != "N/A"]
  if not valid_symbols:
      return "N/A"
  return Counter(valid_symbols).most_common(1)[0][0]

# Forecast analysis functions


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
          precipitation_1h = next_1h_details.get(
              "precipitation_amount", "n/a")
          precipitation_prob_1h = next_1h_details.get(
              "probability_of_precipitation", "n/a")

          # Get next 6 hour forecast details if available
          next_6h = entry["data"].get("next_6_hours", {})
          next_6h_details = next_6h.get("details", {})
          precipitation_6h = next_6h_details.get(
              "precipitation_amount", "n/a")
          precipitation_prob_6h = next_6h_details.get(
              "probability_of_precipitation", "n/a")
          uv_index = next_6h_details.get(
              "ultraviolet_index_clear_sky_max", "n/a")

          # Use 1h precipitation probability if available, otherwise use 6h
          precipitation_prob = precipitation_prob_1h if precipitation_prob_1h != "n/a" else precipitation_prob_6h

          # Get weather symbol with fallbacks
          symbol = next_1h.get("summary", {}).get(
              "symbol_code", next_6h.get("summary", {}).get("symbol_code", "n/a"))

          # Clean up the symbol code by removing day/night suffix if present
          if symbol != "n/a" and "_" in symbol:
              symbol = symbol.split("_")[0]

          current_hour_scores = {
              "weather_score": WEATHER_SCORES.get(symbol, 0) if symbol != "n/a" else 0,
              "temp_score": temp_score(temp),
              "wind_score": wind_score(wind),
              "cloud_score": cloud_score(cloud_coverage),
              "uv_score": uv_score(uv_index),
              "precip_prob_score": precip_probability_score(precipitation_prob)
          }
          total_hourly_score = sum(
              s for s in current_hour_scores.values() if isinstance(s, (int, float)))

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
              ** current_hour_scores,  # Unpack individual scores
              # Add the pre-calculated total score for the hour
              "total_score": total_hourly_score
          })

  # Calculate daily scores for outdoor activities
  day_scores = {}
  for date, hours in daily_forecasts.items():
      # Focus on daylight hours
      daylight_hours = [
          h for h in hours if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR]

      if not daylight_hours:
          continue

      # Calculate total scores
      total_weather_score = sum(h["weather_score"] for h in daylight_hours)
      total_temp_score = sum(h["temp_score"] for h in daylight_hours)
      total_wind_score = sum(h["wind_score"] for h in daylight_hours)
      total_cloud_score = sum(h["cloud_score"] for h in daylight_hours if isinstance(
          h["cloud_score"], (int, float)))
      total_uv_score = sum(h["uv_score"] for h in daylight_hours if isinstance(
          h["uv_score"], (int, float)))
      total_precip_prob_score = sum(h["precip_prob_score"] for h in daylight_hours if isinstance(
          h["precip_prob_score"], (int, float)))

      # Count sunny/fair hours
      sunny_hours = sum(1 for h in daylight_hours if h["symbol"] in [
                        "clearsky", "fair"])
      partly_cloudy_hours = sum(
          1 for h in daylight_hours if h["symbol"] == "partlycloudy")
      rainy_hours = sum(
          1 for h in daylight_hours if "rain" in h["symbol"] or "shower" in h["symbol"])

      # Get precipitation hours with probability > 30%
      likely_rain_hours = sum(1 for h in daylight_hours if isinstance(
          h["precipitation_probability"], (int, float)) and h["precipitation_probability"] > 30)

      # Average precipitation probability
      precip_probs = [h["precipitation_probability"] for h in daylight_hours if isinstance(
        h["precipitation_probability"], (int, float))]
      avg_precip_prob = sum(precip_probs) / \
        len(precip_probs) if precip_probs else None

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
      total_score = (total_weather_score + total_temp_score + total_wind_score + total_cloud_score + total_uv_score + total_precip_prob_score)

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


def _find_activity_blocks_for_day(daylight_hours, location_name, date_obj, min_block_len=2, block_score_threshold=-float('inf'), forbidden_symbols=None):
  """
  Finds all qualifying blocks of weather for a given day's hours based on criteria.
  Uses pre-calculated 'total_score' from hourly data.
  """
  if not daylight_hours:
      return []

  # daylight_hours should be sorted by hour
  hourly_blocks = find_weather_blocks(daylight_hours)

  qualifying_periods = []

  for block_hours, weather_type in hourly_blocks:
      if len(block_hours) < min_block_len:
          continue

      # Check for forbidden symbols within the block
      if forbidden_symbols:
          block_has_forbidden_symbol = False
          for hour_data in block_hours:
              if isinstance(hour_data.get("symbol"), str) and hour_data["symbol"] in forbidden_symbols:
                  block_has_forbidden_symbol = True
                  break
          if block_has_forbidden_symbol:
              continue

      avg_block_score = sum(h["total_score"]
                            for h in block_hours) / len(block_hours)

      if avg_block_score >= block_score_threshold:
          start_time = block_hours[0]["time"]
          end_time = block_hours[-1]["time"]
          temps = [h["temp"] for h in block_hours if isinstance(h["temp"], (int, float))]
          avg_temp = sum(temps) / len(temps) if temps else None

          symbols_in_block = [h["symbol"] for h in block_hours]
          dominant_symbol = _get_dominant_symbol(symbols_in_block)

          period = {
              "location": location_name,
              "date": date_obj,
              "day_name": date_obj.strftime("%A"),
              "start_time": start_time,
              "end_time": end_time,
              "duration": len(block_hours),
              "score": avg_block_score,
              "weather_type": weather_type,  # "sunny", "rainy", "cloudy" from find_weather_blocks
              "avg_temp": avg_temp,
              "dominant_symbol": dominant_symbol
          }
          qualifying_periods.append(period)

  return qualifying_periods


def extract_best_blocks(forecast_data, location_name):
  """
  Extract the single best time block per day from forecast data for a specific location.
  A "best" block has a good score and generally favorable weather type.
  """
  if not forecast_data or not forecast_data.get("daily_forecasts"):
      return []

  extracted_best_periods = []
  daily_forecasts = forecast_data["daily_forecasts"]
  day_scores = forecast_data.get("day_scores", {})

  for date_obj, daily_hours_list in sorted(daily_forecasts.items()):
      # Ensure the day has a score entry; skip if avg_score is too low for "best" consideration
      current_day_score_info = day_scores.get(date_obj)
      # Stricter for "best" day
      if current_day_score_info and current_day_score_info.get("avg_score", -float('inf')) < -5:
          continue

      daylight_hours = sorted(
          [h for h in daily_hours_list if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
          key=lambda x: x["hour"]
      )
      if not daylight_hours:
          continue

      # Find all potentially good blocks for this day
      # Criteria for "best": score >= 0, avoid rainy type explicitly
      # We let _find_activity_blocks_for_day return multiple, then pick the top one.
      potential_blocks_for_day = _find_activity_blocks_for_day(
          daylight_hours,
          location_name,
          date_obj,
          min_block_len=2,
          block_score_threshold=0  # Higher threshold for "best" blocks
      )

      # From these potential blocks, select the one with the highest score,
      # and prefer "sunny" or "cloudy" general types.
      best_block_for_this_day = None
      highest_score_for_day = -float('inf')

      for block_period in potential_blocks_for_day:
          # Prefer non-rainy types for "best" blocks or very high scores
          if block_period["weather_type"] in ["sunny", "cloudy"] or block_period["score"] >= 5:
              if block_period["score"] > highest_score_for_day:
                  highest_score_for_day = block_period["score"]
                  best_block_for_this_day = block_period

      if best_block_for_this_day:
          extracted_best_periods.append(best_block_for_this_day)

  return extracted_best_periods


def recommend_best_times(location_data):
  """Analyze forecast data and recommend the best times to go out this week."""
  madrid_tz = pytz.timezone(TIMEZONE)
  today = datetime.now(madrid_tz).date()
  end_date = today + timedelta(days=FORECAST_DAYS)  # Use FORECAST_DAYS

  all_periods = []

  # 1. Attempt to fill all_periods using extract_best_blocks (stricter criteria)
  for loc_key, forecast in location_data.items():
      if not forecast:
          continue
      location_display_name = LOCATIONS[loc_key]["name"]
      # extract_best_blocks finds one best block per day for this location
      best_blocks_for_loc = extract_best_blocks(
          forecast, location_display_name)
      all_periods.extend(best_blocks_for_loc)

  # 2. If no "best" periods found, use a more lenient approach for all locations and days
  if not all_periods:
      lenient_periods_by_day = defaultdict(list)
      for loc_key, forecast in location_data.items():
          if not forecast or not forecast.get("daily_forecasts"):
              continue

          location_display_name = LOCATIONS[loc_key]["name"]

          for date_obj, daily_hours_list in sorted(forecast["daily_forecasts"].items()):
              if not (today <= date_obj < end_date):
                  continue

              # Skip days with overall very poor scores even for lenient search
              day_score_info = forecast.get("day_scores", {}).get(date_obj)
              if day_score_info and day_score_info.get("avg_score", -float('inf')) < -15:
                  continue

              daylight_hours = sorted(
                  [h for h in daily_hours_list if DAYLIGHT_START_HOUR
                    <= h["hour"] <= DAYLIGHT_END_HOUR],
                  key=lambda x: x["hour"]
              )
              if not daylight_hours:
                  continue

              # Use _find_activity_blocks_for_day with lenient criteria
              blocks_for_day_lenient = _find_activity_blocks_for_day(
                  daylight_hours,
                  location_display_name,
                  date_obj,
                  min_block_len=2,
                  block_score_threshold=-10,  # Lenient score threshold
                  forbidden_symbols=["heavyrain", "heavyrainshowers", "thunderstorm", "heavysnow", "heavysnowshowers"]
              )
              lenient_periods_by_day[date_obj].extend(blocks_for_day_lenient)

      # Consolidate and pick top N from lenient periods
      for date_obj in sorted(lenient_periods_by_day.keys()):
          # Sort by score (best first) within the day
          lenient_periods_by_day[date_obj].sort(
              key=lambda x: x["score"], reverse=True)
          # Take up to 3 best periods per day from the lenient search
          all_periods.extend(lenient_periods_by_day[date_obj][:3])

  # Sort all collected periods (either strict or lenient) by date and then by score
  all_periods.sort(key=lambda x: (x["date"], -x["score"]))
  return all_periods

# Display utility functions


def get_rating_info(score):
  """Return standardized rating description and color based on score."""
  if score >= 6:
      return "Excellent", Fore.LIGHTGREEN_EX
  elif score >= 3:
      return "Good", Fore.GREEN
  elif score >= 0:
      return "Fair", Fore.YELLOW
  elif score >= -3:
      return "Poor", Fore.LIGHTRED_EX
  else:
      return "Avoid", Fore.RED


def _get_day_summary_weather_description(scores, include_precip_warning=True):
  """Generates a concise weather summary string for a day based on its scores."""
  precip_warning = ""
  if include_precip_warning and scores.get("avg_precip_prob") is not None and scores["avg_precip_prob"] > 40:
      precip_warning = f" - {scores['avg_precip_prob']:.0f}% rain"

  if scores.get("sunny_hours", 0) > scores.get("partly_cloudy_hours", 0) and scores.get("sunny_hours", 0) > scores.get("rainy_hours", 0):
      return "Sunny" + precip_warning
  elif scores.get("partly_cloudy_hours", 0) > scores.get("sunny_hours", 0) and scores.get("partly_cloudy_hours", 0) > scores.get("rainy_hours", 0):
      return "P.Cloudy" + precip_warning
  elif scores.get("rainy_hours", 0) > 0:
      return f"Rain ({scores['rainy_hours']}h)"
  else:
      return "Mixed" + precip_warning


def display_forecast(forecast_data, location_name, compare_mode=False):
  """Display weather forecast for a location."""
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

      # Use centralized rating function
      rating, color = get_rating_info(scores["avg_score"])

      # Determine overall weather description
      weather_desc = _get_day_summary_weather_description(scores)

      # Use min-max temperature range
      temp_str = ""
      if scores["min_temp"] is not None and scores["max_temp"] is not None:
          temp_str = f"{scores['min_temp']:>4.1f}°C - {scores['max_temp']:>4.1f}°C"
      else:
          temp_str = "N/A"

      # Print the day summary with color and weather description
      print(
          f"{date_str} {color}[{rating}]{Style.RESET_ALL} {temp_str} - {weather_desc}")

      # In comparison mode, don't show hourly details
      if compare_mode:
          continue

      # Sort and identify best and worst blocks
      daylight_hours = sorted([h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
                              key=lambda x: x["hour"])

      if not daylight_hours:
          continue

      # Score each hour for outdoor activity
      for hour in daylight_hours:
          hour["total_score"] = sum(score for score_name, score in hour.items()
                                    if score_name.endswith("_score") and isinstance(score, (int, float)))

      # Find blocks with similar weather
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

      # Display best time block
      if best_block:
          block, weather_type = best_block
          start_time = block[0]["time"].strftime("%H:%M")
          end_time = block[-1]["time"].strftime("%H:%M")
          print(
              f"  Best: {Fore.GREEN}{start_time}-{end_time}{Style.RESET_ALL}")

      # Display worst time only if it's a good day with a specific bad period
      if worst_block and scores["avg_score"] >= 0:
          block, weather_type = worst_block
          start_time = block[0]["time"].strftime("%H:%M")
          end_time = block[-1]["time"].strftime("%H:%M")
          print(
              f"  Avoid: {Fore.RED}{start_time}-{end_time}{Style.RESET_ALL}")


def compare_locations(location_data, date_filter=None):
  """Compare weather conditions across multiple locations for planning purposes."""
  # If no date filter provided, use today
  if not date_filter:
      date_filter = datetime.now(pytz.timezone(TIMEZONE)).date()

  print(f"\nBest locations for {date_filter.strftime('%A, %d %b')}")

  # Get data for the specified date across all locations
  date_data = []
  for location_name_key, forecast in location_data.items():  # Use location_name_key to avoid clash
      if not forecast or not forecast["day_scores"]:
          continue

      for date, scores in forecast["day_scores"].items():
          if date == date_filter:
              # Add original location name from LOCATIONS if possible, or use a fallback
              display_name = LOCATIONS.get(location_name_key, {}).get(
                  "name", scores.get("location", "Unknown Loc"))
              # Ensure the scores dict has the display name we want for the table
              # The 'location' field in 'scores' should already be the display name from process_forecast
              # but we can ensure it for consistency if it's passed differently.
              scores_copy = scores.copy()
              scores_copy["location_display_for_compare"] = display_name
              date_data.append(scores_copy)
              break

  # Sort locations by score (best to worst)
  date_data.sort(key=lambda x: x["avg_score"], reverse=True)

  if not date_data:
      print(f"\n{Fore.YELLOW}No data available for this date.{Style.RESET_ALL}")
      return

  # Find longest location name for proper formatting
  max_location_length = max(len(data["location_display_for_compare"])
                            for data in date_data) if date_data else 17
  location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

  # Print table header with proper spacing
  print(f"\n{'Location':<{location_width}} {'Rating':<10} {'Temp':<15} {'Weather':<13} {'Score':>6}")
  print(f"{'-' * location_width} {'-' * 10} {'-' * 15} {'-' * 13} {'-' * 6}")

  for data in date_data:
      # Use the name prepared for display
      location_display = data["location_display_for_compare"]

      # Use centralized rating function
      rating, color = get_rating_info(data["avg_score"])

      # Weather description using the helper
      weather = _get_day_summary_weather_description(
          data, include_precip_warning=False)  # No precip % in compare table

      # Temperature range
      temp = "N/A"
      if data["min_temp"] is not None and data["max_temp"] is not None:
          temp = f"{data['min_temp']:.1f}°C - {data['max_temp']:.1f}°C"

      # Format score
      score_str = f"{data['avg_score']:.1f}"

      # Always color location with cyan
      print(f"{Fore.CYAN}{location_display:<{location_width}}{Style.RESET_ALL} {color}{rating:<10}{Style.RESET_ALL} {temp:<15} {weather:<13} {score_str:>6}")


def list_locations():
  """List all available locations."""
  print(f"\n{Fore.CYAN}Available locations:{Style.RESET_ALL}")
  for key, loc in LOCATIONS.items():
      print(f"  {key} - {Fore.CYAN}{loc['name']}{Style.RESET_ALL}")


def display_best_times_recommendation(location_data):
  """Display a simple recommendation for when to go out this week."""
  all_periods = recommend_best_times(location_data)

  if not all_periods:
      print(
          f"\n{Fore.YELLOW}No ideal outdoor times found for this week.{Style.RESET_ALL}")
      print("Try checking individual locations for more details or broaden search criteria if applicable.")
      return

  print(f"\n{Fore.CYAN}BEST TIMES TO GO OUT IN THE NEXT 7 DAYS:{Style.RESET_ALL}")

  # Limit to a reasonable number, e.g., 5 per day for 7 days
  display_periods = all_periods[:35]

  # Find the longest location name for proper alignment
  max_location_length = max(
      len(period["location"]) for period in display_periods) if display_periods else 15
  location_width = max(max_location_length + 2, 17)  # Minimum 17 chars
  weather_width = 20  # Field width for weather + temp alignment

  # Print header row
  print(f"{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{location_width}} {'Weather':<{weather_width}} {'Score':>6}")
  print(f"{'-' * 3} {'-' * 16} {'-' * 15} {'-' * 10} {'-' * location_width} {'-' * weather_width} {'-' * 6}")

  current_date = None

  for i, period in enumerate(display_periods, 1):  # Use display_periods
      if current_date and current_date != period["date"]:
          print()  # Add line break between dates
      current_date = period["date"]

      date_str = period["date"].strftime("%d %b")
      day_name = period["day_name"][:3]
      day_date = f"{day_name}, {date_str}"

      start_str = period["start_time"].strftime("%H:%M")
      end_str = period["end_time"].strftime("%H:%M")
      time_range = f"{start_str}-{end_str}"

      rating, color = get_rating_info(period["score"])
      duration_str = f"{period['duration']} hours"

      weather_desc = get_standardized_weather_desc(
          period["dominant_symbol"])[:12]  # Limit length
      weather_desc = f"{weather_desc:<12}"  # Left-align

      temp_desc = ""
      if period["avg_temp"] is not None:
          temp_desc = f"{period['avg_temp']:>5.1f}°C"  # Right-align temp

      weather_with_temp = f"{weather_desc} {temp_desc}"  # Combined field
      score_str = f"{period['score']:.1f}"

      # Print formatted row
      print(
          f"{i:<3} "
          f"{color}{day_date:<16}{Style.RESET_ALL} "
          f"{time_range:<15} "
          f"{duration_str:<10} "
          f"{Fore.CYAN}{period['location']:<{location_width}}{Style.RESET_ALL} "
          f"{weather_with_temp:<{weather_width}} "
          f"{score_str:>6}"
      )


# Initialize colorama for colored terminal output
init()


def main():
  """Main function to process command-line arguments and display weather forecasts."""
  parser = argparse.ArgumentParser(
      description="Weather forecast for outdoor activities in Asturias")

  location_group = parser.add_mutually_exclusive_group()
  location_group.add_argument("--location", "-l", choices=LOCATIONS.keys(), help="Specific location to check")
  location_group.add_argument("--all", "-a", action="store_true", help="Show all locations")
  location_group.add_argument("--compare", "-c", action="store_true", help="Compare all locations for best weather")
  location_group.add_argument("--list", action="store_true", help="List all available locations")

  parser.add_argument("--date", "-d", type=str, help="Date to compare locations (format: YYYY-MM-DD)")
  parser.add_argument("--no-clear", action="store_true", help="Don't clear the screen before displaying results")
  parser.add_argument("--recommend", "-r", action="store_true", help="Show direct recommendations for when to go out this week")

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
      # Ensure only valid keys are accessed
      if args.location in LOCATIONS:
          selected_locations[args.location] = LOCATIONS[args.location]
      else:
          print(f"{Fore.RED}Error: Location '{args.location}' not found. Use --list to see available locations.{Style.RESET_ALL}")
          return
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
          display_forecast(
              forecast, LOCATIONS[loc_key]["name"], compare_mode=True)
  else:
      # Display each location's forecast in detail (if any data was fetched)
      if not location_data and (args.location or not (args.all or args.compare or args.recommend)):
          # This case handles if a single location was specified but data fetch failed or was empty
          # For example, if 'oviedo' (default) fails, location_data would be empty.
          print(
              f"{Fore.YELLOW}No forecast data processed. Check connection or location.{Style.RESET_ALL}")
      for loc_key, forecast in location_data.items():
          display_forecast(forecast, LOCATIONS[loc_key]["name"])


if __name__ == "__main__":
  main()
