"""
Weather Helper: Weather forecasting tool that helps find the best times and locations for outdoor activities.
"""

import argparse
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from data.forecast_processing import process_forecast
from data.locations import LOCATIONS
from data.weather_api import fetch_weather_data
from display.display_comparison import display_best_times_recommendation
from display.display_core import display_error, display_info, display_loading_message
from display.display_forecast import display_hourly_forecast


def main() -> None:
  """Process command-line arguments and execute requested operations."""
  parser = argparse.ArgumentParser(description='Weather Helper: Weather forecast tool for finding the best times for outdoor activities.')

  parser.add_argument('-l', '--location', help='Specific location to get forecast for')
  parser.add_argument('-d', '--date', help='Date filter for forecasts (YYYY-MM-DD format)')
  parser.add_argument('-a', '--all', action='store_true', help='Show forecasts for all locations')
  parser.add_argument('-r', '--rank', action='store_true', help='Rank locations by weather conditions for today, tomorrow and day after')
  parser.add_argument('--debug', action='store_true', help='Show additional debugging information')

  args = parser.parse_args()

  # Parse date filter if provided
  date_filter = None
  if args.date:
    try:
      date_filter = datetime.strptime(args.date, '%Y-%m-%d').date()
    except ValueError:
      display_error("Invalid date format. Please use YYYY-MM-DD format.")
      return

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
      processed_data = process_forecast(weather_data, location.name)
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
    # Get today, tomorrow, and day after tomorrow's dates
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    # Display rankings for each day
    display_best_times_recommendation(location_data, None, [today, tomorrow, day_after])
  elif args.all:
    # Display forecast for all locations with line breaks between them
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
