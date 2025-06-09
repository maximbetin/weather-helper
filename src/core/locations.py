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
    "gijon": Location("gijon", "Gijón", 43.5322, -5.6610),
    "oviedo": Location("oviedo", "Oviedo", 43.3623, -5.8485),
    "llanes": Location("llanes", "Llanes", 43.4211, -4.7562),
    "aviles": Location("aviles", "Avilés", 43.5567, -5.9256),
    "luarca": Location("luarca", "Luarca", 43.5420, -6.5359),
    "luanco": Location("luanco", "Luanco", 43.6137, -5.7929),
    "salinas": Location("salinas", "Salinas", 43.5753, -5.9585),
    "alicante": Location("alicante", "Alicante", 38.34517, -0.48149),
    "cudillero": Location("cudillero", "Cudillero", 43.5629, -6.1453),
    "ribadesella": Location("ribadesella", "Ribadesella", 43.4631, -5.0567),
    "lagos_covadonga": Location("lagos_covadonga", "Lagos de Covadonga", 43.1600, -4.5900),
}
