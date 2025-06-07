"""
Handles API calls to fetch weather data from Met.no.
"""

import logging
from typing import Any, Dict, Optional

import requests

from src.core.config import API_URL, USER_AGENT
from src.core.locations import Location

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
  return fetch_weather_data_with_fallback(location)


def fetch_weather_data_with_fallback(location: Location) -> Optional[Dict[str, Any]]:
  """Fetch weather data for a specific location, falling back to compact endpoint if complete returns insufficient data.

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

  # First try the complete endpoint
  url = f"{API_URL}?lat={lat}&lon={lon}"
  try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    # Check if the timeseries has at least 5 entries
    if data.get("properties", {}).get("timeseries", []) and len(data["properties"]["timeseries"]) >= 5:
      return data
  except (requests.exceptions.RequestException, ValueError) as e:
    logger.error(f"Error fetching complete forecast for {location.name}: {e}")

  # Fallback to compact endpoint
  compact_url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"
  try:
    response = requests.get(compact_url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
  except (requests.exceptions.RequestException, ValueError) as e:
    logger.error(f"Error fetching compact forecast for {location.name}: {e}")
    return None
