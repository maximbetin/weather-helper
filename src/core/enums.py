"""
Enumerations used throughout the weather helper application.
"""

from enum import Enum


class WeatherBlockType(Enum):
  """Enumeration of weather block types for categorization.

  Attributes:
      SUNNY: Clear or fair weather conditions
      RAINY: Rainy weather conditions
      CLOUDY: Cloudy weather conditions
  """
  SUNNY = "sunny"
  RAINY = "rainy"
  CLOUDY = "cloudy"
