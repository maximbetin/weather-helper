"""Utility functions for displaying weather data and formatting output."""

from colorama import Fore, Style
from datetime import datetime
import pytz
from collections import Counter

from config import LOCATIONS, TIMEZONE, DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR
from weather_utils import get_standardized_weather_desc, find_weather_blocks

def get_rating_info(score):
    """Return standardized rating description and color based on score.

    Args:
        score: Numerical score to convert to rating

    Returns:
        tuple: (rating_text, color_code)
    """
    if score >= 6:
        return "Excellent", Fore.LIGHTGREEN_EX
    elif score >= 3:
        return "Good", Fore.GREEN
    elif score >= 0:
        return "Fair", Fore.YELLOW
    elif score >= -3:
        return "Poor", Fore.LIGHTRED_EX
    else:
        return "Avoid", Fore.RED

def get_weather_description(scores):
    """Generate a weather description based on hour counts.

    Args:
        scores: Day scores dictionary with sunny_hours, partly_cloudy_hours, etc.

    Returns:
        str: Text description of the day's weather
    """
    # Determine if precipitation is likely enough to mention
    precip_warning = ""
    if scores["avg_precip_prob"] is not None and scores["avg_precip_prob"] > 40:
        precip_warning = f" - {scores['avg_precip_prob']:.0f}% rain"

    # Determine primary weather condition
    if scores["sunny_hours"] > scores["partly_cloudy_hours"] and scores["sunny_hours"] > scores["rainy_hours"]:
        return "Sunny" + precip_warning
    elif scores["partly_cloudy_hours"] > scores["sunny_hours"] and scores["partly_cloudy_hours"] > scores["rainy_hours"]:
        return "P.Cloudy" + precip_warning
    elif scores["rainy_hours"] > 0:
        return f"Rain ({scores['rainy_hours']}h)"
    else:
        return "Mixed" + precip_warning

def display_forecast(forecast_data, location_name, compare_mode=False):
    """Display weather forecast for a location.

    Args:
        forecast_data: Processed forecast data dictionary
        location_name: Name of the location to display
        compare_mode: Whether to show abbreviated output for comparison view
    """
    if not forecast_data:
        print(f"{Fore.RED}No forecast data available for {location_name}{Style.RESET_ALL}")
        return

    daily_forecasts = forecast_data["daily_forecasts"]
    day_scores = forecast_data["day_scores"]

    # Display location header
    print(f"\n{Fore.CYAN}{location_name}{Style.RESET_ALL}")

    # Sort days chronologically
    for date in sorted(daily_forecasts.keys()):
        if date not in day_scores:
            continue

        scores = day_scores[date]
        date_str = date.strftime("%a, %d %b")

        # Get rating and description
        rating, color = get_rating_info(scores["avg_score"])
        weather_desc = get_weather_description(scores)

        # Format temperature range
        temp_str = format_temperature_range(scores["min_temp"], scores["max_temp"])

        # Print the day summary
        print(f"{date_str} {color}[{rating}]{Style.RESET_ALL} {temp_str} - {weather_desc}")

        # In comparison mode, don't show hourly details
        if compare_mode:
            continue

        # Show best and worst time blocks
        display_day_blocks(daily_forecasts[date], scores["avg_score"])

def format_temperature_range(min_temp, max_temp):
    """Format temperature range string.

    Args:
        min_temp: Minimum temperature value
        max_temp: Maximum temperature value

    Returns:
        str: Formatted temperature range string
    """
    if min_temp is not None and max_temp is not None:
        return f"{min_temp:>4.1f}°C - {max_temp:>4.1f}°C"
    return "N/A"

