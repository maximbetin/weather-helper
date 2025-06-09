"""Tests for formatting utilities."""

import tkinter as tk
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.gui.formatting import ToolTip, add_tooltip, format_date, format_duration, format_percentage, format_temperature, format_time, format_wind_speed
from src.gui.themes import get_rating_color


def test_format_temperature():
  """Test temperature formatting."""
  assert format_temperature(20.5) == "20.5°C"
  assert format_temperature(None) == "N/A"
  assert format_temperature(0) == "0.0°C"
  assert format_temperature(-5.3) == "-5.3°C"
  assert format_temperature(15, "°F") == "15.0°F"


def test_format_percentage():
  """Test percentage formatting."""
  assert format_percentage(75.6) == "76%"
  assert format_percentage(None) == "N/A"
  assert format_percentage(0) == "0%"
  assert format_percentage(100) == "100%"
  assert format_percentage(50.4, " percent") == "50 percent"


def test_format_percentage_additional():
  """Test additional percentage formatting edge cases."""
  assert format_percentage(99.9) == "100%"
  assert format_percentage(0.1) == "0%"
  assert format_percentage(50.5) == "50%"  # Tests rounding (rounds to nearest even)


def test_format_wind_speed():
  """Test wind speed formatting."""
  assert format_wind_speed(5.2) == "5.2 m/s"
  assert format_wind_speed(None) == "N/A"
  assert format_wind_speed(0) == "0.0 m/s"
  assert format_wind_speed(12.7, " km/h") == "12.7 km/h"


def test_format_time():
  """Test time formatting."""
  dt = datetime(2024, 3, 15, 14, 30, 45)
  assert format_time(dt) == "14:30"

  dt_midnight = datetime(2024, 3, 15, 0, 0)
  assert format_time(dt_midnight) == "00:00"

  dt_noon = datetime(2024, 3, 15, 12, 15)
  assert format_time(dt_noon) == "12:15"


def test_format_date():
  """Test date formatting."""
  # Test with date object
  d = date(2024, 3, 15)
  assert format_date(d) == "Fri, 15 Mar"

  # Test with datetime object
  dt = datetime(2024, 3, 15, 14, 30)
  assert format_date(dt) == "Fri, 15 Mar"

  # Test different dates
  d_jan = date(2024, 1, 1)
  assert format_date(d_jan) == "Mon, 01 Jan"


def test_format_duration():
  """Test duration formatting with proper pluralization."""
  assert format_duration(1) == "1 hour"
  assert format_duration(0) == "0 hours"
  assert format_duration(2) == "2 hours"
  assert format_duration(24) == "24 hours"


def test_get_rating_color():
  """Test color assignment for ratings."""
  assert get_rating_color("Excellent") == "#15803d"  # Darker Green
  assert get_rating_color("Very Good") == "#65a30d"  # Darker Yellow-Green
  assert get_rating_color("Good") == "#ca8a04"       # Darker Yellow
  assert get_rating_color("Fair") == "#ea580c"       # Darker Orange
  assert get_rating_color("Poor") == "#b91c1c"       # Darker Red
  assert get_rating_color("Unknown") == "#1e293b"    # text color (default)


def test_tooltip_creation():
  """Test tooltip creation."""
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
  """Test add_tooltip convenience function."""
  mock_widget = MagicMock()
  mock_widget.bind = MagicMock()

  tooltip = add_tooltip(mock_widget, "Test tooltip")

  assert isinstance(tooltip, ToolTip)
  assert tooltip.text == "Test tooltip"


class TestTooltipWidget:
  """Test tooltip widget behavior with a real tkinter widget."""

  @pytest.fixture
  def root(self):
    """Create a temporary tkinter root for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    root.destroy()

  def test_tooltip_widget_interaction(self, root):
    """Test tooltip with actual tkinter widget."""
    label = tk.Label(root, text="Test")
    tooltip = ToolTip(label, "Test tooltip")

    # Test that tooltip_window starts as None
    assert tooltip.tooltip_window is None

    # Test on_leave method when no tooltip window exists
    tooltip.on_leave()
    assert tooltip.tooltip_window is None


class TestToolTipAdvanced:
  """Advanced tests for ToolTip functionality."""

  @pytest.fixture
  def mock_widget(self):
    """Create a mock widget with necessary methods."""
    widget = MagicMock()
    widget.bind = MagicMock()
    widget.winfo_rootx.return_value = 100
    widget.winfo_rooty.return_value = 200
    widget.bbox.return_value = (10, 20, 30, 40)
    return widget

  def test_tooltip_on_enter_with_bbox(self, mock_widget):
    """Test tooltip on_enter when widget has bbox method."""
    tooltip = ToolTip(mock_widget, "Test tooltip")

    # Mock Toplevel and Label creation
    with patch('tkinter.Toplevel') as mock_toplevel, \
            patch('tkinter.Label') as mock_label:

      mock_top = MagicMock()
      mock_toplevel.return_value = mock_top
      mock_lbl = MagicMock()
      mock_label.return_value = mock_lbl

      # Test on_enter
      tooltip.on_enter()

      # Verify Toplevel was created with correct position
      mock_toplevel.assert_called_once_with(mock_widget)
      mock_top.wm_overrideredirect.assert_called_once_with(True)
      mock_top.wm_geometry.assert_called_once_with("+130+240")  # 100+10+20, 200+20+20

      # Verify Label was created with correct text
      mock_label.assert_called_once()
      call_args = mock_label.call_args[1]
      assert call_args['text'] == "Test tooltip"
      assert call_args['background'] == "#ffffe0"

      # Verify tooltip_window is set
      assert tooltip.tooltip_window == mock_top

  def test_tooltip_on_enter_without_bbox(self, mock_widget):
    """Test tooltip on_enter when widget doesn't have bbox method."""
    # Remove bbox method
    del mock_widget.bbox

    tooltip = ToolTip(mock_widget, "Test tooltip")

    with patch('tkinter.Toplevel') as mock_toplevel, \
            patch('tkinter.Label') as mock_label:

      mock_top = MagicMock()
      mock_toplevel.return_value = mock_top

      # Test on_enter
      tooltip.on_enter()

      # Should use default bbox values (0, 0, 0, 0)
      mock_top.wm_geometry.assert_called_once_with("+120+220")  # 100+0+20, 200+0+20

  def test_tooltip_on_enter_already_exists(self, mock_widget):
    """Test tooltip on_enter when tooltip window already exists."""
    tooltip = ToolTip(mock_widget, "Test tooltip")
    tooltip.tooltip_window = MagicMock()  # Simulate existing tooltip

    with patch('tkinter.Toplevel') as mock_toplevel:
      # Test on_enter - should return early
      tooltip.on_enter()

      # Toplevel should not be called since tooltip already exists
      mock_toplevel.assert_not_called()

  def test_tooltip_on_leave_destroys_window(self, mock_widget):
    """Test tooltip on_leave destroys the tooltip window."""
    tooltip = ToolTip(mock_widget, "Test tooltip")

    # Create a mock tooltip window
    mock_window = MagicMock()
    tooltip.tooltip_window = mock_window

    # Test on_leave
    tooltip.on_leave()

    # Verify window was destroyed and reference cleared
    mock_window.destroy.assert_called_once()
    assert tooltip.tooltip_window is None

  def test_tooltip_hasattr_check(self, mock_widget):
    """Test the hasattr check for bbox method."""
    tooltip = ToolTip(mock_widget, "Test tooltip")

    # Test with bbox method present
    assert hasattr(mock_widget, 'bbox')

    # Remove bbox and test
    del mock_widget.bbox
    assert not hasattr(mock_widget, 'bbox')
