"""Tests for the mobile screen, driven through a stand-in for Flet.

Flet cannot be rendered in CI, so the screen is exercised against a recording
double. That is enough to prove the parts that used to break silently: which
values reach the user, what is built lazily, and how failures are surfaced.
"""

from datetime import datetime, timedelta

import pytest

from src.application.forecast_service import ForecastBatch
from src.core.config import get_current_date
from src.core.models import DailyReport, HourlyWeather
from src.core.scoring import (
    cloud_score,
    humidity_score,
    precip_amount_score,
    temp_score,
    wind_score,
)
from src.mobile.app import create_mobile_app
from src.mobile.view_model import MobileWeatherViewModel

flet = pytest.importorskip("flet")


class StubService:
    def __init__(self, batch, error=None):
        self.batch = batch
        self.error = error
        self.calls = 0

    def load_locations(self, locations, on_progress=None):
        self.calls += 1
        if self.error:
            raise self.error
        if on_progress:
            for index, location in enumerate(locations.values(), 1):
                on_progress(index, len(locations), location)
        return self.batch


class FakePage:
    """A page that records what the screen puts on it."""

    def __init__(self):
        self.controls = []
        self.appbar = None
        self.title = ""
        self.padding = None
        self.bgcolor = None
        self.theme_mode = None
        self.platform_brightness = flet.Brightness.LIGHT
        self.on_platform_brightness_change = None
        self.on_app_lifecycle_state_change = None
        self.updates = 0
        self.tasks = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updates += 1

    def run_task(self, handler, *args, **kwargs):
        self.tasks.append((handler, args, kwargs))


def _hour(forecast_date, hour_of_day, temp=24, **overrides):
    values = {
        "temp": temp,
        "wind": 2,
        "cloud_coverage": 15,
        "precipitation_amount": 0.0,
        "precipitation_probability": 5,
        "relative_humidity": 55,
    }
    values.update(overrides)
    return HourlyWeather(
        time=datetime.combine(forecast_date, datetime.min.time()).replace(
            hour=hour_of_day
        ),
        temp_score=temp_score(values["temp"]),
        wind_score=wind_score(values["wind"]),
        cloud_score=cloud_score(values["cloud_coverage"]),
        precip_amount_score=precip_amount_score(values["precipitation_amount"]),
        humidity_score=humidity_score(values["relative_humidity"]),
        **values,
    )


def _processed(name, forecast_date, hours):
    return {
        "daily_forecasts": {forecast_date: hours},
        "day_scores": {
            forecast_date: DailyReport(
                datetime.combine(forecast_date, datetime.min.time()), hours, name
            )
        },
        "timezone": "Europe/Madrid",
    }


def _batch(forecast_date, **extra):
    forecasts = {
        "gijon": _processed(
            "Gijón", forecast_date, [_hour(forecast_date, h, 26) for h in range(10, 18)]
        ),
        "oviedo": _processed(
            "Oviedo", forecast_date, [_hour(forecast_date, h, 15) for h in range(10, 18)]
        ),
    }
    forecasts.update(extra)
    return ForecastBatch(forecasts=forecasts)


def _screen(batch=None, error=None, brightness=None):
    """Build the screen and run its initial load synchronously."""
    forecast_date = get_current_date() + timedelta(days=1)
    model = MobileWeatherViewModel(
        service=StubService(batch or _batch(forecast_date), error)
    )
    page = FakePage()
    if brightness is not None:
        page.platform_brightness = brightness
    create_mobile_app(page, ft=flet, view_model=model)
    return page, model


def _run_pending_tasks(page):
    import asyncio

    while page.tasks:
        handler, args, kwargs = page.tasks.pop(0)
        result = handler(*args, **kwargs)
        if asyncio.iscoroutine(result):
            asyncio.run(result)


def _all_text(control, found=None):
    """Collect every string rendered anywhere in a control tree."""
    found = [] if found is None else found
    if isinstance(control, flet.Text) and control.value:
        found.append(control.value)
    if isinstance(control, flet.Markdown) and control.value:
        found.append(control.value)
    for attribute in ("controls", "actions"):
        for child in getattr(control, attribute, None) or []:
            _all_text(child, found)
    for attribute in ("content", "title", "subtitle", "leading", "trailing"):
        child = getattr(control, attribute, None)
        if child is not None and not isinstance(child, str):
            _all_text(child, found)
    return found


def _screen_text(page):
    texts = []
    for control in page.controls:
        _all_text(control, texts)
    if page.appbar is not None:
        _all_text(page.appbar, texts)
    return texts


def test_the_screen_leads_with_the_best_place_and_window():
    page, model = _screen()
    _run_pending_tasks(page)

    texts = _screen_text(page)
    best = model.top_recommendation()

    assert best is not None
    assert best.location_name == "Gijón"
    # The answer, the window and the score are all present without expanding.
    assert "Gijón" in texts
    assert best.best_window in texts
    assert str(best.normalized_score) in texts


def test_scores_are_always_shown_out_of_one_hundred():
    page, _ = _screen()
    _run_pending_tasks(page)

    texts = _screen_text(page)

    assert "/100" in texts
    assert any(text == "Excellent" or text == "Very Good" for text in texts)


