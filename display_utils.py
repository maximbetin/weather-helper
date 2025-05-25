"""
Utility functions for displaying weather information and recommendations.
"""

from datetime import datetime
import pytz  # For timezone in compare_locations default date

from colorama import Fore, Style  # Already initialized in config.py

# Import constants and configs
from config import (
    WEATHER_SYMBOLS, WEATHER_DESC_MAP, TIMEZONE,
    DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR,
    COLOR_EXCELLENT, COLOR_VERY_GOOD, COLOR_GOOD, COLOR_FAIR,
    COLOR_POOR, COLOR_BAD, COLOR_MAGENTA, COLOR_RESET,
    COLOR_CYAN, COLOR_LIGHTMAGENTA_EX, COLOR_YELLOW, COLOR_RED,
    COLOR_GREEN, COLOR_LIGHTRED_EX, COLOR_LIGHTGREEN_EX
)
from locations import LOCATIONS
# For display_forecast to show best/worst blocks if not in compare_mode
from forecast_processing import extract_blocks
# For display_best_times_recommendation to get the periods
from forecast_processing import recommend_best_times


# --- Weather symbol/description mapping and helpers ---
def get_weather_desc(symbol):
  """Return standardized weather description from symbol code."""
  if not symbol or not isinstance(symbol, str):
    return "Unknown"
  # Symbol is already base from processing, no need to split '_'
  base = symbol
  desc, _ = WEATHER_SYMBOLS.get(base, (base.replace('_', ' ').capitalize(), 0))
  return desc


def get_standardized_weather_desc(symbol):
  """Return standardized weather description from symbol code (legacy, consider merging with get_weather_desc)."""
  if not symbol or not isinstance(symbol, str):
    return "Unknown"
  if symbol in WEATHER_DESC_MAP:
    return WEATHER_DESC_MAP[symbol]
  # Fallback logic similar to original, symbol is base
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


def get_rating_info(score):
  """Return standardized rating description and color based on score."""
  if score is None:
    return "N/A", COLOR_RESET  # Handle None score gracefully
  if score >= 7.0:
    return "Excellent", COLOR_LIGHTGREEN_EX
  elif score >= 4.5:
    return "Very Good", COLOR_GREEN
  elif score >= 2.0:
    return "Good", COLOR_CYAN
  elif score >= 0.0:
    return "Fair", COLOR_YELLOW
  elif score >= -3.0:
    return "Poor", COLOR_LIGHTRED_EX
  else:
    return "Bad", COLOR_RED


def list_locations():
  """List all available locations."""
  print(f"\n{COLOR_MAGENTA}Available Locations{COLOR_RESET}")
  for key, loc in LOCATIONS.items():
    print(f"  {key} - {COLOR_LIGHTMAGENTA_EX}{loc.name}{COLOR_RESET}")


def display_forecast(processed_forecast_data, location_display_name, compare_mode=False):
  """Display weather forecast for a location.
  Args:
    processed_forecast_data: The output from process_forecast().
    location_display_name: The display name of the location (e.g., "Gijón").
    compare_mode: Boolean, if True, adjusts output for comparison view.
  """
  if not processed_forecast_data:
    print(f"\n{COLOR_YELLOW}No forecast data to display for {location_display_name}.{COLOR_RESET}")
    return

  # daily_forecasts: dict of date -> list of HourlyWeather
  # day_scores: dict of date -> DailyReport
  daily_forecasts = processed_forecast_data.get("daily_forecasts", {})
  day_scores = processed_forecast_data.get("day_scores", {})

  print(f"\n{COLOR_MAGENTA}Daily Forecast for {location_display_name}{COLOR_RESET}")

  # Sort days chronologically
  for date_obj in sorted(daily_forecasts.keys()):
    if date_obj not in day_scores:
      continue  # Should not happen if process_forecast is consistent

    daily_report = day_scores[date_obj]  # This is a DailyReport object
    date_str = date_obj.strftime("%a, %d %b")

    rating, color = get_rating_info(daily_report.avg_score)

    precip_warning = ""
    if daily_report.avg_precip_prob is not None and daily_report.avg_precip_prob > 40:
      precip_warning = f" - {daily_report.avg_precip_prob:.0f}% rain"

    # Determine overall weather description based on DailyReport stats
    if daily_report.sunny_hours > daily_report.partly_cloudy_hours and daily_report.sunny_hours > daily_report.rainy_hours:
      weather_desc_display = "Sunny" + precip_warning
    elif daily_report.partly_cloudy_hours > daily_report.sunny_hours and daily_report.partly_cloudy_hours > daily_report.rainy_hours:
      weather_desc_display = "Partly Cloudy" + precip_warning
    elif daily_report.rainy_hours > 0:
      weather_desc_display = f"Rain ({daily_report.rainy_hours}h)"
    else:
      weather_desc_display = "Mixed" + precip_warning

    temp_str = "N/A"
    if daily_report.min_temp is not None and daily_report.max_temp is not None:
      temp_str = f"{daily_report.min_temp:>4.1f}°C - {daily_report.max_temp:>4.1f}°C"

    print(f"{date_str} {color}[{rating}]{COLOR_RESET} {temp_str} - {weather_desc_display}")

    if not compare_mode:
      # Get daylight HourlyWeather objects for this date
      daylight_hourly_weather = sorted(
          [h for h in daily_forecasts.get(date_obj, []) if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR],
          key=lambda x: x.time
      )
      if not daylight_hourly_weather:
        continue

      weather_blocks = extract_blocks(daylight_hourly_weather)  # extract_blocks expects list of HourlyWeather
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
        start_t = block[0].time.strftime("%H:%M")
        end_t = block[-1].time.strftime("%H:%M")
        print(f"  Best: {COLOR_GREEN}{start_t}-{end_t}{COLOR_RESET}")

      if worst_block_info and daily_report.avg_score >= 0:  # Only show avoid if day is generally good
        block, _ = worst_block_info
        start_t = block[0].time.strftime("%H:%M")
        end_t = block[-1].time.strftime("%H:%M")
        print(f"  Avoid: {COLOR_RED}{start_t}-{end_t}{COLOR_RESET}")
  print()  # Add a blank line after each location's full forecast


