"""API client for fetching weather data from Met.no API."""

import requests
from colorama import Fore, Style
from config import API_URL, USER_AGENT


def fetch_weather_data(location, timeout=10):
    """Fetch weather data for a specific location.

    Args:
        location: Dictionary containing lat/lon coordinates and name
        timeout: Request timeout in seconds (default: 10)

    Returns:
        JSON response from API or None if request failed
    """
    # Extract location data
    lat = location["lat"]
    lon = location["lon"]
    location_name = location["name"]

    # Request headers - required by Met.no API
    headers = {"User-Agent": USER_AGENT}

    # Construct API URL
    url = f"{API_URL}?lat={lat}&lon={lon}"

    # Fetch data with error handling
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}Error: Request timed out for {location_name}{Style.RESET_ALL}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}Error: Connection failed for {location_name}{Style.RESET_ALL}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"{Fore.RED}Error: HTTP error for {location_name}: {e}{Style.RESET_ALL}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error fetching weather data for {location_name}: {e}{Style.RESET_ALL}")
        return None
    except ValueError as e:
        print(f"{Fore.RED}Error parsing JSON response for {location_name}: {e}{Style.RESET_ALL}")
        return None