def test_a_ratings_legend_is_always_visible():
    page, _ = _screen()
    _run_pending_tasks(page)

    texts = _screen_text(page)

    for rating in ("Excellent", "Very Good", "Good", "Fair", "Poor"):
        assert rating in texts


def test_collapsed_cards_do_not_build_their_hourly_rows():
    page, model = _screen()
    _run_pending_tasks(page)

    texts = _screen_text(page)

    # Nothing is expanded, so no hourly time labels are rendered yet.
    assert "10:00" not in texts
    assert "11:00" not in texts


def test_expanding_a_card_builds_its_hours_and_marks_the_best_window():
    page, model = _screen()
    _run_pending_tasks(page)
    screen = _find_screen(page)

    screen.on_tile_toggle("gijon", True)

    texts = _screen_text(page)
    assert "10:00" in texts
    assert "BEST" in texts


def test_collapsing_a_card_drops_its_hourly_rows_again():
    page, _ = _screen()
    _run_pending_tasks(page)
    screen = _find_screen(page)

    screen.on_tile_toggle("gijon", True)
    screen.on_tile_toggle("gijon", False)

    assert "10:00" not in _screen_text(page)


def test_missing_readings_render_as_a_dash_not_as_weather():
    forecast_date = get_current_date() + timedelta(days=1)
    hours = [
        _hour(forecast_date, hour, 24, precipitation_amount=None, cloud_coverage=None)
        for hour in range(10, 18)
    ]
    batch = ForecastBatch(
        forecasts={"gijon": _processed("Gijón", forecast_date, hours)}
    )
    page, _ = _screen(batch)
    _run_pending_tasks(page)
    screen = _find_screen(page)

    screen.on_tile_toggle("gijon", True)

    texts = _screen_text(page)
    assert "—" in texts
    assert "0.0 mm" not in texts


def test_a_failed_load_says_so_instead_of_showing_nothing():
    page, _ = _screen(error=RuntimeError("no network"))
    _run_pending_tasks(page)

    texts = _screen_text(page)

    assert any("Could not load forecasts" in text for text in texts)


def test_unavailable_locations_are_named():
    forecast_date = get_current_date() + timedelta(days=1)
    batch = ForecastBatch(
        forecasts={
            "gijon": _processed(
                "Gijón",
                forecast_date,
                [_hour(forecast_date, h) for h in range(10, 18)],
            )
        },
        errors={"oviedo": "offline"},
        failed_names={"oviedo": "Oviedo"},
    )
    page, _ = _screen(batch)
    _run_pending_tasks(page)

    texts = _screen_text(page)

    assert any("Oviedo" in text and "unavailable" in text for text in texts)


def test_the_screen_reports_when_the_data_was_loaded():
    page, _ = _screen()
    _run_pending_tasks(page)

    assert any("Updated" in text for text in _screen_text(page))


def test_days_are_labelled_relative_to_today():
    page, _ = _screen()
    _run_pending_tasks(page)
    screen = _find_screen(page)

    labels = [option.text for option in screen.date_dropdown.options]

    assert "Tomorrow" in labels


def test_the_dark_palette_is_used_on_a_dark_device():
    page, _ = _screen(brightness=flet.Brightness.DARK)
    _run_pending_tasks(page)

    assert page.bgcolor == "#0f172a"


def test_a_stale_selection_recovers_instead_of_failing_silently():
    page, model = _screen()
    _run_pending_tasks(page)
    screen = _find_screen(page)

    # A location that is not available any more must not raise out of a handler.
    screen.on_tile_toggle("nowhere", True)

    assert any("no longer available" in text for text in _screen_text(page))


def test_a_slow_load_never_overwrites_a_newer_one():
    """Switching region twice quickly must not let the first result win."""
    import asyncio
    import threading

    forecast_date = get_current_date() + timedelta(days=1)
    release_first = threading.Event()

    class SlowThenFastService:
        def __init__(self):
            self.calls = 0

        def load_locations(self, locations, on_progress=None):
            self.calls += 1
            if self.calls == 1:
                release_first.wait(timeout=5)
                return ForecastBatch(forecasts={}, errors={"all": "stale"})
            return _batch(forecast_date)

    model = MobileWeatherViewModel(service=SlowThenFastService())
    page = FakePage()
    create_mobile_app(page, ft=flet, view_model=model)
    page.tasks.clear()  # Drive the loads explicitly instead.
    screen = _find_screen(page)

    async def overlapping_loads():
        slow = asyncio.create_task(screen.refresh_forecast())
        await asyncio.sleep(0)
        fast = asyncio.create_task(screen.refresh_forecast())
        await fast
        finished_status = screen.status.value
        release_first.set()
        await slow
        return finished_status

    status_after_fast = asyncio.run(overlapping_loads())

    assert "2 locations loaded" in status_after_fast
    # The stale result landed later but must not have replaced the newer one.
    assert screen.status.value == status_after_fast


def _find_screen(page):
    """Recover the screen object from the handlers it registered."""
    return page.on_platform_brightness_change.__self__
