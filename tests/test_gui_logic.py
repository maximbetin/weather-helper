import pytest
from unittest.mock import MagicMock
from src.application.forecast_service import LocationForecastResult
from src.gui.app import WeatherHelperApp
from src.core.locations import LOCATION_GROUPS

pytestmark = pytest.mark.windows_gui


def test_group_switching_logic(mock_app):
    """Test switching between location groups."""
    app = mock_app

    # Verify initial state (generation is 0 because after() is mocked and doesn't run callback)
    assert app.load_generation == 0
    assert app.current_locations == LOCATION_GROUPS["Asturias"]

    # Test switching to Spain
    app.group_var.get.return_value = "Spain"

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

def test_generation_check(mock_app):
    """Verify that old generation callbacks are ignored."""
    app = mock_app
    initial_gen = app.load_generation

    # Simulate loading completion with OLD generation
    # app.progress_var is a MagicMock from the mocked tk.DoubleVar() in mock_app_dependencies
    # mock_app fixture already sets up app.progress_var via mock_app_dependencies implicitly?
    # Actually mock_app fixture sets app.progress_bar = MagicMock().
    # But WeatherHelperApp.__init__ sets self.progress_var = tk.DoubleVar().
    # Since mock_app uses mock_app_dependencies, tk.DoubleVar() returns a MagicMock.
    # So app.progress_var is a MagicMock.

    app._on_loading_complete(initial_gen - 1)

    # Should NOT update progress var
    app.progress_var.set.assert_not_called()

    # Simulate loading completion with CURRENT generation
    app._on_loading_complete(initial_gen)
    app.progress_var.set.assert_called_with(100)


def test_stale_worker_cannot_write_results_into_new_region(mock_app):
    """A request that finishes after a region switch must be discarded."""
    app = mock_app
    app.load_generation = 1
    app.root.after.reset_mock()
    old_locations = {"old": MagicMock(name="old_location")}

    def finish_after_switch(location):
        app.load_generation = 2
        return LocationForecastResult(location=location, forecast={"old": True})

    app.forecast_service.load_location = finish_after_switch
    app._load_all_forecasts_threaded(1, old_locations)

    assert app.all_location_processed == {}
    assert app.loaded_locations == set()
    assert app.root.after.call_count == 1  # queued progress only, no completion
    app.root.after.call_args.args[1]()
    app.progress_var.set.assert_not_called()


def test_stale_completion_payload_is_ignored(mock_app):
    app = mock_app
    app.load_generation = 3

    app._on_loading_complete(2, {"old": {"stale": True}}, {"bad": "stale"})

    assert app.all_location_processed == {}
    assert app.loading_errors == {}
