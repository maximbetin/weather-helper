"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""

import argparse
import time
from datetime import datetime
from colorama import init, Fore, Style

# Import from our modules
from config import LOCATIONS, TIMEZONE
from api_client import fetch_weather_data
from forecast_analysis import process_forecast, recommend_best_times
from display_utils import (
    display_forecast, compare_locations, list_locations,
    display_best_times_recommendation
)

# Initialize colorama for colored terminal output
init()


def main():
    """Main function to process command-line arguments and display weather forecasts."""
    parser = argparse.ArgumentParser(description="Weather forecast for outdoor activities in Asturias")

    location_group = parser.add_mutually_exclusive_group()
    location_group.add_argument("--location", "-l", choices=LOCATIONS.keys(),
                               help="Specific location to check")
    location_group.add_argument("--all", "-a", action="store_true",
                               help="Show all locations")
    location_group.add_argument("--compare", "-c", action="store_true",
                               help="Compare all locations for best weather")
    location_group.add_argument("--list", action="store_true",
                               help="List all available locations")

    parser.add_argument("--date", "-d", type=str,
                       help="Date to compare locations (format: YYYY-MM-DD)")
    parser.add_argument("--no-clear", action="store_true",
                       help="Don't clear the screen before displaying results")
    parser.add_argument("--recommend", "-r", action="store_true",
                       help="Show direct recommendations for when to go out this week")

    args = parser.parse_args()

    # Just list locations and exit
    if args.list:
        list_locations()
        return

    # Parse comparison date if provided
    comparison_date = None
    if args.date:
        try:
            comparison_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"{Fore.RED}Invalid date format. Use YYYY-MM-DD.{Style.RESET_ALL}")
            return

    # Default to Oviedo if no location specified
    selected_locations = {}
    if args.location:
        selected_locations[args.location] = LOCATIONS[args.location]
    elif args.all or args.compare or args.recommend:
        selected_locations = LOCATIONS
    else:
        selected_locations["oviedo"] = LOCATIONS["oviedo"]

    # Clear screen unless disabled
    if not args.no_clear:
        print("\033[2J\033[H")  # ANSI escape sequence to clear screen

    fetch_and_display_weather(selected_locations, args, comparison_date)


def fetch_and_display_weather(selected_locations, args, comparison_date=None):
    """Fetch weather data and display according to specified options."""
    # Fetch and process data for all selected locations
    location_data = {}
    for loc_key, location in selected_locations.items():
        print(f"Fetching data for {location['name']}...")
        data = fetch_weather_data(location)
        if data:
            location_data[loc_key] = process_forecast(data, location['name'])
            # Add a small delay between API calls to avoid rate limiting
            time.sleep(0.5)

    print()  # Add a blank line for better readability

    # Handle display based on selected options
    if args.recommend:
        display_best_times_recommendation(location_data)
        return

    if args.compare:
        compare_locations(location_data, comparison_date or datetime.now().date())

        # Show location summaries for each city in comparison mode
        for loc_key, forecast in location_data.items():
            display_forecast(forecast, LOCATIONS[loc_key]["name"], compare_mode=True)
    else:
        # Display each location's forecast in detail
        for loc_key, forecast in location_data.items():
            display_forecast(forecast, LOCATIONS[loc_key]["name"])


if __name__ == "__main__":
    main()
