"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""

import argparse
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import requests
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

# Configuration constants


class Location:
  def __init__(self, key, name, lat, lon):
    self.key = key
    self.name = name
    self.lat = lat
    self.lon = lon


# Define locations in Asturias
LOCATIONS = {
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6611),
    "oviedo": Location("oviedo", "Oviedo", 43.3619, -5.8494),
    "llanes": Location("llanes", "Llanes", 43.4200, -4.7550),
    "aviles": Location("aviles", "Avilés", 43.5547, -5.9248),
    "somiedo": Location("somiedo", "Somiedo", 43.0981, -6.2550),
    "teverga": Location("teverga", "Teverga", 43.1578, -6.0867),
    "taramundi": Location("taramundi", "Taramundi", 43.3583, -7.1083),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4675, -5.0553),
    "tapia": Location("tapia", "Tapia de Casariego", 43.5700, -6.9436),
    "cangas_de_onis": Location("cangas_de_onis", "Cangas de Onís", 43.3507, -5.1356),
    "lagos_covadonga": Location("lagos_covadonga", "Lagos de Covadonga", 43.2728, -4.9906),
}

# Weather rating system - positive scores for good outdoor conditions
WEATHER_SYMBOLS = {
    "clearsky": ("Sunny", 10),
    "fair": ("Mostly Sunny", 8),
    "partlycloudy": ("Partly Cloudy", 6),
    "cloudy": ("Cloudy", 3),
    "lightrain": ("Light Rain", -2),
    "lightrainshowers": ("Light Rain", -2),
    "lightsleet": ("Light Sleet", -3),
    "lightsleetshowers": ("Light Sleet", -3),
    "lightsnow": ("Light Snow", -3),
    "lightsnowshowers": ("Light Snow", -3),
    "rain": ("Rain", -5),
    "rainshowers": ("Rain", -5),
    "sleet": ("Sleet", -6),
    "sleetshowers": ("Sleet", -6),
    "snow": ("Snow", -6),
    "snowshowers": ("Snow", -6),
    "heavyrain": ("Heavy Rain", -10),
    "heavyrainshowers": ("Heavy Rain", -10),
    "heavysleet": ("Heavy Sleet", -10),
    "heavysleetshowers": ("Heavy Sleet", -10),
    "heavysnow": ("Heavy Snow", -10),
    "heavysnowshowers": ("Heavy Snow", -10),
    "fog": ("Foggy", -4),
    "thunderstorm": ("Thunderstorm", -15)
}

# API settings
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT = "DailyHelper/1.0"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
DAYLIGHT_START_HOUR = 8
DAYLIGHT_END_HOUR = 20
FORECAST_DAYS = 7


class HourlyWeather:
  def __init__(self, time, temp, wind, humidity, cloud_coverage, fog, wind_direction, wind_gust, precipitation_amount, precipitation_probability, symbol):
    self.time = time
    self.hour = time.hour
    self.temp = temp
    self.wind = wind
    self.humidity = humidity
    self.cloud_coverage = cloud_coverage
    self.fog = fog
    self.wind_direction = wind_direction
    self.wind_gust = wind_gust
    self.precipitation_amount = precipitation_amount
    self.precipitation_probability = precipitation_probability
    self.symbol = symbol
    self.weather_score = get_weather_score(symbol)
    self.temp_score = temp_score(temp)
    self.wind_score = wind_score(wind)
    self.cloud_score = cloud_score(cloud_coverage)
    self.precip_prob_score = precip_probability_score(
        precipitation_probability)
    self.total_score = self._calculate_total_score()

  def _calculate_total_score(self):
    return sum(score for score in [self.weather_score, self.temp_score, self.wind_score, self.cloud_score, self.precip_prob_score] if isinstance(score, (int, float)))


