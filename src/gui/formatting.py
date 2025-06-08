"""
This module contains utility functions for formatting data for display in the GUI.
"""
from datetime import date, datetime
from typing import Union, Optional
import tkinter as tk


class ToolTip:
  """Simple tooltip implementation for GUI widgets."""

  def __init__(self, widget, text):
    self.widget = widget
    self.text = text
    self.tooltip_window = None
    self.widget.bind("<Enter>", self.on_enter)
    self.widget.bind("<Leave>", self.on_leave)

  def on_enter(self, event=None):
    """Show tooltip on mouse enter."""
    if self.tooltip_window:
      return

    x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
    x += self.widget.winfo_rootx() + 20
    y += self.widget.winfo_rooty() + 20

    self.tooltip_window = tw = tk.Toplevel(self.widget)
    tw.wm_overrideredirect(True)
    tw.wm_geometry(f"+{x}+{y}")

    label = tk.Label(
        tw,
        text=self.text,
        justify='left',
        background="#ffffe0",
        relief='solid',
        borderwidth=1,
        font=("Segoe UI", 8),
        wraplength=300
    )
    label.pack(ipadx=1)

  def on_leave(self, event=None):
    """Hide tooltip on mouse leave."""
    if self.tooltip_window:
      self.tooltip_window.destroy()
      self.tooltip_window = None


def add_tooltip(widget, text):
  """Add a tooltip to a widget."""
  return ToolTip(widget, text)


def format_time(dt: datetime) -> str:
  """Format a datetime object to display time.

  Args:
      dt: The datetime to format

  Returns:
      str: Formatted time string (e.g., "14:30")
  """
  return dt.strftime("%H:%M")


def format_date(d: Union[date, datetime]) -> str:
  """Format a date or datetime object.

  Args:
      d: The date or datetime to format

  Returns:
      Formatted date string
  """
  if isinstance(d, datetime):
    d = d.date()

  return d.strftime("%a, %d %b")


def format_duration(hours: int) -> str:
  """Format duration in hours with proper pluralization.

  Args:
      hours: Number of hours

  Returns:
      Formatted duration string
  """
  if hours == 1:
    return "1 hour"
  else:
    return f"{hours} hours"


def format_temperature(temp: Optional[float], unit: str = "°C") -> str:
  """Format temperature with proper unit and fallback.

  Args:
      temp: Temperature value
      unit: Temperature unit

  Returns:
      Formatted temperature string
  """
  if temp is not None:
    return f"{temp:.1f}{unit}"
  return "N/A"


def format_percentage(value: Optional[float], suffix: str = "%") -> str:
  """Format percentage value with proper fallback.

  Args:
      value: Percentage value
      suffix: Percentage suffix

  Returns:
      Formatted percentage string
  """
  if value is not None:
    return f"{value:.0f}{suffix}"
  return "N/A"


def format_wind_speed(speed: Optional[float], unit: str = " m/s") -> str:
  """Format wind speed with proper unit and fallback.

  Args:
      speed: Wind speed value
      unit: Speed unit

  Returns:
      Formatted wind speed string
  """
  if speed is not None:
    return f"{speed:.1f}{unit}"
  return "N/A"


def get_weather_description(symbol: Optional[str]) -> str:
  """Return a human-readable weather description from a symbol code.

  Args:
      symbol: The weather symbol code.

  Returns:
      A human-readable weather description.
  """
  weather_map = {
      'clearsky': 'Clear Sky',
      'fair': 'Fair',
      'partlycloudy': 'Partly Cloudy',
      'cloudy': 'Cloudy',
      'lightrain': 'Light Rain',
      'lightrainshowers': 'Light Rain Showers',
      'rain': 'Rain',
      'rainshowers': 'Rain Showers',
      'heavyrain': 'Heavy Rain',
      'heavyrainshowers': 'Heavy Rain Showers',
      'lightsnow': 'Light Snow',
      'snow': 'Snow',
      'fog': 'Fog',
      'thunderstorm': 'Thunderstorm',
      'sleet': 'Sleet',
      'lightsleet': 'Light Sleet',
      'sleetshowers': 'Sleet Showers',
      'lightsleetshowers': 'Light Sleet Showers',
      'heavysnow': 'Heavy Snow',
      'heavysnowshowers': 'Heavy Snow Showers',
  }
  s = symbol.lower() if symbol else ''
  return weather_map.get(s, s.replace("_", " ").title())