def compare_locations(all_location_processed_data):
  """Compare weather conditions across multiple locations for the current day's forecast.
  Args:
    all_location_processed_data: Dict where key is loc_key, value is output of process_forecast().
  """
  # Determine the primary date for comparison from the data itself (usually today)
  # We will pick the earliest date for which any location has a DailyReport.
  comparison_target_date = None
  for loc_key, processed_data in all_location_processed_data.items():
    if processed_data and processed_data.get("day_scores"):
      # day_scores is a dict of date -> DailyReport, find the min date (earliest)
      min_date_for_loc = min(processed_data["day_scores"].keys(), default=None)
      if min_date_for_loc:
        if comparison_target_date is None or min_date_for_loc < comparison_target_date:
          comparison_target_date = min_date_for_loc

  if not comparison_target_date:
    # Fallback to system's today if no data yields a date (should not happen if all_processed_data is not empty)
    comparison_target_date = datetime.now(pytz.timezone(TIMEZONE)).date()

  date_str_formatted = comparison_target_date.strftime('%A, %d %b')
  print(f"\n{COLOR_MAGENTA}Location Comparison for {date_str_formatted}{COLOR_RESET}")

  daily_reports_for_date = []
  for loc_key, processed_data in all_location_processed_data.items():
    if not processed_data or not processed_data.get("day_scores"):
      continue
    # Get the DailyReport for the determined comparison_target_date
    if comparison_target_date in processed_data["day_scores"]:
      daily_reports_for_date.append(processed_data["day_scores"][comparison_target_date])

  if not daily_reports_for_date:
    print(f"\n{COLOR_YELLOW}No data available for this date to compare.{COLOR_RESET}")
    return

  # Sort DailyReport objects by avg_score
  daily_reports_for_date.sort(key=lambda dr: dr.avg_score, reverse=True)

  max_loc_len = max(len(dr.location_name) for dr in daily_reports_for_date) if daily_reports_for_date else 15
  loc_width = max(max_loc_len + 2, 17)
  weather_col_width = 15  # For "Partly Cloudy"

  header = f"{COLOR_CYAN}{'Location':<{loc_width}} {'Rating':<10} {'Temp':<15} {'Weather':<{weather_col_width}} {'Score':>6}{COLOR_RESET}"
  print(f"\n{header}")
  print(f"{'.' * loc_width} {'.' * 10} {'.' * 15} {'.' * weather_col_width} {'.' * 6}".replace(".", "-"))  # Dashes

  for dr in daily_reports_for_date:  # dr is DailyReport
    rating_str, rating_color = get_rating_info(dr.avg_score)

    weather_disp = "Mixed"
    if dr.sunny_hours > dr.partly_cloudy_hours and dr.sunny_hours > dr.rainy_hours:
      weather_disp = "Sunny"
    elif dr.partly_cloudy_hours > dr.sunny_hours and dr.partly_cloudy_hours > dr.rainy_hours:
      weather_disp = "Partly Cloudy"
    elif dr.rainy_hours > 0:
      weather_disp = f"Rain ({dr.rainy_hours}h)"

    temp_disp = "N/A"
    if dr.min_temp is not None and dr.max_temp is not None:
      temp_disp = f"{dr.min_temp:.1f}°C - {dr.max_temp:.1f}°C"

    raw_score_val = dr.avg_score
    score_str_disp = f"{raw_score_val:6.1f}"
    _, score_color = get_rating_info(raw_score_val)

    print(f"{COLOR_LIGHTMAGENTA_EX}{dr.location_name:<{loc_width}}{COLOR_RESET} "
          f"{rating_color}{rating_str:<10}{COLOR_RESET} "
          f"{temp_disp:<15} "
          f"{weather_disp:<{weather_col_width}} "
          f"{score_color}{score_str_disp}{COLOR_RESET}")
  print()  # Blank line after table


