"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""

from weather_api import fetch_weather_data
from forecast_processing import process_forecast
from display_utils import (
    list_locations, display_forecast, compare_locations, display_best_times_recommendation,
    display_hourly_forecast
)
from config import (
    FORECAST_DAYS, TIMEZONE, COLOR_RED, COLOR_YELLOW, COLOR_RESET
)
from locations import LOCATIONS
import argparse
import time
from datetime import datetime

import pytz


def main():
  """Process command-line arguments and execute requested operations."""
  parser = argparse.ArgumentParser(
      description='Daily Helper: Weather forecast tool for finding the best times for outdoor activities.')
  parser.add_argument('-l', '--location', help='Specific location to get forecast for')
  parser.add_argument('-c', '--compare', action='store_true',
                      help='Compare weather conditions across all locations')
  parser.add_argument('-a', '--all', action='store_true',
                      help='Show forecasts for all locations')
  parser.add_argument('-r', '--recommend', action='store_true',
                      help='Recommend best times to go out this week')
  parser.add_argument('-d', '--date', help='Date filter for comparison (YYYY-MM-DD format)')
  parser.add_argument('--list', action='store_true', help='List all available locations')
  parser.add_argument('--hourly', action='store_true', help='Show hourly forecast instead of daily')
  parser.add_argument('--debug', action='store_true', help='Show additional debugging information')

  args = parser.parse_args()

  # List locations if requested
  if args.list:
    list_locations()
    return

  # Parse date filter if provided
  date_filter = None
  if args.date:
    try:
      date_filter = datetime.strptime(args.date, '%Y-%m-%d').date()
    except ValueError:
      print(f"{COLOR_RED}Invalid date format. Please use YYYY-MM-DD format.{COLOR_RESET}")
      return

  # Show loading message
  print(f"{COLOR_YELLOW}Fetching weather data...{COLOR_RESET}")
  start_time = time.time()

  # Get location(s) to process
  target_locations = []
  if args.location:
    if args.location in LOCATIONS:
      target_locations = [args.location]
    else:
      print(f"{COLOR_RED}Invalid location. Use --list to see available locations.{COLOR_RESET}")
      return
  elif args.all or args.compare or args.recommend:
    target_locations = list(LOCATIONS.keys())
  else:
    # Default to Gijón if no location specified
    target_locations = ["gijon"]

  # Fetch and process weather data
  location_data = {}
  for loc_key in target_locations:
    location = LOCATIONS[loc_key]
    weather_data = fetch_weather_data(location)

    if weather_data:
      processed_data = process_forecast(weather_data, location.name)
      location_data[loc_key] = processed_data
    else:
      print(f"{COLOR_RED}Unable to fetch weather data for {location.name}.{COLOR_RESET}")

  end_time = time.time()
  if args.debug:
    print(f"{COLOR_YELLOW}Data fetched in {end_time - start_time:.2f} seconds.{COLOR_RESET}")

  # No data retrieved
  if not location_data:
    print(f"{COLOR_RED}No weather data available. Please try again later.{COLOR_RESET}")
    return

  # Handle different display modes
  if args.compare:
    compare_locations(location_data, date_filter)
  elif args.recommend:
    display_best_times_recommendation(location_data)
  elif args.all:
    for loc_key, forecast in location_data.items():
      location_name = LOCATIONS[loc_key].name
      if args.hourly:
        display_hourly_forecast(forecast, location_name)
      else:
        display_forecast(forecast, location_name)
  else:
    # Single location display
    loc_key = target_locations[0]
    location_name = LOCATIONS[loc_key].name
    forecast = location_data[loc_key]

    if args.hourly:
      display_hourly_forecast(forecast, location_name)
    else:
      display_forecast(forecast, location_name)
      # Also show recommendation for single location
      display_best_times_recommendation(location_data, loc_key)


if __name__ == "__main__":
  main()
