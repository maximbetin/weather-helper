"""
Defines the Location class and the dictionary of known locations.
"""

from typing import Dict, NamedTuple


class Location(NamedTuple):
    """Represents a geographical location with coordinates.

    Attributes:
        key: Unique identifier for the location
        name: Human-readable name of the location
        lat: Latitude coordinate
        lon: Longitude coordinate
    """

    key: str
    name: str
    lat: float
    lon: float


# Northern Spain / Asturias
ASTURIAS_LOCATIONS: Dict[str, Location] = {
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6610),
    "oviedo": Location("oviedo", "Oviedo", 43.3623, -5.8485),
    "llanes": Location("llanes", "Llanes", 43.4211, -4.7562),
    "aviles": Location("aviles", "Avilés", 43.5567, -5.9256),
    "luarca": Location("luarca", "Luarca", 43.5420, -6.5359),
    "luanco": Location("luanco", "Luanco", 43.6137, -5.7929),
    "salinas": Location("salinas", "Salinas", 43.5753, -5.9585),
    "cudillero": Location("cudillero", "Cudillero", 43.5629, -6.1453),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4631, -5.0567),
    "cangas_de_onis": Location("cangas_de_onis", "Cangas de Onís", 43.3514, -5.1292),
    "villaviciosa": Location("villaviciosa", "Villaviciosa", 43.4814, -5.4356),
    "lastres": Location("lastres", "Lastres", 43.5135, -5.2696),
}

# Rest of Spain
SPAIN_OTHER_LOCATIONS: Dict[str, Location] = {
    "alicante": Location("alicante", "Alicante", 38.3452, -0.4830),
    "madrid": Location("madrid", "Madrid", 40.4165, -3.7026),
    "barcelona": Location("barcelona", "Barcelona", 41.3888, 2.1590),
    "valencia": Location("valencia", "València", 39.4699, -0.3763),
    "sevilla": Location("sevilla", "Sevilla", 37.3891, -5.9845),
    "granada": Location("granada", "Granada", 37.1882, -3.6067),
    "malaga": Location("malaga", "Málaga", 36.7213, -4.4214),
    "cordoba": Location("cordoba", "Córdoba", 37.8882, -4.7794),
    "zaragoza": Location("zaragoza", "Zaragoza", 41.6488, -0.8891),
    "murcia": Location("murcia", "Murcia", 37.9922, -1.1307),
    "valladolid": Location("valladolid", "Valladolid", 41.6523, -4.7245),
    "bilbao": Location("bilbao", "Bilbao", 43.2630, -2.9350),
    "palma": Location("palma", "Palma", 39.5696, 2.6502),
    "tenerife": Location("tenerife", "Tenerife (Santa Cruz)", 28.4636, -16.2518),
    "las_palmas": Location("las_palmas", "Las Palmas de Gran Canaria", 28.1235, -15.4363),
    "almeria": Location("almeria", "Almería", 36.8300, -2.4300),
    "salobrena": Location("salobrena", "Salobreña", 36.7432, -3.5866),
    "almunecar": Location("almunecar", "Almuñécar", 36.7339, -3.6907),
    "motril": Location("motril", "Motril", 36.7460, -3.5204),
}

# Worldwide
WORLDWIDE_OTHER_LOCATIONS: Dict[str, Location] = {
    "london": Location("london", "London", 51.5074, -0.1278),
    "paris": Location("paris", "Paris", 48.8566, 2.3522),
    "new_york": Location("new_york", "New York", 40.7128, -74.0060),
    "tokyo": Location("tokyo", "Tokyo", 35.6762, 139.6503),
    "berlin": Location("berlin", "Berlin", 52.5200, 13.4050),
    "rome": Location("rome", "Rome", 41.9028, 12.4964),
    "amsterdam": Location("amsterdam", "Amsterdam", 52.3676, 4.9041),
    "prague": Location("prague", "Prague", 50.0880, 14.4208),
    "lisbon": Location("lisbon", "Lisbon", 38.7223, -9.1393),
    "houston": Location("houston", "Houston", 29.7604, -95.3698),
    "rio_de_janeiro": Location("rio_de_janeiro", "Rio de Janeiro", -22.9068, -43.1729),
    "buenos_aires": Location("buenos_aires", "Buenos Aires", -34.6037, -58.3816),
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
