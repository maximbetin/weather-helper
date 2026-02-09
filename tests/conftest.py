import tkinter as tk
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.core.models import HourlyWeather
from src.gui.app import WeatherHelperApp


@pytest.fixture
def sample_hourly_weather():
    """Fixture providing a sample HourlyWeather object for testing."""
    return HourlyWeather(
        time=datetime(2024, 3, 15, 12),
        temp=20,
        wind=5,
        cloud_coverage=20,
        precipitation_amount=0,
        relative_humidity=60,
        temp_score=8,
        wind_score=9,
        cloud_score=10,
        precip_amount_score=6,
        humidity_score=1,
    )


@pytest.fixture
def sample_forecast_data():
    """Fixture providing sample forecast data for testing."""
    test_date = date(2024, 3, 15)  # noqa: F841
    return {
        "properties": {
            "timeseries": [
                {
                    "time": "2024-03-15T12:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 20,
                                "wind_speed": 5,
                                "relative_humidity": 60,
                                "cloud_area_fraction": 20,
                            }
                        },
                        "next_1_hours": {
                            "summary": {"symbol_code": "clearsky"},
                            "details": {
                                "precipitation_amount": 0,
                                "probability_of_precipitation": 0,
                            },
                        },
                    },
                }
            ]
        }
    }


@pytest.fixture(scope="session")
def tk_root():
    """Fixture to create a single Tkinter root for the entire test session."""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def create_hour():
    """Helper to create HourlyWeather with flexible arguments."""
    def _create(time, total_score=None, **kwargs):
        # Default values
        defaults = {
            'temp': 20,
            'wind': 1,
            'precipitation_amount': 0.0,
            'relative_humidity': 60,
            'cloud_coverage': 20,
            'temp_score': 0,
            'wind_score': 0,
            'cloud_score': 0,
            'precip_amount_score': 0,
            'humidity_score': 0
        }

        # If total_score is provided, override score defaults
        if total_score is not None:
            base = total_score // 4
            remainder = total_score - (3 * base)
            defaults.update({
                'temp_score': base,
                'wind_score': base,
                'cloud_score': base,
                'precip_amount_score': remainder
            })

        # Update defaults with provided kwargs
        defaults.update(kwargs)

        return HourlyWeather(time=time, **defaults)
    return _create


@pytest.fixture
def mock_app_dependencies():
    """Patch Tkinter dependencies in app module."""
    with patch('src.gui.app.tk') as mock_tk, \
         patch('src.gui.app.ttk') as mock_ttk, \
         patch('src.gui.app.messagebox') as mock_msgbox, \
         patch('src.gui.app.apply_theme'), \
         patch('src.gui.app.fetch_weather_data'), \
         patch('threading.Thread'):

        # Setup common mock behaviors
        mock_tk.Tk.return_value = MagicMock()
        mock_tk.DoubleVar.return_value = MagicMock()
        mock_tk.StringVar.return_value = MagicMock()
        mock_tk.IntVar.return_value = MagicMock()
        mock_tk.BooleanVar.return_value = MagicMock()

        yield {
            'tk': mock_tk,
            'ttk': mock_ttk,
            'msgbox': mock_msgbox
        }


@pytest.fixture
def mock_app(mock_app_dependencies):
    """Create a mocked WeatherHelperApp with dependencies already mocked."""
    app = WeatherHelperApp()

    # Mock UI components
    app.main_table = MagicMock()
    app.status_label = MagicMock()
    app.subtitle_label = MagicMock()
    app.progress_bar = MagicMock()
    app.location_dropdown = MagicMock()
    app.date_dropdown = MagicMock()
    app.group_var = MagicMock()

    # Mock side panel entries
    app.side_panel_entries = []
    for _ in range(5):
        app.side_panel_entries.append((
            MagicMock(), MagicMock(), MagicMock(), MagicMock()
        ))

    app.show_scores = MagicMock()
    app.show_scores.get.return_value = True

    return app
