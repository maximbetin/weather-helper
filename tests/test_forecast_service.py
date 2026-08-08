import time

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
        process=lambda payload, name, timezone_name=None: processed,
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
        process=lambda payload, name, timezone_name=None: {"name": name},
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
    # Locations are fetched concurrently, so only the counts are guaranteed.
    assert [current for current, _, _ in progress] == [1, 2]
    assert {total for _, total, _ in progress} == {2}
    assert {key for _, _, key in progress} == {"good", "bad"}


def test_load_location_converts_dependency_exception_to_error():
    location = Location("test", "Test", 1.0, 2.0)

    def fail(location):
        raise RuntimeError("network unavailable")

    result = ForecastService(fetch_forecast=fail).load_location(location)

    assert not result.succeeded
    assert result.error == UNEXPECTED_ERROR
    assert "network unavailable" not in result.error


def test_locations_are_loaded_concurrently():
    """A slow location must not hold up the rest of the region."""
    locations = {
        f"loc{index}": Location(f"loc{index}", f"Loc {index}", 1.0, 2.0)
        for index in range(6)
    }

    def slow_fetch(location):
        time.sleep(0.15)
        return {}

    service = ForecastService(
        fetch_forecast=slow_fetch,
        process=lambda payload, name, timezone_name=None: {"name": name},
    )

    started = time.monotonic()
    batch = service.load_locations(locations)
    elapsed = time.monotonic() - started

    assert batch.loaded_count == 6
    # Sequentially this would take at least 0.9s.
    assert elapsed < 0.6


def test_results_keep_the_requested_location_order():
    locations = {
        key: Location(key, key.title(), 1.0, 2.0)
        for key in ("gijon", "oviedo", "llanes", "aviles")
    }

    def variable_fetch(location):
        time.sleep(0.05 if location.key == "gijon" else 0.0)
        return {}

    service = ForecastService(
        fetch_forecast=variable_fetch,
        process=lambda payload, name, timezone_name=None: {"name": name},
    )

    batch = service.load_locations(locations)

    assert list(batch.forecasts) == list(locations)


def test_failed_locations_are_named_for_the_user():
    locations = {
        "gijon": Location("gijon", "Gijón", 1.0, 2.0),
        "oviedo": Location("oviedo", "Oviedo", 1.0, 2.0),
        "llanes": Location("llanes", "Llanes", 1.0, 2.0),
    }
    service = ForecastService(fetch_forecast=lambda location: None)

    batch = service.load_locations(locations)

    assert batch.failure_summary == "Gijón, Llanes, Oviedo"


def test_a_long_list_of_failures_is_summarised():
    locations = {
        f"loc{index}": Location(f"loc{index}", f"Loc {index}", 1.0, 2.0)
        for index in range(6)
    }
    service = ForecastService(fetch_forecast=lambda location: None)

    batch = service.load_locations(locations)

    assert batch.failure_summary.endswith("and 3 more")


def test_loading_no_locations_is_not_an_error():
    batch = ForecastService(fetch_forecast=lambda location: None).load_locations({})

    assert batch.loaded_count == 0
    assert batch.failure_summary == ""
