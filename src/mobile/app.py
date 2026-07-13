"""Minimal Flet UI for the first Weather Helper mobile milestone."""

import asyncio
from datetime import date
from importlib import import_module
from typing import Any, Optional

from src.core.locations import LOCATION_GROUPS
from src.core.scoring import ACTIVITY_PROFILE_LABELS
from src.mobile.view_model import MobileWeatherViewModel, RankedLocationView

BACKGROUND_COLOR = "#f8fafc"
SURFACE_COLOR = "#ffffff"
TEXT_COLOR = "#1e293b"
TEXT_SECONDARY_COLOR = "#64748b"
PRIMARY_COLOR = "#1e3a8a"
RATING_COLORS = {
    "Excellent": "#15803d",
    "Very Good": "#65a30d",
    "Good": "#ca8a04",
    "Fair": "#ea580c",
    "Poor": "#b91c1c",
}
RATING_BACKGROUNDS = {
    "Excellent": "#f0fdf4",
    "Very Good": "#f7fee7",
    "Good": "#fefce8",
    "Fair": "#fff7ed",
    "Poor": "#fef2f2",
}

FLET_INSTALL_HINT = (
    "Flet is not installed in the active environment. Activate a project virtual "
    "environment, install the mobile extra with `python -m pip install -e "
    "\".[mobile]\"`, then run `flet run weather_helper_mobile.py`."
)


def _load_flet():
    try:
        return import_module("flet")
    except ModuleNotFoundError as exc:
        raise RuntimeError(FLET_INSTALL_HINT) from exc


def rating_color(rating: str) -> str:
    """Return the same rating color used by the Windows application."""
    return RATING_COLORS.get(rating, TEXT_COLOR)


def rating_background(rating: str) -> str:
    """Return a subtle background that keeps rating cards readable."""
    return RATING_BACKGROUNDS.get(rating, SURFACE_COLOR)


