import sys
from unittest.mock import MagicMock, patch

# Remove global sys.modules hacking
# mock_tk = MagicMock()
# sys.modules['tkinter'] = mock_tk
# sys.modules['tkinter.ttk'] = MagicMock()
# sys.modules['tkinter.messagebox'] = MagicMock()

import pytest
from src.gui.app import WeatherHelperApp
from src.core.locations import LOCATION_GROUPS


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
        
        yield {
            'tk': mock_tk,
            'ttk': mock_ttk,
            'msgbox': mock_msgbox
        }

def test_group_switching_logic(mock_app_dependencies):
    """Test switching between location groups."""
    # Create app with mocked dependencies
    app = WeatherHelperApp()

    # Verify initial state (generation is 0 because after() is mocked and doesn't run callback)
    assert app.load_generation == 0
    assert app.current_locations == LOCATION_GROUPS["Asturias"]

    # Test switching to Spain
    app.group_var = MagicMock()
    app.group_var.get.return_value = "Spain"

    # Mock UI elements that are accessed
    app.main_table = MagicMock()
    app.location_dropdown = MagicMock()
    app.date_dropdown = MagicMock()
    app.side_panel_entries = []
    app.progress_bar = MagicMock()
    app.subtitle_label = MagicMock()
    app.status_label = MagicMock()

    # Perform switch
    app.on_group_change()

    # Verify new state
    assert app.current_locations == LOCATION_GROUPS["Spain"]
    assert app.load_generation == 1  # Incremented once
    assert app.total_locations == len(LOCATION_GROUPS["Spain"])

    # Test switching to Worldwide
    app.group_var.get.return_value = "Worldwide"
    app.on_group_change()

    assert app.current_locations == LOCATION_GROUPS["Worldwide"]
    assert app.load_generation == 2

def test_generation_check(mock_app_dependencies):
    """Verify that old generation callbacks are ignored."""
    app = WeatherHelperApp()
    initial_gen = app.load_generation

    # Simulate loading completion with OLD generation
    # app.progress_var is a MagicMock from the mocked tk.DoubleVar()
    app.progress_var = MagicMock()
    
    app._on_loading_complete(initial_gen - 1)

    # Should NOT update progress var
    app.progress_var.set.assert_not_called()

    # Simulate loading completion with CURRENT generation
    app._on_loading_complete(initial_gen)
    app.progress_var.set.assert_called_with(100)
