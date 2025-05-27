"""
Functions for displaying weather forecasts.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

import colors
from colors import get_rating_info
from core_utils import (
    get_current_datetime, format_time, format_date,
    get_weather_desc, is_value_valid, get_weather_description_from_counts
)
from display_core import (
    display_heading, display_temperature, display_wind,
    display_precipitation_probability, display_table_header,
    display_warning, get_location_display_name
)
from config import DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR
from forecast_processing import extract_blocks


def display_hourly_forecast(forecast_data: Dict[str, Any], location_name: str) -> None:
  """Display hourly weather forecast for a location for the current day.

  Args:
      forecast_data: Processed forecast data
      location_name: Name of the location
  """
  if not forecast_data:
    return

  daily_forecasts = forecast_data["daily_forecasts"]

  display_heading(f"Hourly Forecast for {location_name}")

  # Get today's date
  today = get_current_datetime().date()

  if today not in daily_forecasts:
    display_warning("No hourly data available for today.")
    return

  # Get today's hours
  hours = sorted([h for h in daily_forecasts[today]], key=lambda x: x.hour)

  if not hours:
    display_warning("No hourly data available for today.")
    return

  # Get current hour
  current_hour = get_current_datetime().hour

  # Print table header
  headers = ["Time", "Weather", "Temp", "Wind", "Rain %", "Score"]
  widths = [8, 15, 8, 8, 8, 6]
  display_table_header(headers, widths)

  # Print hourly data, starting from current hour
  for hour in [h for h in hours if h.hour >= current_hour]:
    time_str = format_time(hour.time)

    # Weather description
    weather_desc = get_weather_desc(hour.symbol)

    # Temperature
    temp_str = display_temperature(hour.temp)

    # Wind
    wind_str = display_wind(hour.wind)

    # Precipitation probability
    precip_prob_str = display_precipitation_probability(hour.precipitation_probability)

    # Score
    rating, color = get_rating_info(hour.total_score)
    score_str = f"{hour.total_score:6.1f}"

    print(f"{time_str:<8} {weather_desc:<15} {temp_str:<8} {wind_str:<8} {precip_prob_str:<8} {color}{score_str}{colors.RESET}")


def display_forecast(processed_forecast_data: Dict[str, Any], location_display_name: str, compare_mode: bool = False) -> None:
  """Display weather forecast for a location.

  Args:
      processed_forecast_data: The output from process_forecast()
      location_display_name: The display name of the location (e.g., "Gijón")
      compare_mode: Boolean, if True, adjusts output for comparison view
  """
  if not processed_forecast_data:
    display_warning(f"No forecast data to display for {location_display_name}.")
    return

  # daily_forecasts: dict of date -> list of HourlyWeather
  # day_scores: dict of date -> DailyReport
  daily_forecasts = processed_forecast_data.get("daily_forecasts", {})
  day_scores = processed_forecast_data.get("day_scores", {})

  display_heading(f"Daily Forecast for {location_display_name}")

  # Sort days chronologically
  for date_obj in sorted(daily_forecasts.keys()):
    if date_obj not in day_scores:
      continue  # Should not happen if process_forecast is consistent

    daily_report = day_scores[date_obj]  # This is a DailyReport object
    date_str = format_date(date_obj)

    rating, color = get_rating_info(daily_report.avg_score)

    # Determine overall weather description based on DailyReport stats
    weather_desc_display = get_weather_description_from_counts(
        daily_report.sunny_hours,
        daily_report.partly_cloudy_hours,
        daily_report.rainy_hours,
        daily_report.avg_precip_prob
    )

    temp_str = "N/A"
    if daily_report.min_temp is not None and daily_report.max_temp is not None:
      temp_str = f"{daily_report.min_temp:>4.1f}°C - {daily_report.max_temp:>4.1f}°C"

    print(f"{date_str} {color}[{rating}]{colors.RESET} {temp_str} - {weather_desc_display}")

    if not compare_mode:
      # Get daylight HourlyWeather objects for this date
      daylight_hourly_weather = sorted(
          [h for h in daily_forecasts.get(date_obj, []) if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
          key=lambda x: x.time
      )
      if not daylight_hourly_weather:
        continue

      weather_blocks = extract_blocks(daylight_hourly_weather)
      best_block_info = None
      worst_block_info = None
      best_score = float('-inf')
      worst_score = float('inf')

      for block, weather_type in weather_blocks:
        if len(block) < 2:
          continue
        avg_block_score = sum(h.total_score for h in block) / len(block)

        if avg_block_score > best_score and (weather_type in ["sunny", "cloudy"] or avg_block_score >= 0):
          best_score = avg_block_score
          best_block_info = (block, weather_type)

        if avg_block_score < worst_score and (weather_type == "rainy" or avg_block_score < 0):
          worst_score = avg_block_score
          worst_block_info = (block, weather_type)

      if best_block_info:
        block, _ = best_block_info
        start_t = format_time(block[0].time)
        end_t = format_time(block[-1].time)
        print(f"  Best: {colors.SUCCESS}{start_t}-{end_t}{colors.RESET}")

      if worst_block_info and daily_report.avg_score >= 0:  # Only show avoid if day is generally good
        block, _ = worst_block_info
        start_t = format_time(block[0].time)
        end_t = format_time(block[-1].time)
        print(f"  Avoid: {colors.ERROR}{start_t}-{end_t}{colors.RESET}")
