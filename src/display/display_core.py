"""
Core display functions for the application.
"""

import re
from typing import List, Optional

from core.core_utils import get_value_or_default
from data.locations import LOCATIONS
from display.colors import CYAN, ERROR, GREEN, HIGHLIGHT, INFO, LIGHTGREEN, LIGHTRED, RESET, SUCCESS, WARNING, YELLOW, colorize


def _format_column(text: str, width: int) -> str:
  """Format a column with proper width accounting for ANSI color codes.

  Args:
      text: The text to format (may include ANSI color codes)
      width: The desired visual width of the column

  Returns:
      Formatted text with proper spacing
  """
  # ANSI color codes don't affect visual width, so we need to handle them specially
  # Use regex to remove all ANSI escape codes for length calculation
  visible_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
  padding = width - len(visible_text)
  if padding < 0:
    padding = 0
  return f"{text}{' ' * padding}"


def get_location_display_name(location_key: str) -> str:
  """Get the display name for a location key.

  Args:
      location_key: The location key

  Returns:
      str: The location display name
  """
  return LOCATIONS[location_key].name


def display_loading_message() -> None:
  """Display a loading message."""
  print(colorize("Fetching weather data...", WARNING))


def display_error(message: str) -> None:
  """Display an error message.

  Args:
      message: Error message to display
  """
  print(colorize(message, ERROR))


def display_info(message: str) -> None:
  """Display an informational message.

  Args:
      message: Information to display
  """
  print(colorize(message, INFO))


def display_warning(message: str) -> None:
  """Display a warning message.

  Args:
      message: Warning message to display
  """
  print(colorize(message, WARNING))


def display_temperature(temp: Optional[float]) -> str:
  """Format temperature for display.

  Args:
      temp: Temperature in Celsius

  Returns:
      str: Formatted temperature string
  """
  return get_value_or_default(f"{temp:.1f}°C" if temp is not None else None, "N/A")
