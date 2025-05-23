"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""
import argparse
from datetime import datetime, timedelta
from typing import Any

import pytz
import requests
from colorama import Fore, Style, init

LOCATIONS: dict[str, dict[str, str | float]] = {
    "oviedo": {"display_name": "Oviedo", "lat": 43.3619, "lon": -5.8494},
    "llanes": {"display_name": "Llanes", "lat": 43.4200, "lon": -4.7550},
    "aviles": {"display_name": "Avilés", "lat": 43.5547, "lon": -5.9248},
    "somiedo": {"display_name": "Somiedo", "lat": 43.0981, "lon": -6.2550},
    "teverga": {"display_name": "Teverga", "lat": 43.1578, "lon": -6.0867},
    "taramundi": {"display_name": "Taramundi", "lat": 43.3583, "lon": -7.1083},
    "ribadesella": {"display_name": "Ribadesella", "lat": 43.4675, "lon": -5.0553},
    "tapia": {"display_name": "Tapia de Casariego", "lat": 43.5700, "lon": -6.9436},
    "cangas_de_onis": {"display_name": "Cangas de Onís", "lat": 43.3507, "lon": -5.1356},
    "lagos_covadonga": {"display_name": "Lagos de Covadonga", "lat": 43.2728, "lon": -4.9906},
}

WEATHER_SCORES: dict[str, int] = {
    "clearsky": 10,
    "fair": 8,
    "partlycloudy": 6,
    "cloudy": 3,
    "lightrain": -2,
    "lightrainshowers": -2,
    "lightsleet": -3,
    "lightsleetshowers": -3,
    "lightsnow": -3,
    "lightsnowshowers": -3,
    "rain": -5,
    "rainshowers": -5,
    "sleet": -6,
    "sleetshowers": -6,
    "snow": -6,
    "snowshowers": -6,
    "heavyrain": -10,
    "heavyrainshowers": -10,
    "heavysleet": -10,
    "heavysleetshowers": -10,
    "heavysnow": -10,
    "heavysnowshowers": -10,
    "fog": -4,
    "thunderstorm": -15,
}

SYMBOL_MAP: dict[str, str] = {
    "rain": "Rain",
    "snow": "Snow",
    "fog": "Foggy",
    "sleet": "Sleet",
    "cloudy": "Cloudy",
    "clearsky": "Sunny",
    "thunderstorm": "Thunderstorm",
    "fair": "Mostly Sunny",
    "lightrain": "Light Rain",
    "heavyrain": "Heavy Rain",
    "lightsnow": "Light Snow",
    "heavysnow": "Heavy Snow",
    "lightsleet": "Light Sleet",
    "heavysleet": "Heavy Sleet",
    "rainshowers": "Rain Showers",
    "snowshowers": "Snow Showers",
    "partlycloudy": "Partly Cloudy",
    "lightrainshowers": "Light Rain Showers",
    "heavyrainshowers": "Heavy Rain Showers",
    "lightsnowshowers": "Light Snow Showers",
    "heavysnowshowers": "Heavy Snow Showers",
    "lightsleetshowers": "Light Sleet Showers",
    "sleetshowers": "Sleet Showers",
    "heavysleetshowers": "Heavy Sleet Showers",
}

RAIN_SYMBOLS: list[str] = [
    "lightrain", "lightrainshowers", "rain", "rainshowers", "heavyrain", "heavyrainshowers"
]

HEADERS: dict[str, str] = {"User-Agent": "DailyHelper/1.0"}
API_URL: str = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
TIMEZONE: str = "Europe/Madrid"

init()  # Initialize colorama for colored terminal output


def fetch_weather_data(location: dict[str, str | float]) -> dict[str, Any] | None:
    """Fetch weather data for a specific location."""
    lat = location["lat"]
    lon = location["lon"]

    # Construct API URL
    url = f"{API_URL}?lat={lat}&lon={lon}"

    # Fetch data with error handling
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error fetching weather data for {location['display_name']}: {e}{Style.RESET_ALL}")
        return None
    except ValueError as e:
        print(f"{Fore.RED}Error parsing JSON response for {location['display_name']}: {e}{Style.RESET_ALL}")
        return None


