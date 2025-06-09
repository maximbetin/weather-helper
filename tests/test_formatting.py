"""Tests for formatting utilities."""

import pytest
from src.gui.formatting import (
    format_temperature,
    format_percentage,
    format_wind_speed,
    format_time,
    format_date,
    format_duration,
    add_tooltip,
    ToolTip
)
from src.gui.themes import get_rating_color
from src.core.config import NumericType
from datetime import date, datetime
import tkinter as tk
from unittest.mock import MagicMock


def test_format_temperature():
  assert format_temperature(25.5) == "25.5°C"
  assert format_temperature(0) == "0.0°C"
  assert format_temperature(-5.2) == "-5.2°C"
  assert format_temperature(None) == "N/A"
  assert format_temperature(100.0) == "100.0°C"
  assert format_temperature(25.555) == "25.6°C"
  assert format_temperature(-5.222) == "-5.2°C"


def test_format_percentage():
  assert format_percentage(75.5) == "76%"
  assert format_percentage(0) == "0%"
  assert format_percentage(100) == "100%"
  assert format_percentage(None) == "N/A"
  assert format_percentage(0.0) == "0%"
  assert format_percentage(100.0) == "100%"
  assert format_percentage(75.555) == "76%"
  assert format_percentage(0.222) == "0%"


def test_format_percentage_additional():
  # Custom suffix
  assert format_percentage(50, suffix=" pct") == "50 pct"
  # Negative value
  assert format_percentage(-10) == "-10%"
  # Float with decimal
  assert format_percentage(12.34) == "12%"
  # None with custom suffix
  assert format_percentage(None, suffix=" pct") == "N/A"


def test_format_wind_speed():
  assert format_wind_speed(15.5) == "15.5 m/s"
  assert format_wind_speed(0) == "0.0 m/s"
  assert format_wind_speed(100) == "100.0 m/s"
  assert format_wind_speed(None) == "N/A"
  assert format_wind_speed(0.0) == "0.0 m/s"
  assert format_wind_speed(100.0) == "100.0 m/s"
  assert format_wind_speed(15.555) == "15.6 m/s"
  assert format_wind_speed(0.222) == "0.2 m/s"


def test_format_time():
  from datetime import datetime
  assert format_time(datetime(2024, 3, 15, 9, 30)) == "09:30"
  assert format_time(datetime(2024, 3, 15, 0, 0)) == "00:00"
  assert format_time(datetime(2024, 3, 15, 23, 59)) == "23:59"


def test_format_date():
  from datetime import datetime, date
  assert format_date(date(2024, 3, 15)) == "Fri, 15 Mar"
  assert format_date(datetime(2024, 1, 1, 12, 0)) == "Mon, 01 Jan"
  assert format_date(date(2024, 12, 31)) == "Tue, 31 Dec"


def test_format_duration():
  assert format_duration(1) == "1 hour"
  assert format_duration(0) == "0 hours"
  assert format_duration(2) == "2 hours"
  assert format_duration(24) == "24 hours"


def test_get_rating_color():
  assert get_rating_color("Excellent")
  assert get_rating_color("Very Good")
  assert get_rating_color("Good")
  assert get_rating_color("Fair")
  assert get_rating_color("Poor")
  # Unknown rating falls back to text color
  assert get_rating_color("N/A")


def test_tooltip_creation():
  # Create a mock widget
  mock_widget = MagicMock()
  mock_widget.bind = MagicMock()

  # Test that ToolTip can be created
  tooltip = ToolTip(mock_widget, "Test tooltip text")

  assert tooltip.widget == mock_widget
  assert tooltip.text == "Test tooltip text"
  assert tooltip.tooltip_window is None

  # Verify that event bindings were called
  mock_widget.bind.assert_any_call("<Enter>", tooltip.on_enter)
  mock_widget.bind.assert_any_call("<Leave>", tooltip.on_leave)


def test_add_tooltip():
  mock_widget = MagicMock()
  mock_widget.bind = MagicMock()

  tooltip = add_tooltip(mock_widget, "Test tooltip")

  assert isinstance(tooltip, ToolTip)
  assert tooltip.text == "Test tooltip"


class TestTooltipWidget:
  @pytest.fixture
  def root(self):
    # Create a temporary tkinter root for testing.
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()

  def test_tooltip_widget_interaction(self, root):
    # Test tooltip with actual tkinter widget.
    label = tk.Label(root, text="Test")
    tooltip = ToolTip(label, "Test tooltip")

    # Test that tooltip_window starts as None
    assert tooltip.tooltip_window is None

    # Test on_leave method when no tooltip window exists
    tooltip.on_leave()
    assert tooltip.tooltip_window is None
