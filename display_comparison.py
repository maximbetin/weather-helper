"""
Functions for comparing and recommending locations based on weather forecasts.
"""

from datetime import date
from typing import Dict, List, Any, Optional, Tuple

import colors
from colors import get_rating_info
from core_utils import (
    format_date, get_current_date, is_value_valid,
    get_weather_desc
)
from display_core import (
    display_heading, display_subheading,
    display_temperature, display_table_header
)
from locations import LOCATIONS
from forecast_processing import recommend_best_times


def compare_locations(all_location_processed_data: Dict[str, Any], date_filter: Optional[date] = None) -> None:
  """Compare weather conditions across multiple locations.

  Args:
      all_location_processed_data: Dictionary of processed forecast data by location key
      date_filter: Optional date to filter the comparison to a specific day
  """
  if not all_location_processed_data:
    return

  display_heading("Location Comparison")

  # If no date filter provided, default to today
  if date_filter is None:
    date_filter = get_current_date()

  # Print the date we're comparing
  display_subheading(f"Weather for {format_date(date_filter)}")

  # Headers for the comparison table
  headers = ["Location", "Rating", "Temp Range", "Weather", "Rain %"]
  widths = [15, 12, 20, 20, 8]
  display_table_header(headers, widths)

  # Get data for each location
  location_ratings = []

  for loc_key, forecast_data in all_location_processed_data.items():
    location_name = LOCATIONS[loc_key].name
    day_scores = forecast_data.get("day_scores", {})

    if date_filter not in day_scores:
      continue  # Skip if no data for this date

    daily_report = day_scores[date_filter]
    rating, color = get_rating_info(daily_report.avg_score)

    # Format temperature range
    temp_range = "N/A"
    if is_value_valid(daily_report.min_temp) and is_value_valid(daily_report.max_temp):
      temp_range = f"{daily_report.min_temp:.1f}°C - {daily_report.max_temp:.1f}°C"

    # Determine weather description
    if daily_report.sunny_hours > daily_report.partly_cloudy_hours and daily_report.sunny_hours > daily_report.rainy_hours:
      weather_desc = "Sunny"
    elif daily_report.partly_cloudy_hours > daily_report.sunny_hours and daily_report.partly_cloudy_hours > daily_report.rainy_hours:
      weather_desc = "Partly Cloudy"
    elif daily_report.rainy_hours > 0:
      weather_desc = f"Rain ({daily_report.rainy_hours}h)"
    else:
      weather_desc = "Mixed"

    # Rain probability
    rain_prob = "N/A"
    if is_value_valid(daily_report.avg_precip_prob):
      rain_prob = f"{daily_report.avg_precip_prob:.0f}%"

    # Store for sorting
    location_ratings.append((
        loc_key,
        location_name,
        daily_report.avg_score,
        rating,
        color,
        temp_range,
        weather_desc,
        rain_prob
    ))

  # Sort by score (highest first)
  location_ratings.sort(key=lambda x: x[2], reverse=True)

  # Display sorted locations
  for _, name, _, rating, color, temp_range, weather, rain_prob in location_ratings:
    print(f"{name:<15} {color}{rating:<12}{colors.RESET} {temp_range:<20} {weather:<20} {rain_prob:<8}")


def display_best_times_recommendation(all_location_processed_data: Dict[str, Any], location_key: Optional[str] = None) -> None:
  """Display recommendations for the best times to go out based on weather forecasts.

  Args:
      all_location_processed_data: Dictionary of processed forecast data by location key
      location_key: Optional location key to filter recommendations to a specific location
  """
  if not all_location_processed_data:
    return

  # Filter to a single location if specified
  if location_key:
    if location_key not in all_location_processed_data:
      return
    location_data = {location_key: all_location_processed_data[location_key]}
    display_heading(f"Recommended Times for {LOCATIONS[location_key].name}")
  else:
    location_data = all_location_processed_data
    display_heading("Best Times This Week")

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

  # Display periods by date
  for date_obj in sorted(date_groups.keys()):
    date_periods = date_groups[date_obj]

    # Display date header
    day_name = date_obj.strftime("%A")
    date_str = format_date(date_obj)
    print(f"\n{colors.INFO}{day_name}, {date_str}{colors.RESET}")

    # Sort periods by score for this date
    date_periods.sort(key=lambda x: x["score"], reverse=True)

    for period in date_periods:
      start_time = period["start_time"].strftime("%H:%M")
      end_time = period["end_time"].strftime("%H:%M")
      score = period["score"]
      rating, color = get_rating_info(score)
      location = period["location"]

      weather_desc = get_weather_desc(period["dominant_symbol"])
      temp = period.get("avg_temp")
      temp_str = display_temperature(temp)

      print(f"  {color}{location:<12}{colors.RESET} {start_time}-{end_time} [{color}{rating}{colors.RESET}] {temp_str} - {weather_desc}")
