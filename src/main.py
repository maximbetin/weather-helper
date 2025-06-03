"""
Weather Helper: Weather forecasting tool that helps find the best times and locations for outdoor activities.
"""

import argparse
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, FORECAST_DAYS, HIGHLIGHT, INFO, LIGHTMAGENTA
from src.daily_report import DailyReport
from src.hourly_weather import HourlyWeather
from src.locations import LOCATIONS
from src.utils import *
from src.weather_api import fetch_weather_data


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
    display_location_rankings_by_date(location_data, date_filters)
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
      print(colorize(f"{day_name}, {date_str}", HIGHLIGHT))
    else:
      print(f"\n{colorize(f'{day_name}, {date_str}', HIGHLIGHT)}")

    # Print table headers
    loc_header = format_column(colorize("Location", INFO), location_width)
    time_header = format_column(colorize("Time", INFO), time_width)
    rating_header = format_column(colorize("Rating", INFO), rating_width)
    temp_header = format_column(colorize("Temperature", INFO), temp_width)
    weather_header = format_column(colorize("Weather", INFO), weather_width)

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
      loc_col = format_column(colorize(location_name, color), location_width)
      time_col = format_column(colorize(time_range, color), time_width)
      rating_col = format_column(colorize(rating_score, color), rating_width)
      temp_col = format_column(temp_str, temp_width)
      weather_col = format_column(weather_desc, weather_width)

      # Print each row with proper spacing and colors
      print(f"  {loc_col} {time_col} {rating_col} {temp_col} {weather_col}")


def display_location_rankings_by_date(all_location_processed_data: Dict[str, Any], dates: List[date]) -> None:
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
    print(colorize(f"{day_name}, {date_str}", HIGHLIGHT))

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
    loc_header = format_column(colorize("Location", INFO), location_width)
    rating_header = format_column(colorize("Rating", INFO), rating_width)
    temp_header = format_column(colorize("Temperature", INFO), temp_width)
    weather_header = format_column(colorize("Weather", INFO), weather_width)

    print(f"  {loc_header} {rating_header} {temp_header} {weather_header}")
    print(f"  {'-' * location_width} {'-' * rating_width} {'-' * temp_width} {'-' * weather_width}")

    # Display sorted locations
    for _, name, score, rating, color, temp_range, weather in location_ratings:
      # Format score with one decimal place
      score_formatted = f"{score:.1f}"
      rating_score = f"[{rating} - {score_formatted}]"

      # Create properly aligned columns with color handling
      name_col = format_column(colorize(name, color), location_width)
      rating_col = format_column(colorize(rating_score, color), rating_width)
      temp_col = format_column(temp_range, temp_width)
      weather_col = format_column(weather, weather_width)

      # Print each row with proper spacing and colors
      print(f"  {name_col} {rating_col} {temp_col} {weather_col}")


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
  time_header = format_column(colorize("Time", INFO), time_width)
  rating_header = format_column(colorize("Rating", INFO), rating_width)
  temp_header = format_column(colorize("Temperature", INFO), temp_width)
  weather_header = format_column(colorize("Weather", INFO), weather_width)

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
    time_col = format_column(colorize(time_str, color), time_width)
    rating_col = format_column(colorize(rating_score, color), rating_width)
    temp_col = format_column(temp_str, temp_width)
    weather_col = format_column(weather_desc, weather_width)

    print(f"  {time_col} {rating_col} {temp_col} {weather_col}")


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
    avg_temp = (
        sum(h.temp for h in block if h.temp is not None) /
        len([h for h in block if h.temp is not None]) if any(h.temp is not None for h in block) else None
    )

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
      for block_entry in top_blocks:  # Renamed 'block' to 'block_entry' to avoid conflict with outer scope
        final_recommendations.append(block_entry)

  return final_recommendations


def main() -> None:
  """Process command-line arguments and execute requested operations."""
  parser = argparse.ArgumentParser(description='Weather Helper: Weather forecast tool for finding the best times for outdoor activities.')

  parser.add_argument('-l', '--location', help='Specific location to get forecast for')
  parser.add_argument('-a', '--all', action='store_true', help='Show forecasts for all locations')
  parser.add_argument('-r', '--rank', action='store_true', help='Rank locations by weather conditions for today, tomorrow and day after')
  parser.add_argument('--debug', action='store_true', help='Show additional debugging information')

  args = parser.parse_args()

  # Get location(s) to process
  target_locations: List[str] = []
  if args.location:
    if args.location in LOCATIONS:
      target_locations = [args.location]
    else:
      display_error("Invalid location. Use the -a option to see all available locations.")
      return
  elif args.all or args.rank:
    target_locations = list(LOCATIONS.keys())
  else:
    # Default to Gijón if no location specified
    target_locations = ["gijon"]

  # Show loading message
  display_loading_message()
  start_time = time.time()

  # Fetch and process weather data
  location_data: Dict[str, Any] = {}
  for loc_key in target_locations:
    location = LOCATIONS[loc_key]
    weather_data = fetch_weather_data(location)

    if weather_data:
      processed_data = process_forecast(weather_data, loc_key)
      location_data[loc_key] = processed_data
    else:
      display_error(f"Unable to fetch weather data for {location.name}.")

  end_time = time.time()
  if args.debug:
    display_info(f"Data fetched in {end_time - start_time:.2f} seconds.")

  # No data retrieved
  if not location_data:
    display_error("No weather data available. Please try again later.")
    return

  # Handle different display modes
  if args.rank:
    # Get dates for the next 7 days
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(FORECAST_DAYS)]

    # Display rankings for each day
    display_best_times_recommendation(location_data, None, dates)
  elif args.all:
    # Display forecast for all locations
    for i, loc_key in enumerate(sorted(location_data.keys())):
      if i > 0:
        print()  # Add line break between locations
      location_name = LOCATIONS[loc_key].name
      forecast = location_data[loc_key]
      display_hourly_forecast(forecast, location_name)
  else:
    # Single location display - always use hourly forecast
    loc_key = target_locations[0]
    location_name = LOCATIONS[loc_key].name
    forecast = location_data[loc_key]
    display_hourly_forecast(forecast, location_name)


if __name__ == "__main__":
  main()
