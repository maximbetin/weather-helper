import tkinter as tk
from datetime import datetime

import pytest

from src.core.models import HourlyWeather


@pytest.fixture
def sample_hourly_weather():
    """Fixture providing a sample HourlyWeather object for testing."""
    return HourlyWeather(
        time=datetime(2024, 3, 15, 12),
        temp=20,
        wind=5,
        cloud_coverage=20,
        precipitation_amount=0,
        temp_score=8,
        wind_score=9,
        cloud_score=10,
        precip_amount_score=6,
    )


@pytest.fixture
def sample_forecast_data():
    """Fixture providing sample forecast data for testing."""
    # test_date = date(2024, 3, 15)  # Unused variable removed
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
