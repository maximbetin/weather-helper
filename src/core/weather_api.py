"""
Handles API calls to fetch weather data from Met.no.
"""

import logging
from typing import Any, Dict, Optional

import requests

from src.core.config import API_URL, API_URL_COMPACT, USER_AGENT
from src.core.locations import Location

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('weather_api')


def _make_request(url: str, location: Location, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
  """Make a request to the weather API and return the JSON response."""
  try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
  except (requests.exceptions.RequestException, ValueError) as e:
    logger.error(f"Error fetching forecast from {url} for {location.name}: {e}")
    return None


def fetch_weather_data(location: Location) -> Optional[Dict[str, Any]]:
  """Fetch weather data for a specific location, falling back to compact endpoint if complete returns insufficient data.

  Args:
      location: Location object containing lat/lon coordinates

  Returns:
      JSON response from API or None if request failed
  """
  lat = location.lat
  lon = location.lon

  headers = {
      "User-Agent": USER_AGENT
  }

  # First try the complete endpoint
  complete_url = f"{API_URL}?lat={lat}&lon={lon}"
  data = _make_request(complete_url, location, headers)
  if data and data.get("properties", {}).get("timeseries", []) and len(data["properties"]["timeseries"]) >= 5:
    return data

  # Fallback to compact endpoint
  compact_url = f"{API_URL_COMPACT}?lat={lat}&lon={lon}"
  return _make_request(compact_url, location, headers)
