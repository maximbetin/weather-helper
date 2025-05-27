"""
Functions for displaying weather forecasts.
"""

from typing import Any, Dict

from core.core_utils import format_time, get_current_datetime, get_weather_desc, is_value_valid
from display.colors import INFO, LIGHTMAGENTA, colorize, get_rating_info
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
    location_color = LIGHTMAGENTA

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
