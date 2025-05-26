"""
Unified color system for the application.
Provides color constants and utility functions for colorized output.
"""

from colorama import Fore, Style, init
from typing import Tuple, Union, Dict

# Initialize colorama for colored terminal output
init()

# Base colors
RED = Fore.RED
LIGHTRED = Fore.LIGHTRED_EX
GREEN = Fore.GREEN
LIGHTGREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.YELLOW
BLUE = Fore.BLUE
CYAN = Fore.CYAN
MAGENTA = Fore.MAGENTA
LIGHTMAGENTA = Fore.LIGHTMAGENTA_EX
RESET = Style.RESET_ALL

# Semantic colors
SUCCESS = LIGHTGREEN
ERROR = LIGHTRED
WARNING = YELLOW
INFO = CYAN
HIGHLIGHT = MAGENTA
EMPHASIS = LIGHTMAGENTA

# Rating colors based on score
RATING_COLORS: Dict[str, str] = {
    "Excellent": LIGHTGREEN,
    "Very Good": GREEN,
    "Good": CYAN,
    "Fair": YELLOW,
    "Poor": LIGHTRED,
    "Bad": RED,
    "N/A": RESET
}


def get_rating_info(score: Union[int, float, None]) -> Tuple[str, str]:
  """Return standardized rating description and color based on score.

  Args:
      score: Numeric score to convert to rating

  Returns:
      Tuple containing (rating_text, color_code)
  """
  if score is None:
    return "N/A", RESET

  if score >= 7.0:
    return "Excellent", RATING_COLORS["Excellent"]
  elif score >= 4.5:
    return "Very Good", RATING_COLORS["Very Good"]
  elif score >= 2.0:
    return "Good", RATING_COLORS["Good"]
  elif score >= 0.0:
    return "Fair", RATING_COLORS["Fair"]
  elif score >= -3.0:
    return "Poor", RATING_COLORS["Poor"]
  else:
    return "Bad", RATING_COLORS["Bad"]


def colorize(text: str, color: str) -> str:
  """Wrap text in the specified color.

  Args:
      text: Text to colorize
      color: Color code from this module

  Returns:
      Colorized text string
  """
  return f"{color}{text}{RESET}"
