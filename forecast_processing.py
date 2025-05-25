"""
Processes raw forecast data, extracts meaningful blocks, and generates recommendations.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import pytz

from config import TIMEZONE, DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR, FORECAST_DAYS
from data_models import HourlyWeather, DailyReport
from scoring_utils import (
    get_weather_score, temp_score, wind_score, cloud_score, precip_probability_score
)
from locations import LOCATIONS  # For display names in recommendations


def extract_blocks(hours, min_block_len=2):
  """Find consecutive blocks of hours with similar weather type."""
  if not hours:
    return []
  # Ensure hours are HourlyWeather objects and sorted
  # The original sort key was x.hour, assuming hours were already HourlyWeather objects
  sorted_hours = sorted(hours, key=lambda x: x.time)  # Sort by full datetime to be safe
  blocks = []
  current_block = [sorted_hours[0]]

  def block_type(h):
    s = h.symbol  # symbol is already base form
    if s in ("clearsky", "fair"):
      return "sunny"
    if "rain" in s:
      return "rainy"
    return "cloudy"

  current_type = block_type(sorted_hours[0])
  for hour_obj in sorted_hours[1:]:
    hour_type = block_type(hour_obj)
    # Check for consecutive hours (time difference of 1 hour)
    if hour_type == current_type and (hour_obj.time - current_block[-1].time) == timedelta(hours=1):
      current_block.append(hour_obj)
    else:
      if len(current_block) >= min_block_len:
        blocks.append((current_block, current_type))
      current_block = [hour_obj]
      current_type = hour_type
  if len(current_block) >= min_block_len:
    blocks.append((current_block, current_type))
  return blocks


def process_forecast(forecast_data, location_name):
  """Process weather forecast data into daily summaries."""
  if not forecast_data or 'properties' not in forecast_data or 'timeseries' not in forecast_data['properties']:
    return None

  forecast_timeseries = forecast_data['properties']['timeseries']
  madrid_tz = pytz.timezone(TIMEZONE)
  daily_forecasts = defaultdict(list)
  today = datetime.now(madrid_tz).date()
  # Ensure end_date calculation uses FORECAST_DAYS from config
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
    # precipitation_6h = next_6h_details.get("precipitation_amount") # Not directly used for HourlyWeather if 1h exists
    precipitation_prob_6h = next_6h_details.get("probability_of_precipitation")

    precipitation_prob = precipitation_prob_1h if precipitation_prob_1h is not None else precipitation_prob_6h
    final_precipitation_amount = precipitation_1h  # Prefer 1h amount
    if final_precipitation_amount is None and next_6h_details:
      final_precipitation_amount = next_6h_details.get("precipitation_amount")

    symbol_code = next_1h.get("summary", {}).get("symbol_code")
    if not symbol_code and next_6h.get("summary"):
      symbol_code = next_6h["summary"].get("symbol_code")
    if not symbol_code:
      symbol_code = "unknown"  # Default if no symbol found

    base_symbol = symbol_code.split('_')[0] if '_' in symbol_code else symbol_code

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
      # Create an empty/default DailyReport if you always want an entry for the day
      # day_scores_reports[date] = DailyReport(date, [], location_name)
      continue
    day_report = DailyReport(date, daylight_h, location_name)
    day_scores_reports[date] = day_report

  return {
      "daily_forecasts": daily_forecasts,  # dict of date -> list of HourlyWeather
      "day_scores": day_scores_reports    # dict of date -> DailyReport
  }


def extract_best_blocks(forecast_data, location_name_key):
  """Extract best time blocks from forecast data for a specific location."""
  # Assumes forecast_data is the output of process_forecast
  if not forecast_data or "daily_forecasts" not in forecast_data or "day_scores" not in forecast_data:
    return []

  extracted_blocks = []
  daily_forecasts_map = forecast_data["daily_forecasts"]
  day_scores_map = forecast_data["day_scores"]
  location_display_name = LOCATIONS[location_name_key].name

  for date, daily_report_obj in day_scores_map.items():
    if daily_report_obj.avg_score < -8:  # Skip days with very poor scores
      continue

    # Get daylight hours from the already processed daily_forecasts_map
    # These are already HourlyWeather objects
    daylight_hours_list = sorted(
        [h for h in daily_forecasts_map.get(date, []) if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
        key=lambda x: x.time  # Sort by time for extract_blocks
    )

    if not daylight_hours_list:
      continue

    weather_blocks_tuples = extract_blocks(daylight_hours_list, min_block_len=2)

    best_block_for_day = None
    best_score_for_day = float('-inf')

    for block_list, weather_type_str in weather_blocks_tuples:
      # block_list is a list of HourlyWeather objects
      avg_block_score = sum(h.total_score for h in block_list) / len(block_list)

      if avg_block_score > best_score_for_day:
        best_score_for_day = avg_block_score
        best_block_for_day = (block_list, weather_type_str)

    if best_block_for_day:
      block_list, weather_type_str = best_block_for_day
      start_time_dt = block_list[0].time
      end_time_dt = block_list[-1].time
      temps_in_block = [h.temp for h in block_list if isinstance(h.temp, (int, float))]
      avg_temp_val = sum(temps_in_block) / len(temps_in_block) if temps_in_block else None

      symbols_in_block = [h.symbol for h in block_list if isinstance(h.symbol, str)]
      symbol_counts = defaultdict(int)
      for s in symbols_in_block:
        symbol_counts[s] += 1
      dominant_sym_str = max(symbol_counts, key=lambda k: symbol_counts[k]) if symbol_counts else ""

      period_dict = {
          "location": location_display_name,
          "date": date,
          "day_name": date.strftime("%A"),
          "start_time": start_time_dt,
          "end_time": end_time_dt,
          "duration": len(block_list),
          "score": best_score_for_day,  # This is avg_block_score of the best block
          "weather_type": weather_type_str,
          "avg_temp": avg_temp_val,
          "dominant_symbol": dominant_sym_str
      }
      extracted_blocks.append(period_dict)

  return extracted_blocks


def recommend_best_times(all_location_processed_data):
  """Analyze forecast data across all locations and recommend best times.
  all_location_processed_data: dict where key is loc_key, value is output of process_forecast
  """
  madrid_tz = pytz.timezone(TIMEZONE)
  today = datetime.now(madrid_tz).date()
  end_date = today + timedelta(days=FORECAST_DAYS)

  all_potential_periods = []

  # Primary strategy: Use extract_best_blocks for each location
  for loc_key, processed_forecast in all_location_processed_data.items():
    if not processed_forecast:
      continue
    # location_name_key for extract_best_blocks should be the key e.g. "gijon"
    best_blocks_for_loc = extract_best_blocks(processed_forecast, loc_key)
    all_potential_periods.extend(best_blocks_for_loc)

  # Fallback strategy if primary yields nothing
  if not all_potential_periods:
    fallback_periods = []
    for loc_key, processed_forecast in all_location_processed_data.items():
      if not processed_forecast or not processed_forecast.get("day_scores"):
        continue

      loc_disp_name = LOCATIONS[loc_key].name
      daily_scores_map = processed_forecast["day_scores"]
      daily_forecasts_map = processed_forecast["daily_forecasts"]

      for date_val, daily_report_obj in sorted(daily_scores_map.items()):
        if not (today <= date_val < end_date):
          continue
        if daily_report_obj.avg_score < -15:  # Lenient day threshold for fallback
          continue

        hourly_weather_list_for_day = daily_forecasts_map.get(date_val, [])
        daylight_h_list = sorted(
            [h_obj for h_obj in hourly_weather_list_for_day if DAYLIGHT_START_HOUR <= h_obj.hour <= DAYLIGHT_END_HOUR],
            key=lambda x_obj: x_obj.time
        )

        if not daylight_h_list:
          continue

        weather_block_tuples = extract_blocks(daylight_h_list, min_block_len=2)

        for block_list, weather_tp_str in weather_block_tuples:
          avg_blk_score = sum(h_obj.total_score for h_obj in block_list) / len(block_list)
          block_thresh = -10  # Lenient block threshold

          # Check for extremely bad weather symbols in the first hour of the block
          # Symbol in HourlyWeather is already the base symbol
          first_hour_symbol = block_list[0].symbol if block_list and isinstance(block_list[0].symbol, str) else ""
          extremely_bad_w = ["heavyrain", "heavyrainshowers", "thunderstorm"]

          if avg_blk_score >= block_thresh and not any(bad_w_sym in first_hour_symbol for bad_w_sym in extremely_bad_w):
            start_t_dt = block_list[0].time
            end_t_dt = block_list[-1].time
            temps_in_blk = [h.temp for h in block_list if isinstance(h.temp, (int, float))]
            avg_t_val = sum(temps_in_blk) / len(temps_in_blk) if temps_in_blk else None

            symbols_in_blk = [h.symbol for h in block_list if isinstance(h.symbol, str)]
            sym_counts = defaultdict(int)
            for s in symbols_in_blk:
              sym_counts[s] += 1
            dom_sym_str = max(sym_counts, key=lambda k: sym_counts[k]) if sym_counts else ""

            period_data_dict = {
                "location": loc_disp_name,
                "date": date_val,
                "day_name": date_val.strftime("%A"),
                "start_time": start_t_dt,
                "end_time": end_t_dt,
                "duration": len(block_list),
                "score": avg_blk_score,
                "weather_type": weather_tp_str,
                "avg_temp": avg_t_val,
                "dominant_symbol": dom_sym_str
            }
            fallback_periods.append(period_data_dict)
    all_potential_periods.extend(fallback_periods)

  # Sort all collected periods by date and then by score (descending)
  all_potential_periods.sort(key=lambda x: (x["date"], -x["score"]))
  return all_potential_periods