def display_day_blocks(hours, day_avg_score):
    """Display best and worst time blocks for a day.

    Args:
        hours: List of hourly forecast data
        day_avg_score: Average score for the day
    """
    # Focus on daylight hours
    daylight_hours = sorted(
        [h for h in hours if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
        key=lambda x: x["hour"]
    )

    if not daylight_hours:
        return

    # Calculate total score for each hour
    for hour in daylight_hours:
        hour["total_score"] = sum(
            score for score_name, score in hour.items()
            if score_name.endswith("_score") and isinstance(score, (int, float))
        )

    # Find blocks with similar weather
    weather_blocks = find_weather_blocks(daylight_hours)

    # Get best and worst times
    best_block, worst_block = find_day_blocks(weather_blocks)

    # Display best time block
    if best_block:
        block, weather_type = best_block
        start_time = block[0]["time"].strftime("%H:%M")
        end_time = block[-1]["time"].strftime("%H:%M")
        full_time = f"{start_time} - {end_time}"
        print(f"   Best: {Fore.GREEN}{full_time:<4}{Style.RESET_ALL}")

    # Display worst time only if it's a good day with a specific bad period
    if worst_block and day_avg_score >= 0:
        block, weather_type = worst_block
        start_time = block[0]["time"].strftime("%H:%M")
        end_time = block[-1]["time"].strftime("%H:%M")
        full_time = f"{start_time} - {end_time}"
        print(f"  Avoid: {Fore.RED}{full_time:<4}{Style.RESET_ALL}")

def find_day_blocks(weather_blocks):
    """Find the best and worst blocks for a day.

    Args:
        weather_blocks: List of (block, weather_type) tuples

    Returns:
        tuple: (best_block, worst_block) where each is (block, weather_type) or None
    """
    best_block = None
    worst_block = None
    best_score = float('-inf')
    worst_score = float('inf')

    # Identify blocks with consistently good or bad weather scores
    for block, weather_type in weather_blocks:
        if len(block) < 2:  # Skip single hour blocks
            continue

        avg_block_score = sum(h["total_score"] for h in block) / len(block)

        # Find single best block
        if avg_block_score > best_score and (weather_type in ["sunny", "cloudy"] or avg_block_score >= 0):
            best_score = avg_block_score
            best_block = (block, weather_type)

        # Find single worst block
        if avg_block_score < worst_score and (weather_type == "rainy" or avg_block_score < 0):
            worst_score = avg_block_score
            worst_block = (block, weather_type)

    return best_block, worst_block

def compare_locations(location_data, date_filter=None):
    """Compare weather conditions across multiple locations for planning purposes.

    Args:
        location_data: Dictionary of processed forecasts by location
        date_filter: Specific date to compare (defaults to today)
    """
    # If no date filter provided, use today
    if not date_filter:
        date_filter = datetime.now(pytz.timezone(TIMEZONE)).date()

    print(f"\nBest locations for {date_filter.strftime('%A, %d %b')}")

    # Get data for the specified date across all locations
    date_data = []
    for location_name, forecast in location_data.items():
        if not forecast or not forecast["day_scores"]:
            continue

        for date, scores in forecast["day_scores"].items():
            if date == date_filter:
                date_data.append(scores)
                break

    # Sort locations by score (best to worst)
    date_data.sort(key=lambda x: x["avg_score"], reverse=True)

    if not date_data:
        print(f"\n{Fore.YELLOW}No data available for this date.{Style.RESET_ALL}")
        return

    # Format and display comparison table
    display_comparison_table(date_data)

def display_comparison_table(date_data):
    """Display a formatted comparison table of locations.

    Args:
        date_data: List of day score dictionaries for the same date
    """
    # Find longest location name for proper formatting
    max_location_length = max(len(data["location"]) for data in date_data)
    location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

    # Print table header with proper spacing
    print(f"\n{'Location':<{location_width}} {'Rating':<10} {'Temp':<15} {'Weather':<13} {'Score':>6}")
    print(f"{'-'*location_width} {'-'*10} {'-'*15} {'-'*13} {'-'*6}")

    for data in date_data:
        location = data["location"]

        # Get rating and color
        rating, color = get_rating_info(data["avg_score"])

        # Weather description
        weather = get_weather_description(data)

        # Temperature range
        temp = format_temperature_range(data["min_temp"], data["max_temp"])

        # Format score
        score_str = f"{data['avg_score']:.1f}"

        # Print row with proper colors
        print(f"{Fore.CYAN}{location:<{location_width}}{Style.RESET_ALL} {color}{rating:<10}{Style.RESET_ALL} {temp:<15} {weather:<13} {score_str:>6}")

def list_locations():
    """List all available locations."""
    print(f"\n{Fore.CYAN}Available locations:{Style.RESET_ALL}")
    for key, loc in LOCATIONS.items():
        print(f"  {key} - {Fore.CYAN}{loc['name']}{Style.RESET_ALL}")

def display_best_times_recommendation(location_data):
    """Display a simple recommendation for when to go out this week.

    Args:
        location_data: Dictionary of processed forecasts by location
    """
    from forecast_analysis import recommend_best_times
    all_periods = recommend_best_times(location_data)

    if not all_periods:
        print(f"\n{Fore.YELLOW}No ideal outdoor times found for this week.{Style.RESET_ALL}")
        print("Try checking individual locations for more details.")
        return

    print(f"\n{Fore.CYAN}Best times for outdoor activities this week:{Style.RESET_ALL}")

    # Group recommendations by day
    days_shown = set()

    # Show top overall recommendations first (max 5)
    top_recommendations = all_periods[:5]

    for period in top_recommendations:
        display_recommendation_period(period)
        days_shown.add(period["date"])

    # Show if there are more options not displayed
    remaining = len(all_periods) - len(top_recommendations)
    if remaining > 0:
        print(f"\n{Fore.YELLOW}Plus {remaining} more options. Check specific locations for details.{Style.RESET_ALL}")

def display_recommendation_period(period):
    """Display a single recommendation period.

    Args:
        period: Dictionary containing recommendation period data
    """
    hours = period["hours"]
    if len(hours) < 2:
        return

    day_name = period["day_name"]
    date = period["date"].strftime("%d %b")
    location = period["location"]
    start_time = hours[0]["time"].strftime("%H:%M")
    end_time = hours[-1]["time"].strftime("%H:%M")
    duration = len(hours)

    # Get average temperature
    temps = [h["temp"] for h in hours if isinstance(h["temp"], (int, float))]
    temp_str = f"{sum(temps)/len(temps):.1f}°C" if temps else "N/A"

    # Get rating and color for score
    rating, color = get_rating_info(period["avg_score"])

    # Print recommendation
    print(f"\n{day_name}, {date} at {Fore.CYAN}{location}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{start_time}-{end_time}{Style.RESET_ALL} ({duration}h) {color}[{rating}]{Style.RESET_ALL} {temp_str}")

    # Get the dominant weather symbol
    symbols = [h["symbol"] for h in hours if isinstance(h["symbol"], str)]
    if symbols:
        most_common = Counter(symbols).most_common(1)[0][0]
        print(f"  Weather: {get_standardized_weather_desc(most_common)}")