def create_mobile_app(
    page: Any,
    *,
    ft: Optional[Any] = None,
    view_model: Optional[MobileWeatherViewModel] = None,
) -> None:
    """Build a compact, touch-friendly forecast comparison screen."""
    ft = ft or _load_flet()
    model = view_model or MobileWeatherViewModel()

    page.title = "Weather Helper"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = BACKGROUND_COLOR

    status = ft.Text("Loading the default Asturias forecast…")
    progress = ft.ProgressBar(visible=False)
    results = ft.Column(spacing=8)
    hourly = ft.Column(spacing=8)
    hourly_heading = ft.Text(
        "Hourly Forecast",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=TEXT_COLOR,
    )
    hourly_hint = ft.Text(
        "Select a location above to view its hourly details.",
        color=TEXT_SECONDARY_COLOR,
    )

    group_dropdown = ft.Dropdown(
        label="Region",
        value=model.group_name,
        options=[ft.DropdownOption(key=name, text=name) for name in LOCATION_GROUPS],
    )
    profile_dropdown = ft.Dropdown(
        label="Activity",
        value=model.activity_profile,
        options=[
            ft.DropdownOption(key=key, text=label)
            for key, label in ACTIVITY_PROFILE_LABELS.items()
        ],
    )
    date_dropdown = ft.Dropdown(label="Date", disabled=True, options=[])
    refresh_button = ft.Button(content="Refresh forecast")

    def render_hourly(card: RankedLocationView) -> None:
        rows = model.hourly_forecast(card.location_key)
        hourly_heading.value = f"Hourly Forecast · {card.location_name}"
        hourly_hint.value = "All available hours for the selected date."
        hourly.controls = [
            ft.Container(
                padding=12,
                bgcolor=SURFACE_COLOR,
                border=ft.Border.all(1, rating_color(row.rating)),
                border_radius=10,
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=3,
                            controls=[
                                ft.Text(
                                    row.time,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_COLOR,
                                ),
                                ft.Text(
                                    f"Temperature: {row.temperature} · Wind: {row.wind}",
                                    color=TEXT_COLOR,
                                ),
                                ft.Text(
                                    f"Clouds: {row.clouds} · Rain: {row.precipitation}",
                                    color=TEXT_SECONDARY_COLOR,
                                ),
                                ft.Text(
                                    f"Rain Risk: {row.rain_risk} · Humidity: {row.humidity}",
                                    color=TEXT_SECONDARY_COLOR,
                                ),
                            ],
                        ),
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            controls=[
                                ft.Text(
                                    f"{row.normalized_score}/100",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=rating_color(row.rating),
                                ),
                                ft.Text(
                                    row.rating,
                                    color=rating_color(row.rating),
                                ),
                            ],
                        ),
                    ],
                ),
            )
            for row in rows
        ]
        if not rows:
            hourly.controls = [ft.Text("No hourly forecast is available.")]

    def select_location(location_key: str):
        return lambda event: render_results(location_key)

    def location_card(card: RankedLocationView, selected: bool):
        color = rating_color(card.rating)
        return ft.Container(
            padding=12,
            bgcolor=rating_background(card.rating),
            border=ft.Border.all(3 if selected else 1, color),
            border_radius=12,
            ink=True,
            on_click=select_location(card.location_key),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(
                                f"#{card.rank}  {card.location_name}",
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_COLOR,
                            ),
                            ft.Text(
                                f"{card.weather_description} · "
                                f"Best Window: {card.best_window}.",
                                color=TEXT_COLOR,
                            ),
                            ft.Text(
                                card.best_window_details,
                                color=TEXT_SECONDARY_COLOR,
                            ),
                            ft.Text(
                                "Selected · hourly details shown below"
                                if selected
                                else "Tap to view hourly details →",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                        ],
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            ft.Text(
                                f"{card.normalized_score}/100",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                            ft.Text(card.rating, color=color),
                        ],
                    ),
                ],
            ),
        )

    def render_results(preferred_location_key: Optional[str] = None) -> None:
        cards = model.ranked_locations()
        if not cards:
            results.controls = [ft.Text("No ranked locations are available for this date.")]
            hourly_heading.value = "Hourly Forecast"
            hourly_hint.value = "No location is selected."
            hourly.controls = []
            page.update()
            return

        card_keys = {card.location_key for card in cards}
        selected_key = preferred_location_key or model.selected_location_key
        if selected_key not in card_keys:
            selected_key = cards[0].location_key
        selected_card = next(card for card in cards if card.location_key == selected_key)
        render_hourly(selected_card)
        result_controls = []
        for card in cards:
            selected = card.location_key == selected_key
            result_controls.append(location_card(card, selected))
            if selected:
                result_controls.extend([hourly_heading, hourly_hint, hourly])
        results.controls = result_controls
        page.update()

    def update_date_options() -> None:
        available_dates = model.available_dates()
        date_dropdown.options = [
            ft.DropdownOption(key=value.isoformat(), text=f"{value:%a, %d %b}")
            for value in available_dates
        ]
        date_dropdown.disabled = not available_dates
        date_dropdown.value = model.selected_date.isoformat() if model.selected_date else None

    def on_group_select(event: Any) -> None:
        model.select_group(event.control.value)
        update_date_options()
        results.controls = []
        hourly.controls = []
        hourly_heading.value = "Hourly Forecast"
        hourly_hint.value = "Loading the selected region…"
        status.value = f"Loading {model.group_name} forecasts…"
        page.update()
        page.run_task(refresh_forecast)

    def on_profile_select(event: Any) -> None:
        model.select_activity_profile(event.control.value)
        render_results()

    def on_date_select(event: Any) -> None:
        model.select_date(date.fromisoformat(event.control.value))
        render_results()

    async def refresh_forecast(event: Any = None) -> None:
        refresh_button.disabled = True
        group_dropdown.disabled = True
        progress.visible = True
        status.value = f"Loading {model.group_name} forecasts…"
        page.update()

        try:
            batch = await asyncio.to_thread(model.load)
            update_date_options()
            status.value = f"Loaded {batch.loaded_count} locations"
            if batch.errors:
                status.value += f" · {len(batch.errors)} failed"
            render_results()
        except Exception as exc:
            status.value = f"Unable to load forecasts: {exc}"
            results.controls = []
            hourly.controls = []
        finally:
            progress.visible = False
            refresh_button.disabled = False
            group_dropdown.disabled = False
            page.update()

    group_dropdown.on_select = on_group_select
    profile_dropdown.on_select = on_profile_select
    date_dropdown.on_select = on_date_select
    refresh_button.on_click = refresh_forecast

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.ListView(
                expand=True,
                spacing=12,
                padding=12,
                controls=[
                    ft.Text(
                        "Weather Helper",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=PRIMARY_COLOR,
                    ),
                    ft.Text(
                        "Compare whole-day outdoor weather scores.",
                        color=TEXT_SECONDARY_COLOR,
                    ),
                    group_dropdown,
                    profile_dropdown,
                    date_dropdown,
                    refresh_button,
                    progress,
                    status,
                    ft.Divider(),
                    ft.Text("Top Locations", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Colors indicate rating quality. Tap any location for details.",
                        color=TEXT_SECONDARY_COLOR,
                    ),
                    results,
                ],
            )
        )
    )
    page.run_task(refresh_forecast)


def main() -> None:
    """Run Weather Helper with Flet's desktop/mobile development host."""
    ft = _load_flet()
    ft.run(create_mobile_app)


if __name__ == "__main__":
    main()