def get_weather_score(
    symbol_code: str | None,
    temperature: float | None = None,
    wind_speed: float | None = None,
    precipitation_amount: float | None = None,
) -> int:
    """Return weather score based on symbol, temperature, wind speed, and precipitation."""
    base_score: int
    if not symbol_code or not isinstance(symbol_code, str):
        base_score = 0  # Default score for unknown or invalid symbol
    else:
        base_symbol = symbol_code.split('_')[0]  # Extract base symbol
        base_score = WEATHER_SCORES.get(base_symbol, 0)  # Get score from symbol or 0

    temp_adjustment = 0
    if temperature is not None:
        if temperature < 5 or temperature > 35:  # Extreme cold or extreme hot
            temp_adjustment = -5
        elif (5 <= temperature < 10) or (30 < temperature <= 35):  # Cold or hot
            temp_adjustment = -3
        elif 10 <= temperature < 15:  # Cool
            temp_adjustment = -1
        elif (15 <= temperature < 20) or (25 < temperature <= 30):  # Mildly warm or warm
            temp_adjustment = 1
        elif 20 <= temperature <= 25:  # Ideal
            temp_adjustment = 2

    wind_adjustment = 0
    if wind_speed is not None:
        if wind_speed < 2:
            wind_adjustment = 1
        elif 5 <= wind_speed < 8:
            wind_adjustment = -1
        elif 8 <= wind_speed < 11:
            wind_adjustment = -3
        elif 11 <= wind_speed < 14:
            wind_adjustment = -5
        elif wind_speed >= 14:
            wind_adjustment = -8

    precip_adjustment = 0
    if base_score != 0:  # Only apply precipitation adjustment if there is a base symbol
        if isinstance(symbol_code, str):
            base_symbol_for_precip = symbol_code.split('_')[0]
            if base_symbol_for_precip in RAIN_SYMBOLS and precipitation_amount is not None and precipitation_amount > 0:
                if 0 < precipitation_amount <= 0.5:
                    precip_adjustment = -1
                elif 0.5 < precipitation_amount <= 2.0:
                    precip_adjustment = -2
                elif 2.0 < precipitation_amount <= 4.0:
                    precip_adjustment = -3
                elif precipitation_amount > 4.0:
                    precip_adjustment = -4

    return base_score + temp_adjustment + wind_adjustment + precip_adjustment


def get_score_category(score: int | float) -> str:
    """Convert numerical score to a human-readable category."""
    int_score = int(score)
    if int_score >= 12:
        return f"{Fore.GREEN}[Excellent]{Style.RESET_ALL}"
    elif int_score >= 8:
        return f"{Fore.GREEN}[Very Good]{Style.RESET_ALL}"
    elif int_score >= 5:
        return f"{Fore.GREEN}[Good]{Style.RESET_ALL}"
    elif int_score >= 2:
        return f"{Fore.YELLOW}[Fair]{Style.RESET_ALL}"
    elif int_score >= 0:
        return f"{Fore.YELLOW}[Okay]{Style.RESET_ALL}"
    elif int_score >= -3:
        return f"{Fore.RED}[Poor]{Style.RESET_ALL}"
    elif int_score >= -7:
        return f"{Fore.RED}[Bad]{Style.RESET_ALL}"
    else:
        return f"{Fore.RED}[Very Bad]{Style.RESET_ALL}"