def display_best_times_recommendation(all_location_processed_data):
  """Display a simple recommendation for when to go out this week, using all_location_processed_data.
  Args:
    all_location_processed_data: Dict where key is loc_key, value is output of process_forecast().
  """
  # recommend_best_times expects the all_location_processed_data structure
  all_periods_list = recommend_best_times(all_location_processed_data)

  if not all_periods_list:
    print(f"\n{COLOR_YELLOW}No ideal outdoor times found for this week based on current criteria.{COLOR_RESET}")
    print("Try checking individual locations for more details.")
    return

  print(f"\n{COLOR_MAGENTA}Best Times to Go Out (Next 7 Days){COLOR_RESET}")

  # Filter to top N per day if list is very long, or just cap total.
  # For now, let's use the logic from recommend_best_times which already sorts and has fallbacks.
  # If we want to further filter/limit here, we can.
  # The current recommend_best_times returns a sorted list of period dicts.

  # Limit to a reasonable number of recommendations, e.g., top 15-20 overall if many.
  # Or ensure diversity across days if recommend_best_times doesn't already.
  # The original implementation had a complex filtering within display. We rely on recommend_best_times now.

  # To keep it similar to original display (top 5 per day like structure):
  days_data = {}
  for p_dict in all_periods_list:
    days_data.setdefault(p_dict["date"], []).append(p_dict)

  filtered_display_periods = []
  for date_obj_key in sorted(days_data.keys()):
    day_specific_periods = sorted(days_data[date_obj_key], key=lambda x: x["score"], reverse=True)
    filtered_display_periods.extend(day_specific_periods[:5])  # Take top 5 for this day

  if not filtered_display_periods:
    print(f"\n{COLOR_YELLOW}No suitable periods found after filtering.{COLOR_RESET}")
    return

  # Cap total recommendations to e.g. 20 if many days have 5 good slots
  filtered_display_periods = filtered_display_periods[:20]

  max_loc_len = max(len(p["location"]) for p in filtered_display_periods) if filtered_display_periods else 15
  loc_width = max(max_loc_len + 2, 17)
  weather_width = 22  # Accommodate "Partly Cloudy  18.5°C"

  header = f"{COLOR_CYAN}{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{loc_width}} {'Weather & Temp':<{weather_width}} {'Score':>6}{COLOR_RESET}"
  print(f"\n{header}")
  print(f"{'.' * 3} {'.' * 16} {'.' * 15} {'.' * 10} {'.' * loc_width} {'.' * weather_width} {'.' * 6}".replace('.', '-'))

  current_date_tracker = None
  for i, period_dict in enumerate(filtered_display_periods, 1):
    if current_date_tracker and current_date_tracker != period_dict["date"]:
      print()  # Add line break between different dates
    current_date_tracker = period_dict["date"]

    date_str_fmt = period_dict["date"].strftime("%d %b")
    day_name_short = period_dict["day_name"][:3]
    day_date_display = f"{day_name_short}, {date_str_fmt}"

    start_str_fmt = period_dict["start_time"].strftime("%H:%M")
    end_str_fmt = period_dict["end_time"].strftime("%H:%M")
    time_range_display = f"{start_str_fmt}-{end_str_fmt}"

    rating_str_disp, overall_color = get_rating_info(period_dict["score"])
    duration_display = f"{period_dict['duration']} hours"

    # Use get_weather_desc for symbol to text conversion
    weather_text_desc = get_weather_desc(period_dict["dominant_symbol"])
    weather_text_desc_padded = f"{weather_text_desc:<15}"  # Pad to 15 for weather description

    temp_text_desc = ""
    if period_dict["avg_temp"] is not None:
      temp_text_desc = f"{period_dict['avg_temp']:>6.1f}°C"  # Right align temp within its space

    weather_temp_combined = f"{weather_text_desc_padded}{temp_text_desc}"

    raw_score_val = period_dict['score']
    score_str_val = f"{raw_score_val:6.1f}"
    # Use overall_color derived from score for the date string and score itself
    # For location and weather, use specific colors or default

    print(f"{i:<3} "
          f"{overall_color}{day_date_display:<16}{COLOR_RESET} "
          f"{time_range_display:<15} "
          f"{duration_display:<10} "
          f"{COLOR_LIGHTMAGENTA_EX}{period_dict['location']:<{loc_width}}{COLOR_RESET} "
          f"{weather_temp_combined:<{weather_width}} "  # Text color for this part is default
          f"{overall_color}{score_str_val}{COLOR_RESET}")
  print()  # final blank line
