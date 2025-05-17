"""Configuration constants for the Daily Helper application."""

# Define locations in Asturias
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

# Weather rating system - positive scores for good outdoor conditions
WEATHER_SCORES = {
    # Sunny/clear conditions (highest scores)
    "clearsky": 10,
    "fair": 8,

    # Partly cloudy conditions (medium scores)
    "partlycloudy": 6,

    # Cloudy but no precipitation (lower scores)
    "cloudy": 3,

    # Light precipitation (negative scores)
    "lightrain": -2,
    "lightrainshowers": -2,
    "lightsleet": -3,
    "lightsleetshowers": -3,
    "lightsnow": -3,
    "lightsnowshowers": -3,

    # Moderate precipitation (more negative)
    "rain": -5,
    "rainshowers": -5,
    "sleet": -6,
    "sleetshowers": -6,
    "snow": -6,
    "snowshowers": -6,

    # Heavy precipitation (most negative)
    "heavyrain": -10,
    "heavyrainshowers": -10,
    "heavysleet": -10,
    "heavysleetshowers": -10,
    "heavysnow": -10,
    "heavysnowshowers": -10,

    # Fog/poor visibility
    "fog": -4,

    # Thunderstorms (most negative)
    "thunderstorm": -15
}

# API settings
API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
USER_AGENT = "DailyHelper/1.0"

# Time zone
TIMEZONE = "Europe/Madrid"

# Weather display settings
DAYLIGHT_START_HOUR = 8
DAYLIGHT_END_HOUR = 20
FORECAST_DAYS = 7