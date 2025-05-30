"""
Configuration constants for the Weather Helper application.
"""

from typing import Dict, Tuple

from colorama import Fore, Style, init

# API settings
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT = "WeatherHelper/1.0"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
DAYLIGHT_START_HOUR = 8
DAYLIGHT_END_HOUR = 20
FORECAST_DAYS = 7  # Max days for forecast processing

# Weather rating system - positive scores for good outdoor conditions
WEATHER_SYMBOLS: Dict[str, Tuple[str, int]] = {
    "clearsky": ("Sunny", 7),
    "fair": ("Mostly Sunny", 5),
    "partlycloudy": ("Partly Cloudy", 3),
    "cloudy": ("Cloudy", 1),
    "lightrain": ("Light Rain", -3),
    "lightrainshowers": ("Light Rain", -3),
    "lightsleet": ("Light Sleet", -4),
    "lightsleetshowers": ("Light Sleet", -4),
    "lightsnow": ("Light Snow", -4),
    "lightsnowshowers": ("Light Snow", -4),
    "rain": ("Rain", -6),
    "rainshowers": ("Rain", -6),
    "sleet": ("Sleet", -7),
    "sleetshowers": ("Sleet", -7),
    "snow": ("Snow", -7),
    "snowshowers": ("Snow", -7),
    "heavyrain": ("Heavy Rain", -10),
    "heavyrainshowers": ("Heavy Rain", -10),
    "heavysleet": ("Heavy Sleet", -10),
    "heavysleetshowers": ("Heavy Sleet", -10),
    "heavysnow": ("Heavy Snow", -10),
    "heavysnowshowers": ("Heavy Snow", -10),
    "fog": ("Foggy", -5),
    "thunderstorm": ("Thunderstorm", -15)
}


# Initialize colorama for colored terminal output
init()

# Base colors
RED = Fore.RED
LIGHTRED = Fore.LIGHTRED_EX
GREEN = Fore.GREEN
LIGHTGREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.YELLOW
BLUE = Fore.BLUE
CYAN = Fore.CYAN
MAGENTA = Fore.MAGENTA
LIGHTMAGENTA = Fore.LIGHTMAGENTA_EX
RESET = Style.RESET_ALL

# Semantic colors
SUCCESS = LIGHTGREEN
ERROR = LIGHTRED
WARNING = YELLOW
INFO = CYAN
HIGHLIGHT = MAGENTA
EMPHASIS = LIGHTMAGENTA

# Rating colors based on score
RATING_COLORS: Dict[str, str] = {
    "Excellent": LIGHTGREEN,
    "Very Good": GREEN,
    "Good": CYAN,
    "Fair": YELLOW,
    "Poor": LIGHTRED,
    "N/A": RESET
}
