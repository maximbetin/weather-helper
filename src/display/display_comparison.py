"""
Functions for comparing and recommending locations based on weather forecasts.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from core.core_utils import format_date, get_current_date, get_weather_desc, get_weather_description_from_counts, is_value_valid
from data.forecast_processing import recommend_best_times
from display.colors import colorize, get_rating_info
from display.display_core import _format_column, display_temperature, get_location_display_name

from . import colors


def display_best_times_recommendation(all_location_processed_data: Dict[str, Any],
                                      location_key: Optional[str] = None,
                                      date_filters: Optional[List[date]] = None) -> None:
  """Display recommendations for the best times to go out based on weather forecasts.

  Args:
      all_location_processed_data: Dictionary of processed forecast data by location key
      location_key: Optional location key to filter recommendations to a specific location
      date_filters: Optional list of dates to display instead of using the recommended periods
  """
  if not all_location_processed_data:
    return

  # Filter to a single location if specified
  if location_key:
    if location_key not in all_location_processed_data:
      return
    location_data = {location_key: all_location_processed_data[location_key]}
  else:
    location_data = all_location_processed_data

  # If specific dates are provided, show rankings for those dates
  if date_filters:
    _display_location_rankings_by_date(location_data, date_filters)
    return

  # Otherwise, show the best times
  periods = recommend_best_times(location_data)

  if not periods:
    print("No good weather periods found in the forecast.")
    return

  # Group by date
  date_groups: Dict[date, List[Dict[str, Any]]] = {}
  for period in periods:
    period_date = period["date"]
    if period_date not in date_groups:
      date_groups[period_date] = []
    date_groups[period_date].append(period)

  # Sort dates to ensure consistent order
  sorted_dates = sorted(date_groups.keys())

  # Define column widths for consistent alignment
  location_width = 22
  time_width = 14
  rating_width = 18
  temp_width = 14
  weather_width = 24

  # Display periods by date in table format
  for i, date_obj in enumerate(sorted_dates):
    date_periods = date_groups[date_obj]

    # Display date header - add newline before dates that aren't the first
    day_name = date_obj.strftime("%A")
    date_str = format_date(date_obj)

    if i == 0:
      print(colorize(f"{day_name}, {date_str}", colors.HIGHLIGHT))
    else:
      print(f"\n{colorize(f'{day_name}, {date_str}', colors.HIGHLIGHT)}")

    # Print table headers
    loc_header = _format_column(colorize("Location", colors.INFO), location_width)
    time_header = _format_column(colorize("Time", colors.INFO), time_width)
    rating_header = _format_column(colorize("Rating", colors.INFO), rating_width)
    temp_header = _format_column(colorize("Temperature", colors.INFO), temp_width)
    weather_header = _format_column(colorize("Weather", colors.INFO), weather_width)

    print(f"  {loc_header} {time_header} {rating_header} {temp_header} {weather_header}")
    print(f"  {'-' * location_width} {'-' * time_width} {'-' * rating_width} {'-' * temp_width} {'-' * weather_width}")

    # Sort periods by score for this date
    date_periods.sort(key=lambda x: x["final_score"], reverse=True)

    # Display with sequential ranking
    for period in date_periods:
      start_time = period["start_time"].strftime("%H:%M")
      end_time = period["end_time"].strftime("%H:%M")
      time_range = f"{start_time}-{end_time}"

      score = period["final_score"]
      score_formatted = f"{score:.1f}"
      rating, color = get_rating_info(score)
      rating_score = f"[{rating} - {score_formatted}]"

      # Capitalize the location name
      location = period["location"]
      location_name = get_location_display_name(location)

      weather_desc = get_weather_desc(period["dominant_symbol"])

      # Add rain probability if available
      if "precipitation_probability" in period and period["precipitation_probability"] and period["precipitation_probability"] > 0:
        weather_desc += f" ({period['precipitation_probability']:.0f}%)"

      temp = period.get("avg_temp")
      temp_str = display_temperature(temp)

      # Format columns with proper alignment and color
      loc_col = _format_column(colorize(location_name, color), location_width)
      time_col = _format_column(colorize(time_range, color), time_width)
      rating_col = _format_column(colorize(rating_score, color), rating_width)
      temp_col = _format_column(temp_str, temp_width)
      weather_col = _format_column(weather_desc, weather_width)

      # Print each row with proper spacing and colors
      print(f"  {loc_col} {time_col} {rating_col} {temp_col} {weather_col}")


def _display_location_rankings_by_date(all_location_processed_data: Dict[str, Any], dates: List[date]) -> None:
  """Display location rankings for specified dates.

  Args:
      all_location_processed_data: Dictionary of processed forecast data by location key
      dates: List of dates to display rankings for
  """
  # Define column widths
  location_width = 22  # Increased to accommodate longer names
  rating_width = 18
  temp_width = 20  # Increased to accommodate expanded temperature format
  weather_width = 24  # Increased to accommodate weather + rain %

  # Process each date
  for i, current_date in enumerate(dates):
    # Add a newline between dates except for the first one
    if i > 0:
      print()

    # Display date header
    day_name = current_date.strftime("%A")
    date_str = format_date(current_date)
    print(colorize(f"{day_name}, {date_str}", colors.HIGHLIGHT))

    # Get data for each location for this date
    location_ratings = []

    for loc_key, forecast_data in all_location_processed_data.items():
      location_name = get_location_display_name(loc_key)
      day_scores = forecast_data.get("day_scores", {})

      if current_date not in day_scores:
        continue  # Skip if no data for this date

      daily_report = day_scores[current_date]
      score = daily_report.avg_score
      rating, color = get_rating_info(score)

      # Format temperature range with space
      temp_range = "N/A"
      if is_value_valid(daily_report.min_temp) and is_value_valid(daily_report.max_temp):
        temp_range = f"{daily_report.min_temp:.1f}°C - {daily_report.max_temp:.1f}°C"

      # Determine weather description
      weather_desc = get_weather_description_from_counts(
          daily_report.sunny_hours,
          daily_report.partly_cloudy_hours,
          daily_report.rainy_hours
      )

      # Add rain probability if available
      if is_value_valid(daily_report.avg_precip_prob) and daily_report.avg_precip_prob > 0:
        weather_desc += f" ({daily_report.avg_precip_prob:.0f}%)"

      # Store for sorting
      location_ratings.append((
          loc_key,
          location_name,
          score,
          rating,
          color,
          temp_range,
          weather_desc
      ))

    # Sort by score (highest first)
    location_ratings.sort(key=lambda x: x[2], reverse=True)

    # Print table headers
    loc_header = _format_column(colorize("Location", colors.INFO), location_width)
    rating_header = _format_column(colorize("Rating", colors.INFO), rating_width)
    temp_header = _format_column(colorize("Temperature", colors.INFO), temp_width)
    weather_header = _format_column(colorize("Weather", colors.INFO), weather_width)

    print(f"  {loc_header} {rating_header} {temp_header} {weather_header}")
    print(f"  {'-' * location_width} {'-' * rating_width} {'-' * temp_width} {'-' * weather_width}")

    # Display sorted locations
    for _, name, score, rating, color, temp_range, weather in location_ratings:
      # Format score with one decimal place
      score_formatted = f"{score:.1f}"
      rating_score = f"[{rating} - {score_formatted}]"

      # Create properly aligned columns with color handling
      name_col = _format_column(colorize(name, color), location_width)
      rating_col = _format_column(colorize(rating_score, color), rating_width)
      temp_col = _format_column(temp_range, temp_width)
      weather_col = _format_column(weather, weather_width)

      # Print each row with proper spacing and colors
      print(f"  {name_col} {rating_col} {temp_col} {weather_col}")
