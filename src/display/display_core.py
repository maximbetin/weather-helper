"""
Core display functions for the application.
"""

from typing import List, Optional

from core.core_utils import get_value_or_default
from data.locations import LOCATIONS
from display.colors import colorize

from . import colors


def _format_column(text: str, width: int) -> str:
  """Format a column with proper width accounting for ANSI color codes.

  Args:
      text: The text to format (may include ANSI color codes)
      width: The desired visual width of the column

  Returns:
      Formatted text with proper spacing
  """
  # ANSI color codes don't affect visual width, so we need to handle them specially
  if '\033[' in text:
    # Find the visible text (exclude ANSI codes)
    visible_text = text.replace(colors.RESET, '').replace(colors.LIGHTGREEN, '').replace(colors.GREEN, '')
    visible_text = visible_text.replace(colors.CYAN, '').replace(colors.YELLOW, '').replace(colors.LIGHTRED, '')
    visible_text = visible_text.replace(colors.INFO, '')

    # Calculate padding based on visible text length
    padding = width - len(visible_text)
    if padding < 0:
      padding = 0

    return f"{text}{' ' * padding}"
  else:
    # Regular text without color codes
    return f"{text:<{width}}"


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
  print(colorize("Fetching weather data...", colors.WARNING))


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
  print(f"\n{colorize(text, colors.HIGHLIGHT)}")


def display_subheading(text: str) -> None:
  """Display a section subheading.

  Args:
      text: Subheading text
  """
  print(colorize(text, colors.EMPHASIS))


def display_temperature(temp: Optional[float]) -> str:
  """Format temperature for display.

  Args:
      temp: Temperature in Celsius

  Returns:
      str: Formatted temperature string
  """
  return get_value_or_default(f"{temp:.1f}°C" if temp is not None else None, "N/A")


def display_wind(wind: Optional[float]) -> str:
  """Format wind speed for display.

  Args:
      wind: Wind speed in m/s

  Returns:
      str: Formatted wind string
  """
  return get_value_or_default(f"{wind:.1f}m/s" if wind is not None else None, "N/A")


def display_precipitation_probability(prob: Optional[float]) -> str:
  """Format precipitation probability for display.

  Args:
      prob: Precipitation probability percentage

  Returns:
      str: Formatted probability string
  """
  return get_value_or_default(f"{prob:.0f}%" if prob is not None else None, "N/A")


def display_table_header(headers: List[str], widths: List[int]) -> None:
  """Display a table header.

  Args:
      headers: List of header column texts
      widths: List of column widths
  """
  header_row = ""
  separator_row = ""

  for header, width in zip(headers, widths):
    header_col = _format_column(colorize(header, colors.INFO), width)
    header_row += header_col + " "
    separator_row += "-" * width + " "

  print(header_row)
  print(separator_row.rstrip())