def format_weather_block_for_display(
    start_time: datetime,
    end_time: datetime,  # This is the timestamp of the start of the last hour in the block
    avg_score: float,
    avg_temp: float | None,
    weather_description: str,
    duration_hours: float | None = None  # Optional, can be calculated if not provided
) -> str:
    """Formats a single weather block's data into a display string."""
    start_str = start_time.strftime('%H:%M')
    # For a block like 10:00, 11:00, 12:00, end_time is 12:00. Display as 10:00 - 12:00.
    # The duration implies it covers the full hour of end_time.
    end_str = end_time.strftime('%H:%M')

    if duration_hours is None:
        # If start and end are the same, it's a 1-hour block.
        # If different, add 1 because end_time is the *start* of the last hour slot.
        duration_hours = (end_time - start_time).total_seconds() / 3600 + 1

    duration_display = f"({duration_hours:.0f}h)"

    avg_temp_display = f"{avg_temp:.1f}°C" if avg_temp is not None else "N/A"
    score_category_display = get_score_category(avg_score)

    return (f"  {Fore.CYAN}{start_str} - {end_str}{Style.RESET_ALL} {duration_display}: "
            f"{weather_description}, {avg_temp_display}, "
            f"Score: {score_category_display} ({avg_score:.1f})")


def get_standardized_weather_desc(symbol: str | None) -> str:
    """Return standardized weather description from symbol code."""
    if not symbol or not isinstance(symbol, str):
        return "Unknown"

    # Check for direct matches in the global SYMBOL_MAP
    if symbol in SYMBOL_MAP:
        return SYMBOL_MAP[symbol]
    else:
        # Fallback: Capitalize and replace underscores for any other unmapped symbols
        base_symbol_only = symbol.split('_')[0]  # Use only the base part before underscore for lookup or formatting
        if base_symbol_only in SYMBOL_MAP:  # Check SYMBOL_MAP again with only base symbol
            return SYMBOL_MAP[base_symbol_only]
        return base_symbol_only.replace("_", " ").capitalize()