class DailyReport:
  def __init__(self, date, daylight_hours, location_name):
    self.date = date
    self.daylight_hours = daylight_hours
    self.location_name = location_name
    self.day_name = date.strftime("%A")

    if not daylight_hours:
      # or some other indicator of no data
      self.avg_score = -float('inf')
      self.sunny_hours = 0
      self.partly_cloudy_hours = 0
      self.rainy_hours = 0
      self.likely_rain_hours = 0
      self.avg_precip_prob = None
      self.total_score = 0
      self.min_temp = None
      self.max_temp = None
      self.avg_temp = None
      return

    total_weather_score = sum(h.weather_score for h in daylight_hours)
    total_temp_score = sum(h.temp_score for h in daylight_hours)
    total_wind_score = sum(h.wind_score for h in daylight_hours)
    total_cloud_score = sum(h.cloud_score for h in daylight_hours if isinstance(
        h.cloud_score, (int, float)))
    total_precip_prob_score = sum(h.precip_prob_score for h in daylight_hours if isinstance(
        h.precip_prob_score, (int, float)))

    self.sunny_hours = sum(1 for h in daylight_hours if h.symbol in ["clearsky", "fair"])
    self.partly_cloudy_hours = sum(
        1 for h in daylight_hours if h.symbol == "partlycloudy")
    self.rainy_hours = sum(
        1 for h in daylight_hours if "rain" in h.symbol or "shower" in h.symbol)
    self.likely_rain_hours = sum(1 for h in daylight_hours if isinstance(
        h.precipitation_probability, (int, float)) and h.precipitation_probability > 30)

    precip_probs = [h.precipitation_probability for h in daylight_hours if isinstance(
        h.precipitation_probability, (int, float))]
    self.avg_precip_prob = sum(precip_probs) / \
        len(precip_probs) if precip_probs else None

    num_hours = len(daylight_hours)
    factor_checks = [
        any(isinstance(h.cloud_score, (int, float))
            for h in daylight_hours),
        any(isinstance(h.precip_prob_score, (int, float))
            for h in daylight_hours)
    ]
    total_available_factors = 3 + sum(factor_checks)

    temps = [h.temp for h in daylight_hours if isinstance(
        h.temp, (int, float))]
    self.min_temp = min(temps) if temps else None
    self.max_temp = max(temps) if temps else None
    self.avg_temp = sum(temps) / len(temps) if temps else None

    self.total_score = (total_weather_score + total_temp_score +
                        total_wind_score + total_cloud_score + total_precip_prob_score)
    self.avg_score = self.total_score / \
        (num_hours * total_available_factors) if num_hours > 0 and total_available_factors > 0 else 0


# Weather description mapping
WEATHER_DESC_MAP = {
    "cloudy": "Cloudy",
    "clearsky": "Sunny",
    "fair": "Mostly Sunny",
    "partlycloudy": "Partly Cloudy",
}

# --- Weather symbol/description mapping and helpers ---


def get_weather_desc(symbol):
  """Return standardized weather description from symbol code."""
  if not symbol or not isinstance(symbol, str):
    return "Unknown"
  base = symbol.split('_')[0] if '_' in symbol else symbol
  desc, _ = WEATHER_SYMBOLS.get(
      base, (base.replace('_', ' ').capitalize(), 0))
  return desc


def get_weather_score(symbol):
  """Return weather score from symbol code."""
  if not symbol or not isinstance(symbol, str):
    return 0
  base = symbol.split('_')[0] if '_' in symbol else symbol
  _, score = WEATHER_SYMBOLS.get(base, ("", 0))
  return score


def get_standardized_weather_desc(symbol):
  """Return standardized weather description from symbol code."""
  if not symbol or not isinstance(symbol, str):
    return "Unknown"
  if symbol in WEATHER_DESC_MAP:
    return WEATHER_DESC_MAP[symbol]
  if "lightrain" in symbol:
    return "Light Rain"
  if "heavyrain" in symbol:
    return "Heavy Rain"
  if "rain" in symbol:
    return "Rain"
  if "lightsnow" in symbol:
    return "Light Snow"
  if "snow" in symbol:
    return "Snow"
  if "fog" in symbol:
    return "Foggy"
  if "thunder" in symbol:
    return "Thunder"
  return symbol.replace("_", " ").capitalize()


