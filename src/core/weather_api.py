"""
Handles API calls to fetch weather data from Met.no.
"""

import logging
from typing import Any, Dict, Optional

import requests

from src.core.config import API_URL, API_URL_COMPACT, OCEAN_API_URL, USER_AGENT
from src.core.locations import Location

REQUEST_TIMEOUT_SECONDS = 10
MIN_COMPLETE_TIMESERIES_LENGTH = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("weather_api")


def _make_request(
    url: str, location: Location, headers: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """Make a request to the weather API and return the JSON response."""
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"Error fetching forecast from {url} for {location.name}: {e}")
        return None


def _build_forecast_url(base_url: str, location: Location) -> str:
    """Build a met.no forecast URL for a location."""
    return f"{base_url}?lat={location.lat}&lon={location.lon}"


def _get_timeseries(data: Optional[Dict[str, Any]]) -> list:
    """Extract timeseries rows from a forecast response."""
    if not data:
        return []
    properties = data.get("properties") or {}
    return properties.get("timeseries") or []


def _has_complete_forecast(data: Optional[Dict[str, Any]]) -> bool:
    """Return True when the complete endpoint has enough forecast rows."""
    return len(_get_timeseries(data)) >= MIN_COMPLETE_TIMESERIES_LENGTH


def fetch_ocean_data(location: Location) -> Optional[Dict[str, Any]]:
    """Fetch ocean data from the API."""
    headers = {"User-Agent": USER_AGENT}
    ocean_url = _build_forecast_url(OCEAN_API_URL, location)
    return _make_request(ocean_url, location, headers)


def fetch_weather_data(location: Location) -> Optional[Dict[str, Any]]:
    """Fetch weather data, falling back to compact when complete is too sparse.
    Also attempts to fetch ocean data and returns a combined dictionary.

    Args:
        location: Location object containing lat/lon coordinates

    Returns:
        JSON response with 'weather' and 'ocean' keys, or None if weather request failed
    """
    headers = {"User-Agent": USER_AGENT}
    complete_url = _build_forecast_url(API_URL, location)
    data = _make_request(complete_url, location, headers)
    
    if not _has_complete_forecast(data):
        compact_url = _build_forecast_url(API_URL_COMPACT, location)
        data = _make_request(compact_url, location, headers)
        
    if data is None:
        return None
        
    ocean_data = fetch_ocean_data(location)
    
    return {
        "weather": data,
        "ocean": ocean_data
    }
