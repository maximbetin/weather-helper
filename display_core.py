"""
Core display functions for the application.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

import colors
from colors import colorize, get_rating_info
from core_utils import format_time, format_date, get_weather_desc
from locations import LOCATIONS


def list_locations() -> None:
  """List all available locations."""
  print(f"\n{colors.HIGHLIGHT}Available Locations{colors.RESET}")
  for key, loc in LOCATIONS.items():
    print(f"  {key} - {colors.EMPHASIS}{loc.name}{colors.RESET}")


def display_loading_message() -> None:
  """Display a loading message."""
  print(f"{colors.WARNING}Fetching weather data...{colors.RESET}")


def display_error(message: str) -> None:
  """Display an error message.

  Args:
      message: Error message to display
  """
  print(colorize(message, colors.ERROR))


def display_info(message: str) -> None:
  """Display an informational message.

  Args:
      message: Information to display
  """
  print(colorize(message, colors.INFO))


def display_warning(message: str) -> None:
  """Display a warning message.

  Args:
      message: Warning message to display
  """
  print(colorize(message, colors.WARNING))


def display_success(message: str) -> None:
  """Display a success message.

  Args:
      message: Success message to display
  """
  print(colorize(message, colors.SUCCESS))


def display_heading(text: str) -> None:
  """Display a section heading.

  Args:
      text: Heading text
  """
  print(f"\n{colors.HIGHLIGHT}{text}{colors.RESET}")


def display_subheading(text: str) -> None:
  """Display a section subheading.

  Args:
      text: Subheading text
  """
  print(f"{colors.EMPHASIS}{text}{colors.RESET}")


def display_temperature(temp: Optional[float]) -> str:
  """Format temperature for display.

  Args:
      temp: Temperature in Celsius

  Returns:
      str: Formatted temperature string
  """
  if temp is None:
    return "N/A"
  return f"{temp:.1f}°C"


def display_wind(wind: Optional[float]) -> str:
  """Format wind speed for display.

  Args:
      wind: Wind speed in m/s

  Returns:
      str: Formatted wind string
  """
  if wind is None:
    return "N/A"
  return f"{wind:.1f}m/s"


def display_precipitation_probability(prob: Optional[float]) -> str:
  """Format precipitation probability for display.

  Args:
      prob: Precipitation probability percentage

  Returns:
      str: Formatted probability string
  """
  if prob is None:
    return "N/A"
  return f"{prob:.0f}%"


def display_table_header(headers: List[str], widths: List[int]) -> None:
  """Display a table header.

  Args:
      headers: List of header column texts
      widths: List of column widths
  """
  header_row = ""
  separator_row = ""

  for header, width in zip(headers, widths):
    header_row += f"{header:<{width}} "
    separator_row += f"{'-' * width} "

  print(f"{colors.INFO}{header_row.rstrip()}{colors.RESET}")
  print(separator_row.rstrip())
