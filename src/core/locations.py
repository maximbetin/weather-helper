"""
Defines the Location class and the dictionary of known locations.
"""

from typing import Dict, NamedTuple

from src.core.config import TIMEZONE

SPAIN_MAINLAND_TZ = "Europe/Madrid"
CANARY_ISLANDS_TZ = "Atlantic/Canary"


class Location(NamedTuple):
    """Represents a geographical location with coordinates.

    Attributes:
        key: Unique identifier for the location
        name: Human-readable name of the location
        lat: Latitude coordinate
        lon: Longitude coordinate
        timezone: IANA time zone name used to interpret this location's forecast
    """

    key: str
    name: str
    lat: float
    lon: float
    timezone: str = TIMEZONE


# Northern Spain / Asturias
ASTURIAS_LOCATIONS: Dict[str, Location] = {
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6610, SPAIN_MAINLAND_TZ),
    "oviedo": Location("oviedo", "Oviedo", 43.3623, -5.8485, SPAIN_MAINLAND_TZ),
    "llanes": Location("llanes", "Llanes", 43.4211, -4.7562, SPAIN_MAINLAND_TZ),
    "aviles": Location("aviles", "Avilés", 43.5567, -5.9256, SPAIN_MAINLAND_TZ),
    "luarca": Location("luarca", "Luarca", 43.5420, -6.5359, SPAIN_MAINLAND_TZ),
    "luanco": Location("luanco", "Luanco", 43.6137, -5.7929, SPAIN_MAINLAND_TZ),
    "salinas": Location("salinas", "Salinas", 43.5753, -5.9585, SPAIN_MAINLAND_TZ),
    "cudillero": Location("cudillero", "Cudillero", 43.5629, -6.1453, SPAIN_MAINLAND_TZ),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4631, -5.0567, SPAIN_MAINLAND_TZ),
    "cangas_de_onis": Location("cangas_de_onis", "Cangas de Onís", 43.3514, -5.1292, SPAIN_MAINLAND_TZ),
    "villaviciosa": Location("villaviciosa", "Villaviciosa", 43.4814, -5.4356, SPAIN_MAINLAND_TZ),
    "lastres": Location("lastres", "Lastres", 43.5135, -5.2696, SPAIN_MAINLAND_TZ),
}

# Rest of Spain
SPAIN_OTHER_LOCATIONS: Dict[str, Location] = {
    "alicante": Location("alicante", "Alicante", 38.3452, -0.4830, SPAIN_MAINLAND_TZ),
    "madrid": Location("madrid", "Madrid", 40.4165, -3.7026, SPAIN_MAINLAND_TZ),
    "barcelona": Location("barcelona", "Barcelona", 41.3888, 2.1590, SPAIN_MAINLAND_TZ),
    "valencia": Location("valencia", "València", 39.4699, -0.3763, SPAIN_MAINLAND_TZ),
    "sevilla": Location("sevilla", "Sevilla", 37.3891, -5.9845, SPAIN_MAINLAND_TZ),
    "granada": Location("granada", "Granada", 37.1882, -3.6067, SPAIN_MAINLAND_TZ),
    "malaga": Location("malaga", "Málaga", 36.7213, -4.4214, SPAIN_MAINLAND_TZ),
    "cordoba": Location("cordoba", "Córdoba", 37.8882, -4.7794, SPAIN_MAINLAND_TZ),
    "zaragoza": Location("zaragoza", "Zaragoza", 41.6488, -0.8891, SPAIN_MAINLAND_TZ),
    "murcia": Location("murcia", "Murcia", 37.9922, -1.1307, SPAIN_MAINLAND_TZ),
    "valladolid": Location("valladolid", "Valladolid", 41.6523, -4.7245, SPAIN_MAINLAND_TZ),
    "bilbao": Location("bilbao", "Bilbao", 43.2630, -2.9350, SPAIN_MAINLAND_TZ),
    "palma": Location("palma", "Palma", 39.5696, 2.6502, SPAIN_MAINLAND_TZ),
    "tenerife": Location("tenerife", "Tenerife (Santa Cruz)", 28.4636, -16.2518, CANARY_ISLANDS_TZ),
    "las_palmas": Location("las_palmas", "Las Palmas de Gran Canaria", 28.1235, -15.4363, CANARY_ISLANDS_TZ),
    "almeria": Location("almeria", "Almería", 36.8300, -2.4300, SPAIN_MAINLAND_TZ),
    "salobrena": Location("salobrena", "Salobreña", 36.7432, -3.5866, SPAIN_MAINLAND_TZ),
    "almunecar": Location("almunecar", "Almuñécar", 36.7339, -3.6907, SPAIN_MAINLAND_TZ),
    "motril": Location("motril", "Motril", 36.7460, -3.5204, SPAIN_MAINLAND_TZ),
}

# Worldwide
WORLDWIDE_OTHER_LOCATIONS: Dict[str, Location] = {
    "london": Location("london", "London", 51.5074, -0.1278, "Europe/London"),
    "paris": Location("paris", "Paris", 48.8566, 2.3522, "Europe/Paris"),
    "new_york": Location("new_york", "New York", 40.7128, -74.0060, "America/New_York"),
    "tokyo": Location("tokyo", "Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    "berlin": Location("berlin", "Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    "rome": Location("rome", "Rome", 41.9028, 12.4964, "Europe/Rome"),
    "amsterdam": Location("amsterdam", "Amsterdam", 52.3676, 4.9041, "Europe/Amsterdam"),
    "prague": Location("prague", "Prague", 50.0880, 14.4208, "Europe/Prague"),
    "lisbon": Location("lisbon", "Lisbon", 38.7223, -9.1393, "Europe/Lisbon"),
    "houston": Location("houston", "Houston", 29.7604, -95.3698, "America/Chicago"),
    "rio_de_janeiro": Location("rio_de_janeiro", "Rio de Janeiro", -22.9068, -43.1729, "America/Sao_Paulo"),
    "buenos_aires": Location("buenos_aires", "Buenos Aires", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
}

# Combined lists
SPAIN_LOCATIONS = SPAIN_OTHER_LOCATIONS.copy()

# Worldwide should only include Madrid from Spain + other international locations
WORLDWIDE_LOCATIONS = WORLDWIDE_OTHER_LOCATIONS.copy()
if "madrid" in SPAIN_OTHER_LOCATIONS:
    WORLDWIDE_LOCATIONS["madrid"] = SPAIN_OTHER_LOCATIONS["madrid"]

# Map names to dictionaries for easy access
LOCATION_GROUPS = {
    "Asturias": ASTURIAS_LOCATIONS,
    "Spain": SPAIN_LOCATIONS,
    "Worldwide": WORLDWIDE_LOCATIONS,
}

# Default set
LOCATIONS = ASTURIAS_LOCATIONS