def fetch_weather_data(location):
  """Fetch weather data for a specific location.

  Args:
      location: Dictionary containing lat/lon coordinates

  Returns:
      JSON response from API or None if request failed
  """
  lat = location.lat
  lon = location.lon

  # Request headers - required by Met.no API
  headers = {
      "User-Agent": USER_AGENT
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
        f"{Fore.RED}Error fetching weather data for {location.name}: {e}{Style.RESET_ALL}")
    return None
  except ValueError as e:
    print(
        f"{Fore.RED}Error parsing JSON response for {location.name}: {e}{Style.RESET_ALL}")
    return None


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


def calc_total_score(hour):
  """Calculate the sum of all score components in an hour's data."""
  return sum(score for score_name, score in hour.items() if score_name.endswith('_score') and isinstance(score, (int, float)))


def extract_blocks(hours, min_block_len=2):
  """Find consecutive blocks of hours with similar weather type."""
  if not hours:
    return []
  sorted_hours = sorted(hours, key=lambda x: x.hour)
  blocks = []
  current_block = [sorted_hours[0]]

  def block_type(h):
    s = h.symbol
    if s in ("clearsky", "fair"):
      return "sunny"
    if "rain" in s:
      return "rainy"
    return "cloudy"
  current_type = block_type(sorted_hours[0])
  for hour in sorted_hours[1:]:
    hour_type = block_type(hour)
    if hour_type == current_type and hour.hour == current_block[-1].hour + 1:
      current_block.append(hour)
    else:
      if len(current_block) >= min_block_len:
        blocks.append((current_block, current_type))
      current_block = [hour]
      current_type = hour_type
  if len(current_block) >= min_block_len:
    blocks.append((current_block, current_type))
  return blocks

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

      # Use 1h precipitation probability if available, otherwise use 6h
      precipitation_prob = precipitation_prob_1h if precipitation_prob_1h != "n/a" else precipitation_prob_6h

      # Get weather symbol with fallbacks
      symbol = next_1h.get("summary", {}).get(
          "symbol_code", next_6h.get("summary", {}).get("symbol_code", "n/a"))

      # Clean up the symbol code by removing day/night suffix if present
      if symbol != "n/a" and "_" in symbol:
        symbol = symbol.split("_")[0]

      hourly_weather = HourlyWeather(
          time=local_time,
          temp=temp,
          wind=wind,
          humidity=humidity,
          cloud_coverage=cloud_coverage,
          fog=fog,
          wind_direction=wind_direction,
          wind_gust=wind_gust,
          precipitation_amount=precipitation_1h if precipitation_1h != "n/a" else precipitation_6h,
          precipitation_probability=precipitation_prob,
          symbol=symbol
      )
      daily_forecasts[forecast_date].append(hourly_weather)

  # Calculate daily scores for outdoor activities
  day_scores = {}
  for date, hours in daily_forecasts.items():
    # Focus on daylight hours
    daylight_hours = [
        h for h in hours if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR]

    if not daylight_hours:
      continue

    day_report = DailyReport(date, daylight_hours, location_name)
    day_scores[date] = day_report

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
  for date, daily_report in day_scores.items():
    # Skip days with very poor scores
    if daily_report.avg_score < -8:
      continue

    # Get daylight hours and calculate scores
    daylight_hours = sorted([h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
                            key=lambda x: x.hour)

    # Find consecutive hours with similar weather
    weather_blocks = extract_blocks(daylight_hours)

    # Find the best block
    best_block = None
    best_score = float('-inf')

    # Identify best block for this day
    for block, weather_type in weather_blocks:
      if len(block) < 2:  # Skip single hour blocks
        continue

      avg_block_score = sum(h.total_score for h in block) / len(block)

      # Identify best block
      if avg_block_score > best_score:
        best_score = avg_block_score
        best_block = (block, weather_type)

    # Add the best block to our extracted blocks
    if best_block:
      block, weather_type = best_block
      start_time = block[0].time
      end_time = block[-1].time

      # Get the average temperature during this period
      temps = [h.temp for h in block if isinstance(h.temp, (int, float))]
      avg_temp = sum(temps) / len(temps) if temps else None

      # Get the dominant weather symbol
      symbols = [h.symbol for h in block if isinstance(h.symbol, str)]
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

    location_display_name = LOCATIONS[location_name].name

    # Use the same approach as display_forecast to get best blocks
    best_blocks = extract_best_blocks(forecast, location_display_name)
    all_periods.extend(best_blocks)

  # If no periods found, use the more general approach
  if not all_periods:
    # Store the best outdoor periods for the week, organized by day
    day_periods = {}

    # Process each location
    for location_name, forecast in location_data.items():
      if not forecast or not forecast.get("day_scores"):
        continue

      location_display_name = LOCATIONS[location_name].name

      # Process each day in the forecast
      for date, daily_report in sorted(forecast["day_scores"].items()):
        if date < today or date >= end_date:
          continue

        # Extremely lenient threshold
        if daily_report.avg_score < -15:
          continue

        # Get the daily forecast data
        daylight_hours = sorted([h for h in forecast["daily_forecasts"].get(date, []) if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
                                key=lambda x: x.hour)

        # Find blocks of weather
        weather_blocks = extract_blocks(daylight_hours)

        # Identify blocks of at least 2 hours
        for block, weather_type in weather_blocks:
          if len(block) < 2:  # Skip single hour blocks
            continue

          avg_block_score = sum(
              h.total_score for h in block) / len(block)

          # Very low threshold for all locations
          block_threshold = -10

          # Only exclude severe weather
          extremely_bad_weather = [
              "heavyrain", "heavyrainshowers", "thunderstorm"]
          if (avg_block_score >= block_threshold and
                  not any(bad in block[0].symbol for bad in extremely_bad_weather if isinstance(block[0].symbol, str))):
            start_time = block[0].time
            end_time = block[-1].time

            # Get the average temperature during this period
            temps = [h.temp for h in block if isinstance(
                h.temp, (int, float))]
            avg_temp = sum(temps) / len(temps) if temps else None

            # Get the dominant weather symbol
            symbols = [
                h.symbol for h in block if isinstance(h.symbol, str)]
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
            day_periods[date] = period

    # Collect top periods for each day
    for date in sorted(day_periods.keys()):
      # Sort by score (best first)
      day_periods[date].sort(key=lambda x: x["score"], reverse=True)

      # Take up to 3 best periods per day
      num_to_take = min(3, len(day_periods[date]))
      for i in range(num_to_take):
        all_periods.append(day_periods[date])

  # Sort all periods by date and then by score
  all_periods.sort(key=lambda x: (x["date"], -x["score"]))

  # Debug: Print number of periods before potential modification
  # print(f"Initial number of periods: {len(all_periods)}")

  # If all_periods were populated by extract_best_blocks, it's fine.
  # If it was populated by the fallback logic, we might have an issue with day_periods[date] being a single object not a list.
  # The fallback logic needs to be adjusted if day_periods[date] is now a single DailyReport.
  # The goal of the fallback was to find *any* decent block from *any* location.

  # Let's re-evaluate the fallback logic structure.
  # The previous logic for all_periods in the fallback case might be problematic with DailyReport objects.
  # The original intent of the fallback was to iterate through all hours of all locations and find good blocks.
  # If all_periods is empty, it means `extract_best_blocks` (which operates on one location's full forecast at a time) didn't find much.
  # The fallback logic then iterates through *all* location_data again.

  # This condition means extract_best_blocks (run per location) yielded nothing overall.
  if not all_periods:
    # The goal here is to find *any* decent block from *any* location.
    # The previous `day_periods` was a dictionary where keys were dates and values were *lists* of periods.
    # Let's adjust the fallback to build a list of periods directly.
    fallback_periods = []
    for location_name_key, forecast_content in location_data.items():
      if not forecast_content or not forecast_content.get("day_scores"):
        continue
      loc_disp_name = LOCATIONS[location_name_key].name
      # dr is DailyReport
      for date_val, dr in sorted(forecast_content["day_scores"].items()):
        if date_val < today or date_val >= end_date:
          continue
        if dr.avg_score < -15:  # Extremely lenient threshold for the day
          continue

        dh_forecast = forecast_content["daily_forecasts"].get(
            date_val, [])
        daylight_h_list = sorted([h_obj for h_obj in dh_forecast if DAYLIGHT_START_HOUR <= h_obj.hour <= DAYLIGHT_END_HOUR],
                                 key=lambda x_obj: x_obj.hour)

        if not daylight_h_list:
          continue

        # extract_blocks expects list of HourlyWeather
        weather_blks = extract_blocks(daylight_h_list)

        for blk, weather_tp in weather_blks:
          if len(blk) < 2:  # Skip single hour blocks
            continue
          avg_blk_score = sum(
              h_obj.total_score for h_obj in blk) / len(blk)
          block_thresh = -10  # Very low threshold for all locations

          extremely_bad_w = ["heavyrain", "heavyrainshowers", "thunderstorm"]
          if (avg_blk_score >= block_thresh and
                  not any(bad in blk[0].symbol for bad in extremely_bad_w if isinstance(blk[0].symbol, str))):
            start_t = blk[0].time
            end_t = blk[-1].time
            temps_in_blk = [h_obj.temp for h_obj in blk if isinstance(
                h_obj.temp, (int, float))]
            avg_t = sum(temps_in_blk) / \
                len(temps_in_blk) if temps_in_blk else None
            symbols_in_blk = [
                h_obj.symbol for h_obj in blk if isinstance(h_obj.symbol, str)]
            sym_counts = defaultdict(int)
            for sym in symbols_in_blk:
              sym_counts[sym] += 1
            dom_sym = max(sym_counts, key=lambda k: sym_counts[k]) if sym_counts else ""

            period_data = {
                "location": loc_disp_name,
                "date": date_val,
                "day_name": date_val.strftime("%A"),
                "start_time": start_t,
                "end_time": end_t,
                "duration": len(blk),
                "score": avg_blk_score,
                "weather_type": weather_tp,
                "avg_temp": avg_t,
                "dominant_symbol": dom_sym
            }
            fallback_periods.append(period_data)
    all_periods.extend(fallback_periods)
    # Sort again if fallback was used
    all_periods.sort(key=lambda x: (x["date"], -x["score"]))

  # print(f"Final number of periods: {len(all_periods)}")
  return all_periods


def get_rating_info(score):
  """Return standardized rating description and color based on score."""
  if score >= 7.0:
    return "Excellent", Fore.LIGHTGREEN_EX
  elif score >= 4.5:
    return "Very Good", Fore.GREEN
  elif score >= 2.0:
    return "Good", Fore.CYAN  # Using Cyan for Good
  elif score >= 0.0:
    return "Fair", Fore.YELLOW
  elif score >= -3.0:
    return "Poor", Fore.LIGHTRED_EX  # Keeping Poor for this range
  else:  # score < -3.0
    return "Bad", Fore.RED


def display_forecast(forecast_data, location_name, compare_mode=False):
  """Display weather forecast for a location."""
  if not forecast_data:
    return

  daily_forecasts = forecast_data["daily_forecasts"]
  day_scores = forecast_data["day_scores"]

  print(f"\n{Fore.MAGENTA}Daily Forecast for {location_name}{Style.RESET_ALL}")

  # Sort days chronologically
  for date in sorted(daily_forecasts.keys()):
    if date not in day_scores:
      continue

    daily_report = day_scores[date]
    date_str = date.strftime("%a, %d %b")

    # Use centralized rating function
    rating, color = get_rating_info(daily_report.avg_score)

    # Determine overall weather description
    precip_warning = ""
    if daily_report.avg_precip_prob is not None and daily_report.avg_precip_prob > 40:
      precip_warning = f" - {daily_report.avg_precip_prob:.0f}% rain"

    if daily_report.sunny_hours > daily_report.partly_cloudy_hours and daily_report.sunny_hours > daily_report.rainy_hours:
      weather_desc = "Sunny" + precip_warning
    elif daily_report.partly_cloudy_hours > daily_report.sunny_hours and daily_report.partly_cloudy_hours > daily_report.rainy_hours:
      weather_desc = "Partly Cloudy" + precip_warning
    elif daily_report.rainy_hours > 0:
      weather_desc = f"Rain ({daily_report.rainy_hours}h)"
    else:
      weather_desc = "Mixed" + precip_warning

    # Use min-max temperature range
    temp_str = ""
    if daily_report.min_temp is not None and daily_report.max_temp is not None:
      temp_str = f"{daily_report.min_temp:>4.1f}°C - {daily_report.max_temp:>4.1f}°C"
    else:
      temp_str = "N/A"

    # Print the day summary with color and weather description
    print(
        f"{date_str} {color}[{rating}]{Style.RESET_ALL} {temp_str} - {weather_desc}")

    if not compare_mode:
      # Sort and identify best and worst blocks
      daylight_hours = sorted([h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <=
                              h.hour <= DAYLIGHT_END_HOUR], key=lambda x: x.hour)

      if not daylight_hours:
        continue

      # Find blocks with similar weather
      weather_blocks = extract_blocks(daylight_hours)

      # Get best and worst times (highest and lowest scoring blocks)
      best_block = None
      worst_block = None
      best_score = float('-inf')
      worst_score = float('inf')

      # Identify blocks with consistently good or bad weather scores
      for block, weather_type in weather_blocks:
        if len(block) < 2:  # Skip single hour blocks
          continue

        avg_block_score = sum(
            h.total_score for h in block) / len(block)

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
        start_time = block[0].time.strftime("%H:%M")
        end_time = block[-1].time.strftime("%H:%M")
        print(
            f"  Best: {Fore.GREEN}{start_time}-{end_time}{Style.RESET_ALL}")

      # Display worst time only if it's a good day with a specific bad period
      if worst_block and daily_report.avg_score >= 0:
        block, weather_type = worst_block
        start_time = block[0].time.strftime("%H:%M")
        end_time = block[-1].time.strftime("%H:%M")
        print(
            f"  Avoid: {Fore.RED}{start_time}-{end_time}{Style.RESET_ALL}")

    # If it's the last day in compare_mode
    elif date == sorted(daily_forecasts.keys())[-1]:
      pass  # No extra blank line needed, next location's header will separate


def compare_locations(location_data, date_filter=None):
  """Compare weather conditions across multiple locations for planning purposes."""
  if not date_filter:
    date_filter = datetime.now(pytz.timezone(TIMEZONE)).date()

  date_str_formatted = date_filter.strftime('%A, %d %b')
  print(
      f"\n{Fore.MAGENTA}Location Comparison for {date_str_formatted}{Style.RESET_ALL}")

  # Get data for the specified date across all locations
  date_data = []
  for location_name, forecast in location_data.items():
    if not forecast or not forecast["day_scores"]:
      continue

    for date, daily_report in forecast["day_scores"].items():
      if date == date_filter:
        date_data.append(daily_report)
        break

  # Sort locations by score (best to worst)
  date_data.sort(key=lambda x: x.avg_score, reverse=True)

  if not date_data:
    print(f"\n{Fore.YELLOW}No data available for this date.{Style.RESET_ALL}")
    return

  # Find longest location name for proper formatting
  max_location_length = max(len(data.location_name) for data in date_data)
  location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

  # Print table header with proper spacing
  weather_col_width = 15
  print(f"\n{Fore.CYAN}{'Location':<{location_width}} {'Rating':<10} {'Temp':<15} {'Weather':<{weather_col_width}} {'Score':>6}{Style.RESET_ALL}")
  print(f"{'-' * location_width} {'-' * 10} {'-' * 15} {'-' * weather_col_width} {'-' * 6}")

  for data in date_data:
    location = data.location_name

    # Use centralized rating function
    rating, color = get_rating_info(data.avg_score)

    # Weather description
    if data.sunny_hours > data.partly_cloudy_hours and data.sunny_hours > data.rainy_hours:
      weather = "Sunny"
    elif data.partly_cloudy_hours > data.sunny_hours and data.partly_cloudy_hours > data.rainy_hours:
      weather = "Partly Cloudy"
    elif data.rainy_hours > 0:
      weather = f"Rain ({data.rainy_hours}h)"
    else:
      weather = "Mixed"

    # Temperature range
    temp = "N/A"
    if data.min_temp is not None and data.max_temp is not None:
      temp = f"{data.min_temp:.1f}°C - {data.max_temp:.1f}°C"

    # Format score
    raw_score = data.avg_score
    score_str = f"{raw_score:6.1f}"
    _, score_color = get_rating_info(raw_score)

    print(f"{Fore.LIGHTMAGENTA_EX}{location:<{location_width}}{Style.RESET_ALL} {color}{rating:<10}{Style.RESET_ALL} {temp:<15} {weather:<{weather_col_width}} {score_color}{score_str}{Style.RESET_ALL}")


def list_locations():
  """List all available locations."""
  print(f"\n{Fore.MAGENTA}Available Locations{Style.RESET_ALL}")
  for key, loc in LOCATIONS.items():
    print(f"  {key} - {Fore.LIGHTMAGENTA_EX}{loc.name}{Style.RESET_ALL}")


def display_best_times_recommendation(location_data):
  """Display a simple recommendation for when to go out this week."""
  all_periods = recommend_best_times(location_data)

  if not all_periods:
    print(
        f"\n{Fore.YELLOW}No ideal outdoor times found for this week.{Style.RESET_ALL}")
    print("Try checking individual locations for more details.")
    return

  print(f"\n{Fore.MAGENTA}Best times to go out in the next 7 days{Style.RESET_ALL}")
  print(f"\n{Fore.CYAN}Recommended Times for Next 7 Days{Style.RESET_ALL}")

  # Group periods by date
  days = {}
  for period in all_periods:
    days.setdefault(period["date"], []).append(period)

  # Extract more options per day, including those with lower scores
  filtered_periods = []
  for date, periods in sorted(days.items()):
    periods.sort(key=lambda x: x["score"], reverse=True)
    for p in periods[:5]:  # Take top 5 periods per day
      filtered_periods.append(p)

  # Find the longest location name for proper alignment
  max_location_length = max(len(
      period["location"]) for period in filtered_periods) if filtered_periods else 15
  location_width = max(max_location_length + 2, 17)  # Minimum 17 chars
  # Field width for weather + temp alignment (at least 15 for 'Partly Cloudy')
  weather_width = 20

  # Print header row
  print(f"\n{Fore.CYAN}{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{location_width}} {'Weather':<{weather_width}} {'Score':>6}{Style.RESET_ALL}")
  print(f"{'-' * 3} {'-' * 16} {'-' * 15} {'-' * 10} {'-' * location_width} {'-' * weather_width} {'-' * 6}")

  current_date = None

  for i, period in enumerate(filtered_periods, 1):
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

    weather_desc = get_weather_desc(period["dominant_symbol"])
    weather_desc = f"{weather_desc:<15}"  # Left-align, never truncate

    temp_desc = ""
    if period["avg_temp"] is not None:
      temp_desc = f"{period['avg_temp']:>5.1f}°C"  # Right-align temp

    # Combined field, temp right-aligned
    weather_with_temp = f"{weather_desc}{temp_desc:>7}"
    raw_score = period['score']
    score_str = f"{raw_score:6.1f}"
    _, score_color = get_rating_info(raw_score)

    # Print formatted row
    print(
        f"{i:<3} "
        f"{color}{day_date:<16}{Style.RESET_ALL} "
        f"{time_range:<15} "
        f"{duration_str:<10} "
        f"{Fore.LIGHTMAGENTA_EX}{period['location']:<{location_width}}{Style.RESET_ALL} "
        f"{weather_with_temp:<{weather_width}} "
        f"{score_color}{score_str}{Style.RESET_ALL}"
    )


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
  selected_locations = {args.location: LOCATIONS[args.location]} if args.location else LOCATIONS if (
      args.all or args.compare or args.recommend) else {"oviedo": LOCATIONS["oviedo"]}

  # Clear screen unless disabled
  if not args.no_clear:
    print("\033[2J\033[H")  # ANSI escape sequence to clear screen

  # Fetch and process data for all selected locations
  location_data = {}
  for loc_key, location in selected_locations.items():
    print(
        f"Fetching data for {Fore.LIGHTMAGENTA_EX}{location.name}{Style.RESET_ALL}...")
    data = fetch_weather_data(location)
    if data:
      location_data[loc_key] = process_forecast(data, location.name)
      # Add a small delay between API calls to avoid rate limiting
      time.sleep(0.5)

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
          forecast, LOCATIONS[loc_key].name, compare_mode=True)
  else:
    # Display each location's forecast in detail
    for loc_key, forecast in location_data.items():
      display_forecast(forecast, LOCATIONS[loc_key].name)


if __name__ == "__main__":
  main()
