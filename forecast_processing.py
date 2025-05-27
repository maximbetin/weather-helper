"""
Processes raw forecast data, extracts meaningful blocks, and generates recommendations.
"""

from collections import defaultdict
from datetime import datetime, timedelta

import pytz

from config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, FORECAST_DAYS, TIMEZONE
from core_utils import get_timezone
from data_models import DailyReport, HourlyWeather
from display_core import get_location_display_name
from scoring_utils import cloud_score, get_weather_score, precip_probability_score, temp_score, wind_score


def extract_base_symbol(symbol_code):
  """Extract the base symbol from a symbol code.

  Args:
      symbol_code: The full symbol code (e.g., 'partlycloudy_day')

  Returns:
      str: Base symbol without time of day suffix
  """
  if not symbol_code:
    return "unknown"

  return symbol_code.split('_')[0] if '_' in symbol_code else symbol_code


def calculate_block_statistics(block_list):
  """Calculate statistics for a block of hours.

  Args:
      block_list: List of HourlyWeather objects in the block

  Returns:
      dict: Dictionary containing statistics for the block
  """
  # Calculate average temperature for the block
  temps_in_block = [h.temp for h in block_list if isinstance(h.temp, (int, float))]
  avg_temp_val = sum(temps_in_block) / len(temps_in_block) if temps_in_block else None

  # Find dominant weather symbol
  symbols_in_block = [h.symbol for h in block_list if isinstance(h.symbol, str)]
  symbol_counts = defaultdict(int)
  for s in symbols_in_block:
    symbol_counts[s] += 1
  dominant_sym_str = max(symbol_counts, key=lambda k: symbol_counts[k]) if symbol_counts else ""

  # Calculate average score
  avg_block_score = sum(h.total_score for h in block_list) / len(block_list)

  return {
    "avg_temp": avg_temp_val,
    "dominant_symbol": dominant_sym_str,
    "avg_score": avg_block_score
  }


def get_block_type(hour_obj):
  """Determine weather block type from hour object.

  Args:
      hour_obj: HourlyWeather object

  Returns:
      str: Weather type ("sunny", "rainy", or "cloudy")
  """
  s = hour_obj.symbol  # symbol is already base form
  if s in ("clearsky", "fair"):
    return "sunny"
  if "rain" in s:
    return "rainy"
  return "cloudy"


def extract_blocks(hours, min_block_len=2):
  """Find consecutive blocks of hours with similar weather type.

  Args:
      hours: List of HourlyWeather objects
      min_block_len: Minimum number of hours to consider a block

  Returns:
      List of (hour_block, weather_type) tuples
  """
  if not hours:
    return []

  # Ensure hours are HourlyWeather objects and sorted
  sorted_hours = sorted(hours, key=lambda x: x.time)  # Sort by full datetime
  blocks = []
  current_block = [sorted_hours[0]]

  current_type = get_block_type(sorted_hours[0])
  for hour_obj in sorted_hours[1:]:
    hour_type = get_block_type(hour_obj)
    # Check for consecutive hours (time difference of 1 hour)
    if hour_type == current_type and (hour_obj.time - current_block[-1].time) == timedelta(hours=1):
      current_block.append(hour_obj)
    else:
      if len(current_block) >= min_block_len:
        blocks.append((current_block, current_type))
      current_block = [hour_obj]
      current_type = hour_type

  # Don't forget the last block
  if len(current_block) >= min_block_len:
    blocks.append((current_block, current_type))

  return blocks


def process_forecast(forecast_data, location_name):
  """Process weather forecast data into daily summaries."""
  if not forecast_data or 'properties' not in forecast_data or 'timeseries' not in forecast_data['properties']:
    return None

  forecast_timeseries = forecast_data['properties']['timeseries']
  madrid_tz = get_timezone()
  daily_forecasts = defaultdict(list)
  today = datetime.now(madrid_tz).date()
  end_date = today + timedelta(days=FORECAST_DAYS)

  for entry in forecast_timeseries:
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    local_time = time_utc.astimezone(madrid_tz)
    forecast_date = local_time.date()

    if not (today <= forecast_date < end_date):
      continue

    instant_details = entry["data"]["instant"]["details"]
    temp = instant_details.get("air_temperature")
    wind = instant_details.get("wind_speed")
    humidity = instant_details.get("relative_humidity")
    cloud_coverage = instant_details.get("cloud_area_fraction")
    fog = instant_details.get("fog_area_fraction")
    wind_direction = instant_details.get("wind_from_direction")
    wind_gust = instant_details.get("wind_speed_of_gust")

    next_1h = entry["data"].get("next_1_hours", {})
    next_1h_details = next_1h.get("details", {})
    precipitation_1h = next_1h_details.get("precipitation_amount")
    precipitation_prob_1h = next_1h_details.get("probability_of_precipitation")

    next_6h = entry["data"].get("next_6_hours", {})
    next_6h_details = next_6h.get("details", {})
    precipitation_prob_6h = next_6h_details.get("probability_of_precipitation")

    precipitation_prob = precipitation_prob_1h if precipitation_prob_1h is not None else precipitation_prob_6h
    final_precipitation_amount = precipitation_1h  # Prefer 1h amount
    if final_precipitation_amount is None and next_6h_details:
      final_precipitation_amount = next_6h_details.get("precipitation_amount")

    symbol_code = next_1h.get("summary", {}).get("symbol_code")
    if not symbol_code and next_6h.get("summary"):
      symbol_code = next_6h["summary"].get("symbol_code")

    base_symbol = extract_base_symbol(symbol_code)

    hourly_weather = HourlyWeather(
        time=local_time,
        temp=temp,
        wind=wind,
        humidity=humidity,
        cloud_coverage=cloud_coverage,
        fog=fog,
        wind_direction=wind_direction,
        wind_gust=wind_gust,
        precipitation_amount=final_precipitation_amount,
        precipitation_probability=precipitation_prob,
        symbol=base_symbol,
        weather_score=get_weather_score(base_symbol),
        temp_score=temp_score(temp),
        wind_score=wind_score(wind),
        cloud_score=cloud_score(cloud_coverage),
        precip_prob_score=precip_probability_score(precipitation_prob)
    )
    daily_forecasts[forecast_date].append(hourly_weather)

  day_scores_reports = {}
  for date, hours_list in daily_forecasts.items():
    daylight_h = [h for h in hours_list if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR]
    if not daylight_h:  # Skip if no daylight hours data for the day
      continue
    day_report = DailyReport(date, daylight_h, location_name)
    day_scores_reports[date] = day_report

  return {
      "daily_forecasts": daily_forecasts,  # dict of date -> list of HourlyWeather
      "day_scores": day_scores_reports    # dict of date -> DailyReport
  }


