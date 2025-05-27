"""
Utility functions for displaying weather information and recommendations.
"""

import colors
from colors import get_rating_info
from config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR
from core_utils import get_current_datetime, get_weather_desc
from forecast_processing import extract_blocks, recommend_best_times
from locations import LOCATIONS


def display_hourly_forecast(forecast_data, location_name):
  """Display hourly weather forecast for a location for the current day."""
  if not forecast_data:
    return

  daily_forecasts = forecast_data["daily_forecasts"]
  day_scores = forecast_data["day_scores"]

  print(f"\n{colors.HIGHLIGHT}{location_name}{colors.RESET}")

  # Get today's date
  current_dt = get_current_datetime()
  today = current_dt.date()

  if today not in daily_forecasts:
    print(f"{colors.WARNING}No hourly data available for today.{colors.RESET}")
    return

  # Get today's hours
  hours = sorted([h for h in daily_forecasts[today]], key=lambda x: x.hour)

  if not hours:
    print(f"{colors.WARNING}No hourly data available for today.{colors.RESET}")
    return

  # Get current hour
  current_hour = current_dt.hour

  # Print table header
  print(f"\n{colors.INFO}{'Time':<8} {'Weather':<15} {'Temp':<8} {'Wind':<8} {'Rain %':<8} {'Score':>6}{colors.RESET}")
  print(f"{'-' * 8} {'-' * 15} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 6}")

  # Print hourly data, starting from current hour
  for hour in [h for h in hours if h.hour >= current_hour]:
    time_str = hour.time.strftime("%H:%M")

    # Weather description
    weather_desc = get_weather_desc(hour.symbol)

    # Temperature
    temp_str = f"{hour.temp:.1f}°C" if isinstance(hour.temp, (int, float)) else "N/A"

    # Wind
    wind_str = f"{hour.wind:.1f}m/s" if isinstance(hour.wind, (int, float)) else "N/A"

    # Precipitation probability
    precip_prob_str = f"{hour.precipitation_probability:.0f}%" if isinstance(hour.precipitation_probability, (int, float)) else "N/A"

    # Score
    rating, color = get_rating_info(hour.total_score)
    score_str = f"{hour.total_score:6.1f}"

    print(f"{time_str:<8} {weather_desc:<15} {temp_str:<8} {wind_str:<8} {precip_prob_str:<8} {color}{score_str}{colors.RESET}")


def display_forecast(processed_forecast_data, location_display_name, compare_mode=False):
  """Display weather forecast for a location.
  Args:
    processed_forecast_data: The output from process_forecast().
    location_display_name: The display name of the location (e.g., "Gijón").
    compare_mode: Boolean, if True, adjusts output for comparison view.
  """
  if not processed_forecast_data:
    print(f"\n{colors.WARNING}No forecast data to display for {location_display_name}.{colors.RESET}")
    return

  # daily_forecasts: dict of date -> list of HourlyWeather
  # day_scores: dict of date -> DailyReport
  daily_forecasts = processed_forecast_data.get("daily_forecasts", {})
  day_scores = processed_forecast_data.get("day_scores", {})

  print(f"\n{colors.HIGHLIGHT}Daily Forecast for {location_display_name}{colors.RESET}")

  # Sort days chronologically
  for date_obj in sorted(daily_forecasts.keys()):
    if date_obj not in day_scores:
      continue  # Should not happen if process_forecast is consistent

    daily_report = day_scores[date_obj]  # This is a DailyReport object
    date_str = date_obj.strftime("%a, %d %b")

    rating, color = get_rating_info(daily_report.avg_score)

    # Use the weather_description property
    weather_desc_display = daily_report.weather_description

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
        print(f"  Best: {colors.GREEN}{start_t}-{end_t}{colors.RESET}")

      if worst_block_info and daily_report.avg_score >= 0:  # Only show avoid if day is generally good
        block, _ = worst_block_info
        start_t = block[0].time.strftime("%H:%M")
        end_t = block[-1].time.strftime("%H:%M")
        print(f"  Avoid: {colors.RED}{start_t}-{end_t}{colors.RESET}")
  print()  # Add a blank line after each location's full forecast


