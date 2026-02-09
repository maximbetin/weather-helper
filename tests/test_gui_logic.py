import sys
from unittest.mock import MagicMock, patch

# Mock tkinter before importing app
mock_tk = MagicMock()
sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

# Now import the app
from src.gui.app import WeatherHelperApp
from src.core.locations import LOCATION_GROUPS

def test_group_switching_logic():
        # Setup mock app
        with patch('src.gui.app.apply_theme'), \
             patch('src.gui.app.fetch_weather_data'), \
             patch('threading.Thread'):

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

def test_generation_check():
    """Verify that old generation callbacks are ignored."""
    with patch('src.gui.app.apply_theme'), \
         patch('src.gui.app.fetch_weather_data') as mock_fetch, \
         patch('threading.Thread'):

        app = WeatherHelperApp()
        initial_gen = app.load_generation

        # Simulate loading completion with OLD generation
        app.progress_var = MagicMock()
        app._on_loading_complete(initial_gen - 1)

        # Should NOT update progress var (mock shouldn't be called)
        # But wait, progress_var is initialized in _setup_status_bar.
        # We need to verify that set() was NOT called.
        # However, _setup_status_bar is called in __init__, so progress_var is a Mock from tk.DoubleVar()
        # But we mocked tk, so app.progress_var is a MagicMock.

        app.progress_var.reset_mock()
        app._on_loading_complete(initial_gen - 1)
        app.progress_var.set.assert_not_called()

        # Simulate loading completion with CURRENT generation
        app._on_loading_complete(initial_gen)
        app.progress_var.set.assert_called_with(100)
