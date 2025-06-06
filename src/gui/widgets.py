"""
Custom Tkinter widgets for the weather helper application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any
from src.gui.themes import COLORS, FONTS, PADDING


class WeatherCard(ttk.Frame):
  """A card widget that displays weather information for a specific time period."""

  def __init__(self, parent, **kwargs):
    super().__init__(parent, **kwargs)
    self.setup_ui()

  def setup_ui(self):
    """Set up the weather card UI components."""
    # Main container with padding and border
    self.configure(padding=PADDING['medium'], style='Card.TFrame')

    # Time and date label
    self.time_label = ttk.Label(
        self,
        text="Loading...",
        font=FONTS['subheading'],
        style='Card.TLabel'
    )
    self.time_label.grid(row=0, column=0, sticky="w", pady=(0, PADDING['small']))

    # Temperature display
    self.temp_label = ttk.Label(
        self,
        text="--°C",
        font=FONTS['heading'],
        style='Card.TLabel'
    )
    self.temp_label.grid(row=1, column=0, sticky="w")

    # Weather condition
    self.weather_label = ttk.Label(
        self,
        text="Loading weather...",
        font=FONTS['body'],
        style='Card.TLabel'
    )
    self.weather_label.grid(row=2, column=0, sticky="w", pady=(PADDING['small'], 0))

    # Additional weather details
    self.details_label = ttk.Label(
        self,
        text="",
        font=FONTS['small'],
        style='Card.TLabel'
    )
    self.details_label.grid(row=3, column=0, sticky="w", pady=(PADDING['small'], 0))

    # Configure grid weights
    self.columnconfigure(0, weight=1)

    # Configure card style
    style = ttk.Style()
    style.configure('Card.TFrame',
                    background=COLORS['background'],
                    relief='solid',
                    borderwidth=1)
    style.configure('Card.TLabel',
                    background=COLORS['background'],
                    foreground=COLORS['text'])

  def update_weather(self, time_str: str, temperature: float, condition: str, details: Optional[Dict[str, Any]] = None):
    """Update the weather information displayed in the card.

    Args:
        time_str: The time to display (e.g., "14:00")
        temperature: The temperature in Celsius
        condition: The weather condition description
        details: Optional dictionary containing additional weather details
    """
    self.time_label.configure(text=time_str)
    self.temp_label.configure(text=f"{temperature:.1f}°C")
    self.weather_label.configure(text=condition)

    # Update additional details if provided
    if details:
      details_text = []
      if 'precipitation_amount' in details:
        details_text.append(f"Rain: {details['precipitation_amount']:.1f}mm")
      if 'wind_speed' in details:
        details_text.append(f"Wind: {details['wind_speed']:.1f}m/s")
      if 'relative_humidity' in details:
        details_text.append(f"Humidity: {details['relative_humidity']:.0f}%")

      self.details_label.configure(text="\n".join(details_text))
    else:
      self.details_label.configure(text="")
