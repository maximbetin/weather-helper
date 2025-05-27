"""
Handles API calls to fetch weather data from Met.no.
"""

import logging
from typing import Any, Dict, Optional

import requests

from core.config import API_URL, USER_AGENT
from data.locations import Location
from display.colors import ERROR, colorize

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weather_api')


def fetch_weather_data(location: Location) -> Optional[Dict[str, Any]]:
  """Fetch weather data for a specific location.

  Args:
      location: Location object containing lat/lon coordinates

  Returns:
      JSON response from API or None if request failed
  """
  lat = location.lat
  lon = location.lon

  # Request headers - required by Met.no API
  headers = {
      "User-Agent": USER_AGENT
  }

  # Construct API URL
  url = f"{API_URL}?lat={lat}&lon={lon}"

  # Fetch data with error handling
  try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()
  except requests.exceptions.Timeout:
    error_msg = f"Timeout error fetching weather data for {location.name}"
    logger.error(error_msg)
    print(colorize(f"Error: {error_msg}", ERROR))
    return None
  except requests.exceptions.RequestException as e:
    logger.error(f"Error fetching weather data for {location.name}: {e}")
    print(colorize(f"Error fetching weather data for {location.name}: {e}", ERROR))
    return None
  except ValueError as e:  # Handle cases where response is not valid JSON
    logger.error(f"Error parsing JSON response for {location.name}: {e}")
    print(colorize(f"Error parsing JSON response for {location.name}: {e}", ERROR))
    return None