def compare_locations(all_location_processed_data, date_filter=None):
  """Compare weather conditions across all locations for a given date.

  Args:
    all_location_processed_data: Dictionary of location_key -> processed_forecast_data
    date_filter: Optional date to filter to, or current date if None
  """
  if not all_location_processed_data:
    return

  # Get the target date
  comparison_target_date = date_filter
  if comparison_target_date is None:
    comparison_target_date = get_current_datetime().date()

  date_str_formatted = comparison_target_date.strftime('%A, %d %b')
  print(f"\n{colors.HIGHLIGHT}Location Comparison for {date_str_formatted}{colors.RESET}")

  daily_reports_for_date = []
  for location_key, processed_data in all_location_processed_data.items():
    day_scores = processed_data.get("day_scores", {})
    if comparison_target_date in day_scores:
      daily_reports_for_date.append(day_scores[comparison_target_date])

  if not daily_reports_for_date:
    print(f"\n{colors.WARNING}No data available for this date to compare.{colors.RESET}")
    return

  # Sort locations by score, best first
  daily_reports_for_date.sort(key=lambda r: r.avg_score, reverse=True)

  # Find optimal column widths
  loc_width = max(len(dr.location_name) for dr in daily_reports_for_date) + 2
  weather_col_width = 15  # For "Partly Cloudy"

  header = f"{colors.INFO}{'Location':<{loc_width}} {'Rating':<10} {'Temp':<15} {'Weather':<{weather_col_width}} {'Score':>6}{colors.RESET}"
  print(f"\n{header}")
  print(f"{'.' * loc_width} {'.' * 10} {'.' * 15} {'.' * weather_col_width} {'.' * 6}".replace(".", "-"))  # Dashes

  for dr in daily_reports_for_date:  # dr is DailyReport
    rating_str, rating_color = get_rating_info(dr.avg_score)

    # Weather
    weather_disp = "N/A"
    if dr.rainy_hours > 0:
      weather_disp = f"Rain ({dr.rainy_hours}h)"
    elif dr.sunny_hours > 0 or dr.partly_cloudy_hours > 0:
      weather_disp = dr.weather_description

    # Format score
    raw_score_val = dr.avg_score
    score_str_disp = f"{raw_score_val:6.1f}"
    _, score_color = get_rating_info(raw_score_val)

    temp_disp = "N/A"
    if dr.min_temp is not None and dr.max_temp is not None:
      temp_disp = f"{dr.min_temp:.1f}°C - {dr.max_temp:.1f}°C"

    print(f"{colors.EMPHASIS}{dr.location_name:<{loc_width}}{colors.RESET} "
          f"{rating_color}{rating_str:<10}{colors.RESET} "
          f"{temp_disp:<15} "
          f"{weather_disp:<{weather_col_width}} "
          f"{score_color}{score_str_disp}{colors.RESET}")
  print()  # Blank line after table


def display_best_times_recommendation(all_location_processed_data, location_key=None):
  """Display a simple recommendation for when to go out this week, using all_location_processed_data.
  Args:
    all_location_processed_data: Dict where key is loc_key, value is output of process_forecast().
    location_key: Optional location key to filter recommendations for a specific location.
  """
  # Filter data if location_key is provided
  if location_key:
    if location_key not in all_location_processed_data:
      print(f"\n{colors.WARNING}No data available for location: {LOCATIONS[location_key].name}{colors.RESET}")
      return
    filtered_data = {location_key: all_location_processed_data[location_key]}
    location_display = f" in {LOCATIONS[location_key].name}"
  else:
    filtered_data = all_location_processed_data
    location_display = ""

  # recommend_best_times expects the all_location_processed_data structure
  all_periods_list = recommend_best_times(filtered_data)

  if not all_periods_list:
    print(f"\n{colors.WARNING}No ideal outdoor times found for this week{location_display} based on current criteria.{colors.RESET}")
    print("Try checking individual locations for more details.")
    return

  print(f"\n{colors.HIGHLIGHT}Best Times to Go Out{location_display} (Next 7 Days){colors.RESET}")

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
    print(f"\n{colors.WARNING}No suitable periods found after filtering.{colors.RESET}")
    return

  # Cap total recommendations to e.g. 20 if many days have 5 good slots
  filtered_display_periods = filtered_display_periods[:20]

  max_loc_len = max(len(p["location"]) for p in filtered_display_periods) if filtered_display_periods else 15
  loc_width = max(max_loc_len + 2, 17)
  weather_width = 22  # Accommodate "Partly Cloudy  18.5°C"

  header = f"{colors.INFO}{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{loc_width}} {'Weather & Temp':<{weather_width}} {'Score':>6}{colors.RESET}"
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
          f"{overall_color}{day_date_display:<16}{colors.RESET} "
          f"{time_range_display:<15} "
          f"{duration_display:<10} "
          f"{colors.EMPHASIS}{period_dict['location']:<{loc_width}}{colors.RESET} "
          f"{weather_temp_combined:<{weather_width}} "  # Text color for this part is default
          f"{overall_color}{score_str_val}{colors.RESET}")
  print()  # final blank line
