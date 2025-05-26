"""
Handles API calls to fetch weather data from Met.no.
"""

import requests

from config import API_URL, USER_AGENT, COLOR_RED, COLOR_RESET


def fetch_weather_data(location):
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
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()
  except requests.exceptions.RequestException as e:
    print(f"{COLOR_RED}Error fetching weather data for {location.name}: {e}{COLOR_RESET}")
    return None
  except ValueError as e:  # Handle cases where response is not valid JSON
    print(f"{COLOR_RED}Error parsing JSON response for {location.name}: {e}{COLOR_RESET}")
    return None