def calculate_location_rank_data(weather_data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Calculates ranking data for a single location based on good weather blocks.
    Considers weather for the next 48 hours for ranking.
    """
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        return {'rank_score': 0, 'good_blocks': [], 'error': 'No timeseries data'}

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)
    now_madrid = datetime.now(madrid_tz)
    ranking_horizon_end = now_madrid + timedelta(hours=48)

    good_blocks_details = []
    current_block_data = None
    total_rank_score = 0.0

    for entry in timeseries:
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        if local_time > ranking_horizon_end:  # Only consider next 48h for ranking
            if current_block_data:  # Finalize any open block before breaking
                duration_hours = (current_block_data['last_good_time'] - current_block_data['start_time']).total_seconds() / 3600 + 1  # +1 for inclusive hour
                avg_score_block = sum(current_block_data['scores']) / len(current_block_data['scores'])
                valid_temps_block = [t for t in current_block_data['temps'] if t is not None]
                avg_temp_block = sum(valid_temps_block) / len(valid_temps_block) if valid_temps_block else None

                block_info = {
                    'start_time': current_block_data['start_time'],
                    'end_time': current_block_data['last_good_time'],  # This is the start of the last hour in block
                    'duration_hours': duration_hours,
                    'avg_score': avg_score_block,
                    'avg_temp': avg_temp_block,
                    'weather': get_standardized_weather_desc(current_block_data['symbols'][0]),
                }
                good_blocks_details.append(block_info)
                total_rank_score += avg_score_block * duration_hours
                current_block_data = None
            break

        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        symbol_code_1h = next_1h_summary.get('symbol_code')

        if not symbol_code_1h:
            if current_block_data:
                duration_hours = (current_block_data['last_good_time'] - current_block_data['start_time']).total_seconds() / 3600 + 1
                avg_score_block = sum(current_block_data['scores']) / len(current_block_data['scores'])
                valid_temps_block = [t for t in current_block_data['temps'] if t is not None]
                avg_temp_block = sum(valid_temps_block) / len(valid_temps_block) if valid_temps_block else None
                block_info = {
                    'start_time': current_block_data['start_time'],
                    'end_time': current_block_data['last_good_time'],
                    'duration_hours': duration_hours,
                    'avg_score': avg_score_block,
                    'avg_temp': avg_temp_block,
                    'weather': get_standardized_weather_desc(current_block_data['symbols'][0]),
                }
                good_blocks_details.append(block_info)
                total_rank_score += avg_score_block * duration_hours
                current_block_data = None
            continue

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')
        score = get_weather_score(symbol_code_1h, temp, wind_speed_instant, precip_amount_1h)

        if score >= 5:  # Good weather
            if current_block_data is None:
                current_block_data = {
                    'start_time': local_time,
                    'scores': [score],
                    'temps': [temp if temp is not None else 0.0],  # Store 0 if None, handle in avg calc
                    'symbols': [symbol_code_1h],
                    'last_good_time': local_time
                }
            else:
                current_block_data['scores'].append(score)
                current_block_data['temps'].append(temp if temp is not None else 0.0)
                current_block_data['symbols'].append(symbol_code_1h)
                current_block_data['last_good_time'] = local_time
        else:  # Not good weather, end current block if one exists
            if current_block_data:
                duration_hours = (current_block_data['last_good_time'] - current_block_data['start_time']).total_seconds() / 3600 + 1
                avg_score_block = sum(current_block_data['scores']) / len(current_block_data['scores'])
                valid_temps_block = [t for t in current_block_data['temps'] if t is not None]
                avg_temp_block = sum(valid_temps_block) / len(valid_temps_block) if valid_temps_block else None

                block_info = {
                    'start_time': current_block_data['start_time'],
                    'end_time': current_block_data['last_good_time'],
                    'duration_hours': duration_hours,
                    'avg_score': avg_score_block,
                    'avg_temp': avg_temp_block,
                    'weather': get_standardized_weather_desc(current_block_data['symbols'][0]),
                }
                good_blocks_details.append(block_info)
                total_rank_score += avg_score_block * duration_hours
                current_block_data = None

    # After loop, check if a block was active till the end of horizon or data
    if current_block_data:
        duration_hours = (current_block_data['last_good_time'] - current_block_data['start_time']).total_seconds() / 3600 + 1
        avg_score_block = sum(current_block_data['scores']) / len(current_block_data['scores'])
        valid_temps_block = [t for t in current_block_data['temps'] if t is not None]  # Recalc valid temps
        avg_temp_block = sum(valid_temps_block) / len(valid_temps_block) if valid_temps_block else None
        block_info = {
            'start_time': current_block_data['start_time'],
            'end_time': current_block_data['last_good_time'],
            'duration_hours': duration_hours,
            'avg_score': avg_score_block,
            'avg_temp': avg_temp_block,
            'weather': get_standardized_weather_desc(current_block_data['symbols'][0]),
        }
        good_blocks_details.append(block_info)
        total_rank_score += avg_score_block * duration_hours

    return {'rank_score': total_rank_score, 'good_blocks': good_blocks_details}


def display_ranked_locations(all_locations_data: list[tuple[str, dict[str, Any]]], top_n: int = 20) -> None:
    """Displays locations ranked by their weather suitability."""
    print(f"\n{Fore.CYAN}--- Top Locations for Outdoor Activities (Next 48 Hours) ---{Style.RESET_ALL}")

    if not all_locations_data:
        print(f"{Fore.YELLOW}No location data to rank.{Style.RESET_ALL}")
        return

    # Filter out locations with errors or no good blocks for ranking
    # And sort by rank_score descending
    sorted_locations = sorted(
        [data for data in all_locations_data if not data[1].get('error') and data[1]['rank_score'] > 0],
        key=lambda x: x[1]['rank_score'],
        reverse=True
    )

    if not sorted_locations:
        print(f"{Fore.YELLOW}No locations with suitable upcoming weather found for ranking.{Style.RESET_ALL}")
        return

    for i, (location_name, data) in enumerate(sorted_locations[:top_n]):
        rank = i + 1
        rank_score_display = f"{data['rank_score']:.1f}"

        # Find the best block (e.g., longest duration, then highest score)
        best_block_info_str = "No significant good weather periods."
        if data['good_blocks']:
            # Sort blocks by duration, then by avg_score
            best_block = sorted(data['good_blocks'], key=lambda b: (b['duration_hours'], b['avg_score']), reverse=True)[0]
            start_t = best_block['start_time'].strftime('%a %H:%M')
            end_t = (best_block['end_time'] + timedelta(hours=1)).strftime('%H:%M')  # Display end of block inclusively
            duration_h = best_block['duration_hours']
            avg_s = best_block['avg_score']
            avg_t_display = f"{best_block['avg_temp']:.1f}°C" if best_block['avg_temp'] is not None else 'N/A'
            weather_b = best_block['weather']
            best_block_info_str = (
                f"Best period: {start_t}-{end_t} ({duration_h:.0f}h), "
                f"Avg Score: {avg_s:.1f}, {avg_t_display}, {weather_b}"
            )

        print(f"{Fore.GREEN}{rank}. {location_name}{Style.RESET_ALL} "
              f"(Rank Score: {Fore.YELLOW}{rank_score_display}{Style.RESET_ALL})")
        # print(f"   {best_block_info_str}") # Old way of showing just one best block

        # New: Display all good blocks for this ranked location using the unified formatter
        if data['good_blocks']:
            print(f"   {Fore.BLUE}Key Good Weather Periods (next 48h):{Style.RESET_ALL}")
            current_rank_display_day: str | None = None
            for good_block in sorted(data['good_blocks'], key=lambda b: b['start_time']):  # Sort by time

                block_day = good_block['start_time'].strftime('%A, %Y-%m-%d')
                if block_day != current_rank_display_day:
                    # Indent day header slightly for ranked list context
                    print(f"     {Fore.MAGENTA}{block_day}{Style.RESET_ALL}")
                    current_rank_display_day = block_day

                # format_weather_block_for_display expects 'weather_description'
                # good_block has 'weather'
                formatted_block_str = format_weather_block_for_display(
                    start_time=good_block['start_time'],
                    end_time=good_block['end_time'],  # 'end_time' in good_block is last good hour start
                    avg_score=good_block['avg_score'],
                    avg_temp=good_block['avg_temp'],
                    weather_description=good_block['weather'],  # Key name matches
                    duration_hours=good_block['duration_hours']
                )
                # Indent the block info further
                print(f"   {formatted_block_str.strip()}")  # strip to remove its leading spaces if any
        else:
            print(f"   {Fore.YELLOW}No significant good weather periods identified for ranking.{Style.RESET_ALL}")

        if i < top_n - 1 and i < len(sorted_locations) - 1:
            print()  # Add a space between ranked location entries


def display_hourly_forecast_24h(weather_data: dict[str, Any] | None, location_name: str) -> None:
    """Displays detailed hourly forecast for the next 24 hours for a specific location."""
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        print(f"{Fore.YELLOW}No timeseries data to display for {location_name}.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Hourly Forecast for {location_name} (Next 24 Hours):{Style.RESET_ALL}")

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)
    now_madrid = datetime.now(madrid_tz)
    forecast_end_time = now_madrid + timedelta(hours=24)

    current_display_day: str | None = None
    displayed_an_hour = False

    for entry in timeseries:
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        if local_time < now_madrid:  # Skip past events
            continue
        if local_time > forecast_end_time:  # Don't go beyond 24 hours from now
            break

        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        symbol_code_1h = next_1h_summary.get('symbol_code')

        if not symbol_code_1h:
            continue

        base_symbol = symbol_code_1h.split('_')[0]
        weather_display = get_standardized_weather_desc(symbol_code_1h)  # Use full symbol

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')

        score = get_weather_score(symbol_code_1h, temp, wind_speed_instant, precip_amount_1h)
        score_category = get_score_category(score)

        day_name_full = local_time.strftime('%A, %Y-%m-%d')
        if day_name_full != current_display_day:
            if displayed_an_hour:
                print()  # Add space if not the very first day header
            print(f"{Fore.MAGENTA}{day_name_full}{Style.RESET_ALL}")
            current_display_day = day_name_full

        temp_display = f"{temp}°C" if temp is not None else "N/A"
        wind_display = f"{wind_speed_instant} m/s" if wind_speed_instant is not None else "N/A"
        precip_display = f"{precip_amount_1h} mm" if precip_amount_1h is not None else "N/A"

        print(f"{Fore.CYAN}{local_time.strftime('%H:%M')}{Style.RESET_ALL}: "
              f"{score_category}, {temp_display}, Wind: {wind_display}, Precip: {precip_display}, {weather_display}")
        displayed_an_hour = True

    if not displayed_an_hour:
        print(f"{Fore.YELLOW}No forecast data available for the next 24 hours for {location_name}.{Style.RESET_ALL}")


def display_best_times_for_activities(weather_data: dict[str, Any] | None, location_name: str) -> None:
    """Displays the best time ranges for outdoor activities based on a weather score threshold."""
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        print(f"{Fore.YELLOW}No timeseries data to analyze for {location_name}.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Best Time Ranges for Outdoor Activities in {location_name} (Score >= 5):{Style.RESET_ALL}")

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)

    good_time_blocks = []
    current_block_data = None

    for i, entry in enumerate(timeseries):
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        symbol_code_1h = next_1h_summary.get('symbol_code')

        if not symbol_code_1h:
            # If a block was active, and current hour has no symbol, end the block.
            if current_block_data:
                good_time_blocks.append(current_block_data)
                current_block_data = None
            continue

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')
        score = get_weather_score(symbol_code_1h, temp, wind_speed_instant, precip_amount_1h)

        if score >= 5:
            if current_block_data is None:  # New block starts
                current_block_data = {
                    'start_time': local_time,
                    'scores': [score],
                    'temps': [temp],
                    'symbols': [symbol_code_1h],
                    'last_good_time': local_time
                }
            else:  # Continue existing block
                current_block_data['scores'].append(score)
                current_block_data['temps'].append(temp)
                current_block_data['symbols'].append(symbol_code_1h)
                current_block_data['last_good_time'] = local_time
        else:  # Score < 5, so good block (if any) ends
            if current_block_data is not None:
                good_time_blocks.append(current_block_data)
                current_block_data = None

    # If a block was active till the very end of timeseries
    if current_block_data is not None:
        good_time_blocks.append(current_block_data)

    if not good_time_blocks:
        print(f"{Fore.YELLOW}No suitable time ranges with a score of 'Good' or better found for {location_name}.{Style.RESET_ALL}")
        return

    current_display_day: str | None = None
    for block in good_time_blocks:
        avg_score = sum(block['scores']) / len(block['scores'])

        valid_temps = [t for t in block['temps'] if t is not None]
        avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else None

        representative_symbol = block['symbols'][0]  # Use the first symbol of the block
        weather_display = get_standardized_weather_desc(representative_symbol)
        score_category = get_score_category(int(avg_score))

        block_start_time = block['start_time']
        # block_end_time_inclusive is the timestamp of the start of the last good hour slot
        block_end_time_inclusive = block['last_good_time']

        day_name_full = block_start_time.strftime('%A, %Y-%m-%d')
        if day_name_full != current_display_day:
            # Prevent printing an extra newline if it's the first day block
            if current_display_day is not None:
                print()
            print(f"{Fore.MAGENTA}{day_name_full}{Style.RESET_ALL}")
            current_display_day = day_name_full

        start_str = block_start_time.strftime('%H:%M')
        end_str = block_end_time_inclusive.strftime('%H:%M')

        avg_temp_display = f"{avg_temp:.1f}°C" if avg_temp is not None else "N/A"

        if start_str == end_str:  # Single hour block
            print(f"  {Fore.CYAN}{start_str}{Style.RESET_ALL}: "
                  f"{score_category} (Avg Score: {avg_score:.1f}) "
                  f"({avg_temp_display}, {weather_display})")
        else:  # Multi-hour block
            # For display, if block is 10:00, 11:00, 12:00, show as 10:00 - 12:00
            print(f"  {Fore.CYAN}{start_str} - {end_str}{Style.RESET_ALL}: "
                  f"{score_category} (Avg Score: {avg_score:.1f}) "
                  f"({avg_temp_display}, {weather_display})")
    if not good_time_blocks and current_display_day is None:  # Handles if no good blocks at all
        print(f"{Fore.YELLOW}No times with a score of 'Good' or better found for {location_name}.{Style.RESET_ALL}")


def display_timeseries_data(weather_data: dict[str, Any] | None, location_name: str) -> None:
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        print(f"{Fore.YELLOW}No timeseries data to display for {location_name}.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Detailed Timeseries Data for: {location_name}{Style.RESET_ALL}")

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)
    current_display_day: str | None = None

    for _, entry in enumerate(timeseries):
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        # Hourly data extraction
        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        symbol_code_1h = next_1h_summary.get('symbol_code')

        # If no symbol code, skip this entry and do not print it
        if not symbol_code_1h:
            continue

        base_symbol = symbol_code_1h.split('_')[0]
        weather_display = f"{get_standardized_weather_desc(base_symbol)}"

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')

        score = get_weather_score(symbol_code_1h, temp, wind_speed_instant, precip_amount_1h)
        score_category = get_score_category(score)

        # Print day header when it changes
        day_name_full = local_time.strftime('%A, %Y-%m-%d')
        if day_name_full != current_display_day:
            print(f"\n{Fore.MAGENTA}{day_name_full}{Style.RESET_ALL}")
            current_display_day = day_name_full

        temp_display = f"{temp}°C" if temp is not None else "N/A"

        print(f"{Fore.CYAN}{local_time.strftime('%H:%M')}{Style.RESET_ALL}: "
              f"{score_category} ({temp_display}, {weather_display})")


def display_weather_forecast_by_ranges(weather_data: dict[str, Any] | None, location_name: str) -> None:
    """Displays the full weather forecast in condensed time ranges based on consistent weather symbols."""
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        print(f"{Fore.RED}No timeseries data available for {location_name}.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.BLUE}--- Weather Forecast for: {location_name} ---{Style.RESET_ALL}")

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)

    weather_blocks = []
    current_block = None
    # Consider data for a reasonable horizon, e.g., next 7 days, to avoid overly long outputs if API returns extensive data.
    # For now, processing all available in timeseries.

    for i, entry in enumerate(timeseries):
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        current_symbol_code = next_1h_summary.get('symbol_code')

        if not current_symbol_code:  # Should ideally not happen if API is consistent
            if current_block:  # Finalize existing block
                weather_blocks.append(current_block)
                current_block = None
            continue

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')
        score = get_weather_score(current_symbol_code, temp, wind_speed_instant, precip_amount_1h)

        # Define block by consistent base symbol_code
        current_base_symbol = current_symbol_code.split('_')[0]

        if current_block is None:
            current_block = {
                'start_time': local_time,
                'base_symbol': current_base_symbol,
                'scores': [score],
                'temps': [temp],
                'last_time': local_time,
                'full_symbols': [current_symbol_code]
            }
        elif current_block['base_symbol'] == current_base_symbol:
            current_block['scores'].append(score)
            current_block['temps'].append(temp)
            current_block['last_time'] = local_time
            current_block['full_symbols'].append(current_symbol_code)
        else:  # Symbol changed, finalize previous block and start new one
            weather_blocks.append(current_block)
            current_block = {
                'start_time': local_time,
                'base_symbol': current_base_symbol,
                'scores': [score],
                'temps': [temp],
                'last_time': local_time,
                'full_symbols': [current_symbol_code]
            }

    if current_block:  # Append the last block
        weather_blocks.append(current_block)

    if not weather_blocks:
        print(f"{Fore.YELLOW}No forecast data processed for {location_name}.{Style.RESET_ALL}")
        return

    current_display_day: str | None = None
    for block in weather_blocks:
        avg_score = sum(block['scores']) / len(block['scores'])
        valid_temps = [t for t in block['temps'] if t is not None]
        avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else None

        # Use the most frequent full symbol in the block, or the first one, for display
        # This handles cases like partlycloudy_day vs partlycloudy_night within same base block
        representative_full_symbol = max(set(block['full_symbols']), key=block['full_symbols'].count)
        weather_display = get_standardized_weather_desc(representative_full_symbol)
        # score_category = get_score_category(avg_score) # No longer needed here

        block_start_time = block['start_time']
        block_end_time_inclusive = block['last_time']
        duration_hours = (block_end_time_inclusive - block_start_time).total_seconds() / 3600 + 1

        day_name_full = block_start_time.strftime('%A, %Y-%m-%d')
        if day_name_full != current_display_day:
            if current_display_day is not None:
                print()  # Newline before new day
            print(f"{Fore.MAGENTA}{day_name_full}{Style.RESET_ALL}")
            current_display_day = day_name_full

        # Use the new formatter
        display_string = format_weather_block_for_display(
            start_time=block_start_time,
            end_time=block_end_time_inclusive,
            avg_score=avg_score,
            avg_temp=avg_temp,
            weather_description=weather_display,
            duration_hours=duration_hours
        )
        print(display_string)
        # print(f"  {Fore.CYAN}{start_str} - {end_str}{Style.RESET_ALL} {duration_str}: "
        #       f"{weather_display}, {avg_temp_display}, Score: {score_category} ({avg_score:.1f})")


def main() -> None:
    """Main function to process command-line arguments and display weather forecasts."""
    parser = argparse.ArgumentParser(description="Daily Helper: Asturias weather forecasting tool.")
    parser.add_argument(
        "--rank",
        action="store_true",
        help="Rank locations by weather suitability for outdoor activities over the next 48 hours."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,  # Default to top 10 if --rank is used
        help="Number of locations to display when ranking (default: 10)."
    )
    # Consider adding --location to focus on one or more specific locations

    args = parser.parse_args()

    if args.rank:
        all_location_data_for_ranking = []
        print(f"{Fore.BLUE}Fetching and analyzing data for ranking...{Style.RESET_ALL}")
        for loc_key, loc_info in LOCATIONS.items():
            display_name = str(loc_info['display_name'])
            print(f"{Fore.BLUE}Fetching data for {display_name}...{Style.RESET_ALL}")
            weather_data = fetch_weather_data(loc_info)
            if weather_data:
                rank_data = calculate_location_rank_data(weather_data)
                all_location_data_for_ranking.append((display_name, rank_data))
            else:
                all_location_data_for_ranking.append((display_name, {'rank_score': 0, 'good_blocks': [], 'error': 'Failed to fetch data'}))

        display_ranked_locations(all_location_data_for_ranking, top_n=args.top)
    else:
        # Default behavior: Show condensed best times for each location.
        for loc_key, loc_info in LOCATIONS.items():
            display_name = str(loc_info['display_name'])
            weather_data = fetch_weather_data(loc_info)
            # display_best_times_for_activities(weather_data, display_name) # Shows GOOD score ranges
            display_weather_forecast_by_ranges(weather_data, display_name)  # Shows all weather in ranges
            # display_hourly_forecast_24h(weather_data, display_name) # Kept for reference


if __name__ == "__main__":
    main()
