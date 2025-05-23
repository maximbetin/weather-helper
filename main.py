"""
Daily Helper: Weather forecasting tool that helps find the best times and locations
for outdoor activities in Asturias, Spain.
"""
from datetime import datetime
from typing import Any

import pytz
import requests
from colorama import Fore, Style, init

LOCATIONS: dict[str, dict[str, str | float]] = {
    "oviedo": {"display_name": "Oviedo", "lat": 43.3619, "lon": -5.8494},
    # "llanes": {"display_name": "Llanes", "lat": 43.4200, "lon": -4.7550},
    # "aviles": {"display_name": "Avilés", "lat": 43.5547, "lon": -5.9248},
    # "somiedo": {"display_name": "Somiedo", "lat": 43.0981, "lon": -6.2550},
    # "teverga": {"display_name": "Teverga", "lat": 43.1578, "lon": -6.0867},
    # "taramundi": {"display_name": "Taramundi", "lat": 43.3583, "lon": -7.1083},
    # "ribadesella": {"display_name": "Ribadesella", "lat": 43.4675, "lon": -5.0553},
    # "tapia": {"display_name": "Tapia de Casariego", "lat": 43.5700, "lon": -6.9436},
    # "cangas_de_onis": {"display_name": "Cangas de Onís", "lat": 43.3507, "lon": -5.1356},
    # "lagos_covadonga": {"display_name": "Lagos de Covadonga", "lat": 43.2728, "lon": -4.9906},
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


def get_score_category(score: int) -> str:
    """Convert numerical score to a human-readable category."""
    if score >= 12:
        return f"{Fore.GREEN}[Excellent]{Style.RESET_ALL}"
    elif score >= 8:
        return f"{Fore.GREEN}[Very Good]{Style.RESET_ALL}"
    elif score >= 5:
        return f"{Fore.GREEN}[Good]{Style.RESET_ALL}"
    elif score >= 2:
        return f"{Fore.YELLOW}[Fair]{Style.RESET_ALL}"
    elif score >= 0:
        return f"{Fore.YELLOW}[Okay]{Style.RESET_ALL}"
    elif score >= -3:
        return f"{Fore.RED}[Poor]{Style.RESET_ALL}"
    elif score >= -7:
        return f"{Fore.RED}[Bad]{Style.RESET_ALL}"
    else:
        return f"{Fore.RED}[Very Bad]{Style.RESET_ALL}"


def get_standardized_weather_desc(symbol: str | None) -> str:
    """Return standardized weather description from symbol code."""
    if not symbol or not isinstance(symbol, str):
        return "Unknown"

    # Check for direct matches in the global SYMBOL_MAP
    if symbol in SYMBOL_MAP:
        return SYMBOL_MAP[symbol]
    else:
        # Fallback: Capitalize and replace underscores for any other unmapped symbols
        return symbol.replace("_", " ").capitalize()


def display_best_times_for_activities(weather_data: dict[str, Any] | None, location_name: str) -> None:
    """Displays the best times for outdoor activities based on a weather score threshold."""
    if not weather_data or 'properties' not in weather_data or 'timeseries' not in weather_data['properties']:
        print(f"{Fore.YELLOW}No timeseries data to analyze for {location_name}.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Best Times for Outdoor Activities in {location_name} (Score >= 5):{Style.RESET_ALL}")

    timeseries = weather_data['properties']['timeseries']
    madrid_tz = pytz.timezone(TIMEZONE)
    current_display_day: str | None = None
    found_good_time = False

    for _, entry in enumerate(timeseries):
        time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = time_utc.astimezone(madrid_tz)

        instant_details = entry['data'].get('instant', {}).get('details', {})
        next_1h_summary = entry['data'].get('next_1_hours', {}).get('summary', {})
        next_1h_details = entry['data'].get('next_1_hours', {}).get('details', {})
        symbol_code_1h = next_1h_summary.get('symbol_code')

        if not symbol_code_1h:
            continue

        temp = instant_details.get('air_temperature')
        wind_speed_instant = instant_details.get('wind_speed')
        precip_amount_1h = next_1h_details.get('precipitation_amount')

        score = get_weather_score(symbol_code_1h, temp, wind_speed_instant, precip_amount_1h)

        if score >= 5:
            found_good_time = True
            base_symbol = symbol_code_1h.split('_')[0]
            weather_display = f"{get_standardized_weather_desc(base_symbol)}"
            score_category = get_score_category(score)

            day_name_full = local_time.strftime('%A, %Y-%m-%d')
            if day_name_full != current_display_day:
                print(f"\n{Fore.MAGENTA}{day_name_full}{Style.RESET_ALL}")
                current_display_day = day_name_full

            temp_display = f"{temp}°C" if temp is not None else "N/A"
            print(f"{Fore.CYAN}{local_time.strftime('%H:%M')}{Style.RESET_ALL}: "
                  f"{score_category} ({temp_display}, {weather_display})")

    if not found_good_time:
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


def main() -> None:
    """Main function to process command-line arguments and display weather forecasts."""

    for location_name, location_info in LOCATIONS.items():
        location_name = str(location_info['display_name'])
        weather_data = fetch_weather_data(location_info)
        # display_timeseries_data(weather_data, location_name)  # Keep or remove as needed
        display_best_times_for_activities(weather_data, location_name)


if __name__ == "__main__":
    main()
