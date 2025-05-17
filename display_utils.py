"""Utility functions for displaying weather data and formatting output."""

from colorama import Fore, Style
from datetime import datetime
import pytz

from config import LOCATIONS, TIMEZONE, DAYLIGHT_START_HOUR, DAYLIGHT_END_HOUR
from weather_utils import get_standardized_weather_desc

def get_rating_info(score):
    """Return standardized rating description and color based on score."""
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

def display_forecast(forecast_data, location_name, compare_mode=False):
    """Display weather forecast for a location."""
    if not forecast_data:
        return

    daily_forecasts = forecast_data["daily_forecasts"]
    day_scores = forecast_data["day_scores"]

    # Consistently color location names
    print(f"\n{Fore.CYAN}{location_name}{Style.RESET_ALL}")

    # Sort days chronologically
    for date in sorted(daily_forecasts.keys()):
        if date not in day_scores:
            continue

        scores = day_scores[date]
        date_str = date.strftime("%a, %d %b")

        # Use centralized rating function
        rating, color = get_rating_info(scores["avg_score"])

        # Determine overall weather description
        precip_warning = ""
        if scores["avg_precip_prob"] is not None and scores["avg_precip_prob"] > 40:
            precip_warning = f" - {scores['avg_precip_prob']:.0f}% rain"

        if scores["sunny_hours"] > scores["partly_cloudy_hours"] and scores["sunny_hours"] > scores["rainy_hours"]:
            weather_desc = "Sunny" + precip_warning
        elif scores["partly_cloudy_hours"] > scores["sunny_hours"] and scores["partly_cloudy_hours"] > scores["rainy_hours"]:
            weather_desc = "P.Cloudy" + precip_warning
        elif scores["rainy_hours"] > 0:
            weather_desc = f"Rain ({scores['rainy_hours']}h)"
        else:
            weather_desc = "Mixed" + precip_warning

        # Use min-max temperature range
        temp_str = ""
        if scores["min_temp"] is not None and scores["max_temp"] is not None:
          temp_str = f"{scores['min_temp']:>4.1f}°C - {scores['max_temp']:>4.1f}°C"
        else:
          temp_str = "N/A"

        # Print the day summary with color and weather description
        print(f"{date_str} {color}[{rating}]{Style.RESET_ALL} {temp_str} - {weather_desc}")

        # In comparison mode, don't show hourly details
        if compare_mode:
            continue

        # Sort and identify best and worst blocks
        daylight_hours = sorted([h for h in daily_forecasts[date] if DAYLIGHT_START_HOUR <= h["hour"] <= DAYLIGHT_END_HOUR],
                              key=lambda x: x["hour"])

        if not daylight_hours:
            continue

        # Score each hour for outdoor activity
        for hour in daylight_hours:
            hour["total_score"] = sum(score for score_name, score in hour.items()
                                  if score_name.endswith("_score") and isinstance(score, (int, float)))

        # Find blocks with similar weather
        from weather_utils import find_weather_blocks
        weather_blocks = find_weather_blocks(daylight_hours)

        # Get best and worst times (highest and lowest scoring blocks)
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

        # Display best time block
        if best_block:
            block, weather_type = best_block
            start_time = block[0]["time"].strftime("%H:%M")
            end_time = block[-1]["time"].strftime("%H:%M")
            print(f"  Best: {Fore.GREEN}{start_time}-{end_time}{Style.RESET_ALL}")

        # Display worst time only if it's a good day with a specific bad period
        if worst_block and scores["avg_score"] >= 0:
            block, weather_type = worst_block
            start_time = block[0]["time"].strftime("%H:%M")
            end_time = block[-1]["time"].strftime("%H:%M")
            print(f"  Avoid: {Fore.RED}{start_time}-{end_time}{Style.RESET_ALL}")

