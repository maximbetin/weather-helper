"""Configuration constants for the Daily Helper application."""

# --------------------------
# LOCATION SETTINGS
# --------------------------
LOCATIONS = {
    "gijon": {"name": "Gijón", "lat": 43.5322, "lon": -5.6611},
    "llanes": {"name": "Llanes", "lat": 43.4200, "lon": -4.7550},
    "ribadesella": {"name": "Ribadesella", "lat": 43.4675, "lon": -5.0553},
    "tapia": {"name": "Tapia de Casariego", "lat": 43.5700, "lon": -6.9436},
    "aviles": {"name": "Avilés", "lat": 43.5547, "lon": -5.9248},
    "cangas_de_onis": {"name": "Cangas de Onís", "lat": 43.3507, "lon": -5.1356},
    "lagos_covadonga": {"name": "Lagos de Covadonga", "lat": 43.2728, "lon": -4.9906},
    "somiedo": {"name": "Somiedo", "lat": 43.0981, "lon": -6.2550},
    "teverga": {"name": "Teverga", "lat": 43.1578, "lon": -6.0867},
    "taramundi": {"name": "Taramundi", "lat": 43.3583, "lon": -7.1083},
    "oviedo": {"name": "Oviedo", "lat": 43.3619, "lon": -5.8494}
}

# --------------------------
# TIME SETTINGS
# --------------------------
TIMEZONE = "Europe/Madrid"
DAYLIGHT_START_HOUR = 8  # When to start considering daylight hours
DAYLIGHT_END_HOUR = 20   # When to stop considering daylight hours
FORECAST_DAYS = 7        # Number of days to forecast

# --------------------------
# API SETTINGS
# --------------------------
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT = "DailyHelper/1.0"

# --------------------------
# WEATHER SCORING SYSTEM
# --------------------------
# Positive scores indicate good conditions for outdoor activities
# Negative scores indicate poor conditions
WEATHER_SCORES = {
    # Clear conditions (highest scores)
    "clearsky": 10,      # Clear sky, no clouds
    "fair": 8,           # Fair weather, minimal clouds

    # Partly cloudy conditions (medium scores)
    "partlycloudy": 6,   # Partly cloudy

    # Cloudy but no precipitation (lower scores)
    "cloudy": 3,         # Mostly cloudy

    # Light precipitation (negative scores)
    "lightrain": -2,     # Light rain
    "lightrainshowers": -2,  # Light rain showers
    "lightsleet": -3,    # Light sleet
    "lightsleetshowers": -3, # Light sleet showers
    "lightsnow": -3,     # Light snow
    "lightsnowshowers": -3,  # Light snow showers

    # Moderate precipitation (more negative)
    "rain": -5,          # Moderate rain
    "rainshowers": -5,   # Moderate rain showers
    "sleet": -6,         # Moderate sleet
    "sleetshowers": -6,  # Moderate sleet showers
    "snow": -6,          # Moderate snow
    "snowshowers": -6,   # Moderate snow showers

    # Heavy precipitation (most negative)
    "heavyrain": -10,    # Heavy rain
    "heavyrainshowers": -10, # Heavy rain showers
    "heavysleet": -10,   # Heavy sleet
    "heavysleetshowers": -10, # Heavy sleet showers
    "heavysnow": -10,    # Heavy snow
    "heavysnowshowers": -10, # Heavy snow showers

    # Poor visibility
    "fog": -4,           # Foggy conditions

    # Severe weather (most negative)
    "thunderstorm": -15  # Thunderstorms
}