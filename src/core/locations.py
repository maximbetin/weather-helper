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


# Define locations (only Spanish locations have been tested so far)
LOCATIONS: Dict[str, Location] = {
    # Northern Spain / Asturias (original set)
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6610),
    "oviedo": Location("oviedo", "Oviedo", 43.3623, -5.8485),
    "llanes": Location("llanes", "Llanes", 43.4211, -4.7562),
    "aviles": Location("aviles", "Avilés", 43.5567, -5.9256),
    "luarca": Location("luarca", "Luarca", 43.5420, -6.5359),
    "luanco": Location("luanco", "Luanco", 43.6137, -5.7929),
    "salinas": Location("salinas", "Salinas", 43.5753, -5.9585),
    "cudillero": Location("cudillero", "Cudillero", 43.5629, -6.1453),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4631, -5.0567),
    # Existing Mediterranean coast
    "alicante": Location("alicante", "Alicante", 38.3452, -0.4830),
    # Major Spanish cities (peninsula)
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
    # Islands and southern coast
    "palma": Location("palma", "Palma", 39.5696, 2.6502),
    "tenerife": Location(
        "tenerife",
        "Tenerife (Santa Cruz)",
        28.4636,
        -16.2518,
    ),
    "las_palmas": Location(
        "las_palmas",
        "Las Palmas de Gran Canaria",
        28.1235,
        -15.4363,
    ),
    "almeria": Location("almeria", "Almería", 36.8300, -2.4300),
}