def compare_locations(location_data, date_filter=None):
    """Compare weather conditions across multiple locations for planning purposes."""
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

    # Find longest location name for proper formatting
    max_location_length = max(len(data["location"]) for data in date_data)
    location_width = max(max_location_length + 2, 17)  # Minimum 17 chars

    # Print table header with proper spacing
    print(f"\n{'Location':<{location_width}} {'Rating':<10} {'Temp':<15} {'Weather':<13} {'Score':>6}")
    print(f"{'-'*location_width} {'-'*10} {'-'*15} {'-'*13} {'-'*6}")

    for data in date_data:
        location = data["location"]

        # Use centralized rating function
        rating, color = get_rating_info(data["avg_score"])

        # Weather description
        if data["sunny_hours"] > data["partly_cloudy_hours"] and data["sunny_hours"] > data["rainy_hours"]:
            weather = "Sunny"
        elif data["partly_cloudy_hours"] > data["sunny_hours"] and data["partly_cloudy_hours"] > data["rainy_hours"]:
            weather = "P.Cloudy"
        elif data["rainy_hours"] > 0:
            weather = f"Rain ({data['rainy_hours']}h)"
        else:
            weather = "Mixed"

        # Temperature range
        temp = "N/A"
        if data["min_temp"] is not None and data["max_temp"] is not None:
            temp = f"{data['min_temp']:.1f}°C - {data['max_temp']:.1f}°C"

        # Format score
        score_str = f"{data['avg_score']:.1f}"

        # Always color location with cyan
        print(f"{Fore.CYAN}{location:<{location_width}}{Style.RESET_ALL} {color}{rating:<10}{Style.RESET_ALL} {temp:<15} {weather:<13} {score_str:>6}")

def list_locations():
    """List all available locations."""
    print(f"\n{Fore.CYAN}Available locations:{Style.RESET_ALL}")
    for key, loc in LOCATIONS.items():
        print(f"  {key} - {Fore.CYAN}{loc['name']}{Style.RESET_ALL}")

def display_best_times_recommendation(location_data):
    """Display a simple recommendation for when to go out this week."""
    from forecast_analysis import recommend_best_times
    all_periods = recommend_best_times(location_data)

    if not all_periods:
        print(f"\n{Fore.YELLOW}No ideal outdoor times found for this week.{Style.RESET_ALL}")
        print("Try checking individual locations for more details.")
        return

    print(f"\n{Fore.CYAN}BEST TIMES TO GO OUT IN THE NEXT 7 DAYS:{Style.RESET_ALL}")

    # Group periods by date
    from collections import defaultdict
    days = defaultdict(list)
    for period in all_periods:
        days[period["date"]].append(period)

    # Extract more options per day, including those with lower scores
    filtered_periods = []
    for date, periods in sorted(days.items()):
        periods.sort(key=lambda x: x["score"], reverse=True)
        for p in periods[:5]:  # Take top 5 periods per day
            filtered_periods.append(p)

    # Find the longest location name for proper alignment
    max_location_length = max(len(period["location"]) for period in filtered_periods) if filtered_periods else 15
    location_width = max(max_location_length + 2, 17)  # Minimum 17 chars
    weather_width = 20  # Field width for weather + temp alignment

    # Print header row
    print(f"{'#':<3} {'Day & Date':<16} {'Time':<15} {'Duration':<10} {'Location':<{location_width}} {'Weather':<{weather_width}} {'Score':>6}")
    print(f"{'-'*3} {'-'*16} {'-'*15} {'-'*10} {'-'*location_width} {'-'*weather_width} {'-'*6}")

    current_date = None

    for i, period in enumerate(filtered_periods, 1):
        if current_date and current_date != period["date"]:
            print()  # Add line break between dates
        current_date = period["date"]

        date_str = period["date"].strftime("%d %b")
        day_name = period["day_name"][:3]
        day_date = f"{day_name}, {date_str}"

        start_str = period["start_time"].strftime("%H:%M")
        end_str = period["end_time"].strftime("%H:%M")
        time_range = f"{start_str}-{end_str}"

        rating, color = get_rating_info(period["score"])
        duration_str = f"{period['duration']} hours"

        weather_desc = get_standardized_weather_desc(period["dominant_symbol"])[:12]  # Limit length
        weather_desc = f"{weather_desc:<12}"  # Left-align

        temp_desc = ""
        if period["avg_temp"] is not None:
            temp_desc = f"{period['avg_temp']:>5.1f}°C"  # Right-align temp

        weather_with_temp = f"{weather_desc} {temp_desc}"  # Combined field
        score_str = f"{period['score']:.1f}"

        # Print formatted row
        print(
            f"{i:<3} "
            f"{color}{day_date:<16}{Style.RESET_ALL} "
            f"{time_range:<15} "
            f"{duration_str:<10} "
            f"{Fore.CYAN}{period['location']:<{location_width}}{Style.RESET_ALL} "
            f"{weather_with_temp:<{weather_width}} "
            f"{score_str:>6}"
        )