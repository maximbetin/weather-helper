from src.application.forecast_service import (
    DOWNLOAD_ERROR,
    UNEXPECTED_ERROR,
    ForecastService,
)
from src.core.locations import Location


def test_load_location_fetches_and_processes_forecast():
    location = Location("test", "Test", 1.0, 2.0)
    raw = {"properties": {"timeseries": []}}
    processed = {"daily_forecasts": {}, "day_scores": {}}
    service = ForecastService(
        fetch_forecast=lambda requested: raw,
        process=lambda payload, name: processed,
    )

    result = service.load_location(location)

    assert result.succeeded
    assert result.location == location
    assert result.forecast == processed
    assert result.error is None


def test_load_locations_keeps_partial_success_and_reports_progress():
    locations = {
        "good": Location("good", "Good", 1.0, 2.0),
        "bad": Location("bad", "Bad", 3.0, 4.0),
    }
    progress = []
    service = ForecastService(
        fetch_forecast=lambda location: {} if location.key == "good" else None,
        process=lambda payload, name: {"name": name},
    )

    batch = service.load_locations(
        locations,
        on_progress=lambda current, total, location: progress.append(
            (current, total, location.key)
        ),
    )

    assert batch.forecasts == {"good": {"name": "Good"}}
    assert batch.errors == {"bad": DOWNLOAD_ERROR}
    assert batch.loaded_count == 1
    assert progress == [(1, 2, "good"), (2, 2, "bad")]


def test_load_location_converts_dependency_exception_to_error():
    location = Location("test", "Test", 1.0, 2.0)

    def fail(location):
        raise RuntimeError("network unavailable")

    result = ForecastService(fetch_forecast=fail).load_location(location)

    assert not result.succeeded
    assert result.error == UNEXPECTED_ERROR
    assert "network unavailable" not in result.error
