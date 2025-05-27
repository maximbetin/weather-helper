"""
Functions for displaying weather forecasts.
"""

from typing import Any, Dict

from core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR
from core.core_utils import format_date, format_time, get_current_datetime, get_weather_desc, is_value_valid
from data.forecast_processing import find_best_and_worst_blocks
from display.colors import EMPHASIS, ERROR, INFO, SUCCESS, colorize, get_rating_info
from display.display_core import _format_column, display_temperature, display_warning


def display_hourly_forecast(forecast_data: Dict[str, Any], location_name: str) -> None:
  """Display hourly weather forecast for a location for the current day.

  Args:
      forecast_data: Processed forecast data
      location_name: Name of the location
  """
  if not forecast_data:
    return

  daily_forecasts = forecast_data["daily_forecasts"]

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

  # Get daily report and rating for consistent coloring
  day_scores = forecast_data.get("day_scores", {})
  if today in day_scores:
    daily_report = day_scores[today]
    _, location_color = get_rating_info(daily_report.avg_score)
  else:
    location_color = EMPHASIS

  # Print location name as heading
  print(colorize(f"{location_name}", location_color))

  # Define column widths for consistent alignment - omit rank for default view
  time_width = 8
  rating_width = 18
  temp_width = 14
  weather_width = 24

  # Print table headers using _format_column for consistent alignment - omitting Rank
  time_header = _format_column(colorize("Time", INFO), time_width)
  rating_header = _format_column(colorize("Rating", INFO), rating_width)
  temp_header = _format_column(colorize("Temperature", INFO), temp_width)
  weather_header = _format_column(colorize("Weather", INFO), weather_width)

  print(f"  {time_header} {rating_header} {temp_header} {weather_header}")
  print(f"  {'-' * time_width} {'-' * rating_width} {'-' * temp_width} {'-' * weather_width}")

  # Print hourly data, starting from current hour and ending at 21:00 (9 PM)
  filtered_hours = [h for h in hours if h.hour >= current_hour and h.hour <= 21]

  for hour in filtered_hours:
    time_str = format_time(hour.time)

    # Weather description
    weather_desc = get_weather_desc(hour.symbol)

    # Add rain probability if available
    if is_value_valid(hour.precipitation_probability) and hour.precipitation_probability > 0:
      weather_desc += f" ({hour.precipitation_probability:.0f}%)"

    # Temperature
    temp_str = display_temperature(hour.temp)

    # Score and rating
    rating, color = get_rating_info(hour.total_score)
    score_formatted = f"{hour.total_score:.1f}"
    rating_score = f"[{rating} - {score_formatted}]"

    # Format columns with proper alignment and color - omitting rank column
    time_col = _format_column(colorize(time_str, color), time_width)
    rating_col = _format_column(colorize(rating_score, color), rating_width)
    temp_col = _format_column(temp_str, temp_width)
    weather_col = _format_column(weather_desc, weather_width)

    print(f"  {time_col} {rating_col} {temp_col} {weather_col}")


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

  # Define column widths for consistent alignment - omit rank for default view
  date_width = 14
  rating_width = 18
  temp_width = 20  # Increased to accommodate expanded temperature format
  weather_width = 24

  # Get first day's score for location coloring if available
  if daily_forecasts:
    first_date = sorted(daily_forecasts.keys())[0] if daily_forecasts else None
    if first_date and first_date in day_scores:
      daily_report = day_scores[first_date]
      _, location_color = get_rating_info(daily_report.avg_score)
    else:
      location_color = EMPHASIS
  else:
    location_color = EMPHASIS

  # Print location name as heading
  print(colorize(f"{location_display_name}", location_color))

  # Print table headers using _format_column for consistent alignment - omitting Rank and Time Range for weekly view
  date_header = _format_column(colorize("Date", INFO), date_width)
  rating_header = _format_column(colorize("Rating", INFO), rating_width)
  temp_header = _format_column(colorize("Temperature", INFO), temp_width)
  weather_header = _format_column(colorize("Weather", INFO), weather_width)

  print(f"  {date_header} {rating_header} {temp_header} {weather_header}")
  print(f"  {'-' * date_width} {'-' * rating_width} {'-' * temp_width} {'-' * weather_width}")

  # Sort days chronologically
  for i, date_obj in enumerate(sorted(daily_forecasts.keys())):
    if date_obj not in day_scores:
      continue  # Should not happen if process_forecast is consistent

    daily_report = day_scores[date_obj]  # This is a DailyReport object
    date_str = format_date(date_obj)

    score = daily_report.avg_score
    rating, color = get_rating_info(score)
    score_formatted = f"{score:.1f}"
    rating_score = f"[{rating} - {score_formatted}]"

    # Use the weather_description property directly from DailyReport
    weather_desc_display = daily_report.weather_description

    # Add rain probability if available
    if is_value_valid(daily_report.avg_precip_prob) and daily_report.avg_precip_prob > 0:
      weather_desc_display += f" ({daily_report.avg_precip_prob:.0f}%)"

    # Format temperature - simplified to min-max with space
    temp_str = "N/A"
    if daily_report.min_temp is not None and daily_report.max_temp is not None:
      temp_str = f"{daily_report.min_temp:.1f}°C - {daily_report.max_temp:.1f}°C"

    # Format columns with proper alignment and color - omitting rank column
    date_col = _format_column(colorize(date_str, color), date_width)
    rating_col = _format_column(colorize(rating_score, color), rating_width)
    temp_col = _format_column(temp_str, temp_width)
    weather_col = _format_column(weather_desc_display, weather_width)

    # Print row without the rank and time range columns for weekly view
    print(f"  {date_col} {rating_col} {temp_col} {weather_col}")

    if not compare_mode:
      # Get daylight HourlyWeather objects for this date
      daylight_hourly_weather = sorted(
          [h for h in daily_forecasts.get(date_obj, []) if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
          key=lambda x: x.time
      )
      if not daylight_hourly_weather:
        continue

      # Use the consolidated function to find best and worst blocks
      best_block_info, worst_block_info = find_best_and_worst_blocks(daylight_hourly_weather)

      if best_block_info:
        block, _ = best_block_info
        start_t = format_time(block[0].time)
        end_t = format_time(block[-1].time)
        print(f"    Best time: {colorize(f'{start_t}-{end_t}', SUCCESS)}")

      if worst_block_info and daily_report.avg_score >= 0:  # Only show avoid if day is generally good
        block, _ = worst_block_info
        start_t = format_time(block[0].time)
        end_t = format_time(block[-1].time)
        print(f"    Avoid: {colorize(f'{start_t}-{end_t}', ERROR)}")
