import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from src.gui.app import WeatherHelperApp
from src.gui.formatting import format_date, get_weather_description
from src.core.evaluation import get_rating_info
from src.core.hourly_weather import HourlyWeather
from datetime import datetime, date


@pytest.fixture
def app(tk_root):
  """Fixture to create an instance of the app and mock dependencies."""
  with patch('src.gui.app.fetch_weather_data') as mock_fetch:
    with patch('tkinter.Tk', return_value=tk_root):
      mock_fetch.return_value = None  # Prevents actual API calls
      app_instance = WeatherHelperApp()
      app_instance.root.withdraw()  # Hide the main window during tests
      yield app_instance
      # No need to destroy here, as the tk_root fixture handles it


def test_app_initialization(app):
  """Test if the app initializes correctly."""
  assert app.root.title() == "Weather Helper"
  assert app.main_frame is not None
  assert app.title_label['text'] == "Weather Helper"


def test_selectors_setup(app):
  """Test if the location and date selectors are set up."""
  assert app.location_dropdown is not None
  assert app.date_dropdown is not None


def test_side_panel_setup(app):
  """Test if the side panel is set up with placeholders."""
  assert app.side_panel is not None
  assert len(app.side_panel_entries) == 5


def test_main_table_setup(app):
  """Test if the main table is set up with the correct columns."""
  assert app.main_table is not None
  columns = ("Time", "Score", "Temperature", "Weather", "Wind", "Humidity")
  assert app.main_table['columns'] == columns


def test_get_rating_info():
  assert get_rating_info(20) == "Excellent"
  assert get_rating_info(15) == "Very Good"
  assert get_rating_info(10) == "Good"
  assert get_rating_info(5) == "Fair"
  assert get_rating_info(0) == "Poor"
  assert get_rating_info(None) == "N/A"


def test_format_date():
  test_date = date(2024, 1, 5)
  assert format_date(test_date) == "Fri, 05 Jan"
