import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

from src.core.models import HourlyWeather


def test_populate_location_entry(mock_app):
    app = mock_app

    # Create sample data matching what get_top_locations_for_date returns
    loc_data = {
        "location_name": "Test Location",
        "avg_score": 85.5,
        "optimal_block": {
            "start": datetime(2023, 1, 1, 10, 0),
            "end": datetime(2023, 1, 1, 14, 0),
            "temp": 22.5,
            "wind": 5.0,
            "precip": 0.0
        }
    }

    rank_label, name_label, score_label, details_label = app.side_panel_entries[0]

    # Call the method
    app._populate_location_entry(
        1, loc_data, rank_label, name_label, score_label, details_label
    )

    # Verify calls
    rank_label.config.assert_called_with(text="#1")
    name_label.config.assert_called_with(text="Test Location")
    # Check if score text contains expected values
    score_args = score_label.config.call_args[1]
    assert "85.5" in score_args['text']
    assert "Excellent" in score_args['text'] or "Very Good" in score_args['text'] # Depending on threshold

def test_update_main_table_rendering(mock_app, create_hour):
    app = mock_app
    app.selected_location_key = "test_loc"
    app.selected_date = date(2023, 1, 1)

    # Create sample processed data
    # We need a structure that get_time_blocks_for_date can consume
    # It takes a processed dict with "daily_forecasts"

    # Create a real HourlyWeather object using helper
    hw = create_hour(
        time=datetime(2023, 1, 1, 12, 0),
        total_score=20, # 5+5+5+5
        temp=20.0,
        wind=10.0
    )
    # create_hour defaults: temp=20, wind=1. We override wind.
    # We also need to set specific fields if the test checks them.
    # The test checks: values[1] == "20.0°C", values[4] == "0.0 mm"
    # create_hour sets precip=0.0 by default.

    processed_data = {
        "daily_forecasts": {
            date(2023, 1, 1): [hw]
        }
    }

    app.all_location_processed = {"test_loc": processed_data}

    # Mock get_time_blocks_for_date to return our list directly
    with patch('src.gui.app.get_time_blocks_for_date', return_value=[hw]):
        app._update_main_table()

    # Verify insert was called
    app.main_table.insert.assert_called()

    # Verify values passed to insert
    call_args = app.main_table.insert.call_args
    values = call_args[1]['values']

    # Check format
    assert values[0] == "12:00"
    assert values[1] == "20.0°C"
    assert values[4] == "0.0 mm" # Precip
