"""
Evaluation and scoring logic for weather forecasts.
Provides functions to process forecasts, evaluate time blocks, and rank locations for GUI use.
"""

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional

from src.core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, FORECAST_DAYS
from src.core.daily_report import DailyReport
from src.core.hourly_weather import HourlyWeather
from src.utils.misc import (
    get_weather_score,
    temp_score,
    wind_score,
    cloud_score,
    precip_probability_score,
    extract_base_symbol
)


def process_forecast(forecast_data: dict, location_name: str) -> Optional[dict]:
  """Process weather forecast data into daily summaries and hourly blocks."""
  if not forecast_data or 'properties' not in forecast_data or 'timeseries' not in forecast_data['properties']:
    return None

  forecast_timeseries = forecast_data['properties']['timeseries']
  daily_forecasts = defaultdict(list)
  today = datetime.now().date()
  end_date = today + timedelta(days=FORECAST_DAYS)

  for entry in forecast_timeseries:
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    local_time = time_utc  # Assume already local or adjust as needed
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
    final_precipitation_amount = precipitation_1h
    if final_precipitation_amount is None and next_6h_details:
      final_precipitation_amount = next_6h_details.get("precipitation_amount")
    symbol_code = next_1h.get("summary", {}).get("symbol_code")
    if not symbol_code and next_6h.get("summary"):
      symbol_code = next_6h["summary"].get("symbol_code")
    base_symbol = extract_base_symbol(symbol_code) if symbol_code else ""
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
    if not daylight_h:
      continue
    day_report = DailyReport(date, daylight_h, location_name)
    day_scores_reports[date] = day_report
  return {
      "daily_forecasts": daily_forecasts,
      "day_scores": day_scores_reports
  }


def get_available_dates(processed_forecast: dict) -> List[date]:
  """Return all available dates for a processed forecast."""
  if not processed_forecast or "daily_forecasts" not in processed_forecast:
    return []
  return sorted(processed_forecast["daily_forecasts"].keys())


def get_time_blocks_for_date(processed_forecast: dict, d: date) -> List[HourlyWeather]:
  """Return all HourlyWeather blocks for a given date."""
  if not processed_forecast or "daily_forecasts" not in processed_forecast:
    return []
  return sorted(processed_forecast["daily_forecasts"].get(d, []), key=lambda h: h.hour)


def get_top_locations_for_date(all_location_processed: Dict[str, dict], d: date, top_n: int = 5) -> List[dict]:
  """Return the top N locations for a given date, sorted by daily score."""
  results = []
  for loc_key, processed in all_location_processed.items():
    day_scores = processed.get("day_scores", {})
    if d in day_scores:
      report = day_scores[d]
      results.append({
          "location_key": loc_key,
          "location_name": getattr(report, "location_name", loc_key),
          "avg_score": getattr(report, "avg_score", 0),
          "min_temp": getattr(report, "min_temp", None),
          "max_temp": getattr(report, "max_temp", None),
          "weather_description": getattr(report, "weather_description", "")
      })
  results.sort(key=lambda x: x["avg_score"], reverse=True)
  return results[:top_n]
