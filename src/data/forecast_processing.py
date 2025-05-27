"""
Processes raw forecast data, extracts meaningful blocks, and generates recommendations.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, FORECAST_DAYS
from core.core_utils import get_current_date, get_timezone
from data.data_models import DailyReport, HourlyWeather
from data.scoring_utils import cloud_score, get_weather_score, precip_probability_score, temp_score, wind_score


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


def find_best_and_worst_blocks(daylight_hours: List[HourlyWeather]) -> Tuple[Optional[Tuple[List[HourlyWeather], str]], Optional[Tuple[List[HourlyWeather], str]]]:
  """Find the best and worst time blocks in a day.

  Args:
      daylight_hours: List of HourlyWeather objects for daylight hours

  Returns:
      Tuple containing (best_block_info, worst_block_info) where each is either None or
      a tuple of (hour_block, weather_type)
  """
  if not daylight_hours:
    return None, None

  weather_blocks = extract_blocks(daylight_hours)
  best_block_info = None
  worst_block_info = None
  best_score = float('-inf')
  worst_score = float('inf')

  for block, weather_type in weather_blocks:
    if len(block) < 2:
      continue

    # Calculate block score once and reuse
    avg_block_score = sum(h.total_score for h in block) / len(block)

    if avg_block_score > best_score and (weather_type in ["sunny", "cloudy"] or avg_block_score >= 0):
      best_score = avg_block_score
      best_block_info = (block, weather_type)

    if avg_block_score < worst_score and (weather_type == "rainy" or avg_block_score < 0):
      worst_score = avg_block_score
      worst_block_info = (block, weather_type)

  return best_block_info, worst_block_info


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

  all_day_blocks = []
  daily_forecasts = forecast_data["daily_forecasts"]

  # Filter for daylight hours
  for date, hours in daily_forecasts.items():
    daylight_hours = [h for h in hours if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR]
    if not daylight_hours:
      continue

    # Extract good weather blocks (with at least 2 consecutive hours)
    all_blocks = extract_blocks(daylight_hours, min_block_len=2)
    sunny_blocks = [(block, date) for block, block_type in all_blocks if block_type == "sunny"]

    if sunny_blocks:
      all_day_blocks.extend(sunny_blocks)

  # Calculate score for each block and sort
  block_scores = []
  for block, date in all_day_blocks:
    avg_score = sum(h.total_score for h in block) / len(block)
    start_time = min(h.time for h in block)
    end_time = max(h.time for h in block)
    duration = (end_time.hour - start_time.hour) + 1  # Include both start and end hour

    # Find dominant symbol
    symbol_counts: Dict[str, int] = defaultdict(int)
    for hour in block:
      if hour.symbol:
        symbol_counts[hour.symbol] += 1

    # Find dominant symbol safely
    dominant_symbol = ""
    if symbol_counts:
      dominant_symbol = max(symbol_counts.items(), key=lambda x: x[1])[0]

    # Calculate temperature average
    avg_temp = sum(h.temp for h in block if h.temp is not None) / \
        len([h for h in block if h.temp is not None]) if any(h.temp is not None for h in block) else None

    # Calculate penalty for shorter blocks
    duration_factor = min(1.0, duration / 4)  # Normalize to max 1.0
    final_score = avg_score * duration_factor

    block_scores.append({
      "location": location_name_key,
      "date": date,
      "start_time": start_time,
      "end_time": end_time,
      "duration": duration,
      "avg_score": avg_score,
      "final_score": final_score,
      "block": block,
      "dominant_symbol": dominant_symbol,
      "avg_temp": avg_temp
    })

  # Sort by score (descending)
  sorted_blocks = sorted(block_scores, key=lambda x: x["final_score"], reverse=True)
  return sorted_blocks[:5]  # Return top 5 blocks


def recommend_best_times(all_location_processed_data):
  """Find the best times to go out across all locations.

  Args:
      all_location_processed_data: Dictionary of location -> processed forecast data

  Returns:
      List of recommendations grouped by date
  """
  all_blocks = []

  # Extract best blocks for each location
  for loc_key, forecast_data in all_location_processed_data.items():
    location_blocks = extract_best_blocks(forecast_data, loc_key)
    all_blocks.extend(location_blocks)

  # Group blocks by date
  blocks_by_date = {}
  for block in all_blocks:
    date_key = block["date"]
    if date_key not in blocks_by_date:
      blocks_by_date[date_key] = []
    blocks_by_date[date_key].append(block)

  # Get today and the next 2 days
  today = get_current_date()
  target_dates = [today, today + timedelta(days=1), today + timedelta(days=2)]

  # Get the top 5 blocks for each target date
  final_recommendations = []

  for target_date in target_dates:
    if target_date in blocks_by_date:
      # Sort blocks for this date by score (descending)
      date_blocks = blocks_by_date[target_date]
      sorted_blocks = sorted(date_blocks, key=lambda x: x["final_score"], reverse=True)

      # Take the top 5 blocks for this date
      top_blocks = sorted_blocks[:5]
      for block in top_blocks:
        final_recommendations.append(block)

  return final_recommendations