def extract_best_blocks(forecast_data, location_name_key):
  """Extract best time blocks from forecast data for a specific location."""
  if not forecast_data or "daily_forecasts" not in forecast_data or "day_scores" not in forecast_data:
    return []

  extracted_blocks = []
  day_scores_map = forecast_data["day_scores"]
  location_display_name = get_location_display_name(location_name_key)

  for date, daily_report_obj in day_scores_map.items():
    if daily_report_obj.avg_score < -8:  # Skip days with very poor scores
      continue

    # Use the daylight hours already available in the daily_report_obj
    daylight_hours_list = sorted(daily_report_obj.daylight_hours, key=lambda x: x.time)

    if not daylight_hours_list:
      continue

    weather_blocks_tuples = extract_blocks(daylight_hours_list, min_block_len=2)

    best_block_for_day = None
    best_score_for_day = float('-inf')

    for block_list, weather_type_str in weather_blocks_tuples:
      avg_block_score = sum(h.total_score for h in block_list) / len(block_list)

      if avg_block_score > best_score_for_day:
        best_score_for_day = avg_block_score
        best_block_for_day = (block_list, weather_type_str)

    if best_block_for_day:
      block_list, weather_type_str = best_block_for_day
      start_time_dt = block_list[0].time
      end_time_dt = block_list[-1].time

      # Get statistics for the block
      block_stats = calculate_block_statistics(block_list)

      period_dict = {
          "location": location_display_name,
          "date": date,
          "day_name": date.strftime("%A"),
          "start_time": start_time_dt,
          "end_time": end_time_dt,
          "duration": len(block_list),
          "score": block_stats["avg_score"],
          "weather_type": weather_type_str,
          "avg_temp": block_stats["avg_temp"],
          "dominant_symbol": block_stats["dominant_symbol"]
      }
      extracted_blocks.append(period_dict)

  return extracted_blocks


def recommend_best_times(all_location_processed_data):
  """Analyze forecast data and recommend the best times to go out this week."""
  madrid_tz = pytz.timezone(TIMEZONE)
  today = datetime.now(madrid_tz).date()
  end_date = today + timedelta(days=FORECAST_DAYS)
  all_periods = []

  # Extract best blocks for each location
  for location_name_key, forecast_data in all_location_processed_data.items():
    if not forecast_data:
      continue
    best_blocks = extract_best_blocks(forecast_data, location_name_key)
    all_periods.extend(best_blocks)

  # If no periods found, use a more lenient approach with lower thresholds
  if not all_periods:
    for location_name_key, forecast_data in all_location_processed_data.items():
      if not forecast_data or not forecast_data.get("day_scores"):
        continue

      location_display_name = get_location_display_name(location_name_key)

      for date_val, daily_report in sorted(forecast_data["day_scores"].items()):
        if date_val < today or date_val >= end_date or daily_report.avg_score < -15:
          continue

        daylight_hours = sorted(daily_report.daylight_hours, key=lambda x: x.hour)
        if not daylight_hours:
          continue

        weather_block_tuples = extract_blocks(daylight_hours, min_block_len=2)
        extremely_bad_weather = ["heavyrain", "heavyrainshowers", "thunderstorm"]
        block_threshold = -10  # Very low threshold

        for block, weather_type in weather_block_tuples:
          if len(block) < 2:  # Skip single hour blocks
            continue

          # Calculate block statistics
          block_stats = calculate_block_statistics(block)
          avg_block_score = block_stats["avg_score"]

          # Skip blocks with extremely bad weather
          if (avg_block_score < block_threshold or
              any(bad in block[0].symbol for bad in extremely_bad_weather
                  if isinstance(block[0].symbol, str))):
            continue

          # Create period dictionary
          start_time = block[0].time
          end_time = block[-1].time

          period = {
              "location": location_display_name,
              "date": date_val,
              "day_name": date_val.strftime("%A"),
              "start_time": start_time,
              "end_time": end_time,
              "duration": len(block),
              "score": avg_block_score,
              "weather_type": weather_type,
              "avg_temp": block_stats["avg_temp"],
              "dominant_symbol": block_stats["dominant_symbol"]
          }
          all_periods.append(period)

  # Sort all periods by date and then by score (highest first)
  all_periods.sort(key=lambda x: (x["date"], -x["score"]))

  return all_periods
