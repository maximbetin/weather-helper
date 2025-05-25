"""
Configuration constants for the Daily Helper application.
"""

import pytz
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init()

# API settings
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT = "DailyHelper/1.0"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
DAYLIGHT_START_HOUR = 8
DAYLIGHT_END_HOUR = 20
FORECAST_DAYS = 7  # Max days for forecast processing

# Weather rating system - positive scores for good outdoor conditions
WEATHER_SYMBOLS = {
    "clearsky": ("Sunny", 10),
    "fair": ("Mostly Sunny", 8),
    "partlycloudy": ("Partly Cloudy", 6),
    "cloudy": ("Cloudy", 3),
    "lightrain": ("Light Rain", -2),
    "lightrainshowers": ("Light Rain", -2),
    "lightsleet": ("Light Sleet", -3),
    "lightsleetshowers": ("Light Sleet", -3),
    "lightsnow": ("Light Snow", -3),
    "lightsnowshowers": ("Light Snow", -3),
    "rain": ("Rain", -5),
    "rainshowers": ("Rain", -5),
    "sleet": ("Sleet", -6),
    "sleetshowers": ("Sleet", -6),
    "snow": ("Snow", -6),
    "snowshowers": ("Snow", -6),
    "heavyrain": ("Heavy Rain", -10),
    "heavyrainshowers": ("Heavy Rain", -10),
    "heavysleet": ("Heavy Sleet", -10),
    "heavysleetshowers": ("Heavy Sleet", -10),
    "heavysnow": ("Heavy Snow", -10),
    "heavysnowshowers": ("Heavy Snow", -10),
    "fog": ("Foggy", -4),
    "thunderstorm": ("Thunderstorm", -15)
}

# Weather description mapping (used by get_standardized_weather_desc)
WEATHER_DESC_MAP = {
    "cloudy": "Cloudy",
    "clearsky": "Sunny",
    "fair": "Mostly Sunny",
    "partlycloudy": "Partly Cloudy",
}

# Colorama Styles (optional, can be used in display_utils)
COLOR_EXCELLENT = Fore.LIGHTGREEN_EX
COLOR_VERY_GOOD = Fore.GREEN
COLOR_GOOD = Fore.CYAN
COLOR_FAIR = Fore.YELLOW
COLOR_POOR = Fore.LIGHTRED_EX
COLOR_BAD = Fore.RED
COLOR_MAGENTA = Fore.MAGENTA
COLOR_RESET = Style.RESET_ALL
COLOR_LIGHTMAGENTA_EX = Fore.LIGHTMAGENTA_EX

# Add missing direct color usages if any
COLOR_CYAN = Fore.CYAN  # For Good rating, and table headers
COLOR_YELLOW = Fore.YELLOW  # For Fair rating, and warnings
COLOR_RED = Fore.RED  # For Bad rating, and errors/avoid
COLOR_GREEN = Fore.GREEN  # For Very Good rating
COLOR_LIGHTRED_EX = Fore.LIGHTRED_EX  # For Poor rating
COLOR_LIGHTGREEN_EX = Fore.LIGHTGREEN_EX  # For Excellent rating
