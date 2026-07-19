"""Responsive Flet interface for desktop previews and Android builds."""

import asyncio
from datetime import date
from importlib import import_module
from typing import Any, Optional

from src.application.presentation import (
    BASE_COLORS,
    get_rating_background as rating_background,
    get_rating_color as rating_color,
)
from src.core.config import MET_NORWAY_LICENSE_URL, MET_NORWAY_SOURCE_URL
from src.core.locations import LOCATION_GROUPS
from src.core.scoring import ACTIVITY_PROFILE_LABELS
from src.mobile.view_model import MobileWeatherViewModel, RankedLocationView

BACKGROUND_COLOR = BASE_COLORS["background"]
SURFACE_COLOR = BASE_COLORS["surface"]
TEXT_COLOR = BASE_COLORS["text"]
TEXT_SECONDARY_COLOR = BASE_COLORS["text_secondary"]
PRIMARY_COLOR = BASE_COLORS["primary"]

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


def create_mobile_app(
    page: Any,
    *,
    ft: Optional[Any] = None,
    view_model: Optional[MobileWeatherViewModel] = None,
) -> None:
    """Build a responsive forecast overview with persistent ranking and details."""
    ft = ft or _load_flet()
    model = view_model or MobileWeatherViewModel()

    page.title = "Weather Helper"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = BACKGROUND_COLOR

    status = ft.Text(
        "Loading the default Asturias forecast…",
        color=TEXT_SECONDARY_COLOR,
        size=13,
    )
    progress = ft.ProgressBar(visible=False)
    ranking = ft.Column(spacing=6)
    selected_summary = ft.Column(spacing=8)
    hourly = ft.Column(spacing=8)
    detail_heading = ft.Text("Location Forecast", size=21, weight=ft.FontWeight.BOLD)
    detail_context = ft.Text(
        "Choose any loaded location to view its hourly forecast.",
        color=TEXT_SECONDARY_COLOR,
    )

    def style_dropdown(dd: ft.Dropdown) -> ft.Dropdown:
        dd.dense = True
        dd.border_radius = 8
        dd.content_padding = 10
        dd.border_color = "#cbd5e1"
        return dd

    group_dropdown = style_dropdown(ft.Dropdown(
        label="Region",
        value=model.group_name,
        options=[ft.DropdownOption(key=name, text=name) for name in LOCATION_GROUPS],
    ))
    location_dropdown = style_dropdown(ft.Dropdown(
        label="Location",
        disabled=True,
        options=[],
        hint_text="Loading locations…",
    ))
    profile_dropdown = style_dropdown(ft.Dropdown(
        label="Activity",
        value=model.activity_profile,
        options=[
            ft.DropdownOption(key=key, text=label)
            for key, label in ACTIVITY_PROFILE_LABELS.items()
        ],
    ))
    date_dropdown = style_dropdown(ft.Dropdown(label="Date", disabled=True, options=[]))
    details_header = ft.Text(
        "SELECTED LOCATION",
        size=12,
        weight=ft.FontWeight.BOLD,
        color=PRIMARY_COLOR,
    )
    refresh_button = ft.Button(content="Refresh forecast")

    def render_details(card: RankedLocationView) -> None:
        color = rating_color(card.rating)
        if card.is_ranked:
            summary_context = (
                f"#{card.rank} in {model.group_name} · {card.weather_description}"
            )
            score_controls = [
                ft.Text(
                    f"{card.normalized_score}/100",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                ),
                ft.Text(card.rating, color=color),
            ]
            recommendation_controls = [
                ft.Divider(height=1, color=color),
                ft.Text(
                    f"Best Window: {card.best_window}.",
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_COLOR,
                ),
                ft.Text(card.best_window_details, color=TEXT_SECONDARY_COLOR),
            ]
        else:
            summary_context = (
                f"Not ranked in {model.group_name} · {card.weather_description}"
            )
            score_controls = [
                ft.Text("Not ranked", weight=ft.FontWeight.BOLD, color=color),
            ]
            recommendation_controls = [
                ft.Divider(height=1, color=color),
                ft.Text(card.best_window_details, color=TEXT_SECONDARY_COLOR),
            ]
        selected_summary.controls = [
            ft.Container(
                padding=16,
                bgcolor=rating_background(card.rating),
                border=ft.Border.all(2, color),
                border_radius=12,
                content=ft.Column(
                    spacing=7,
                    controls=[
                        ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            card.location_name,
                                            size=23,
                                            weight=ft.FontWeight.BOLD,
                                            color=TEXT_COLOR,
                                        ),
                                        ft.Text(
                                            summary_context,
                                            color=TEXT_SECONDARY_COLOR,
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=1,
                                    controls=score_controls,
                                ),
                            ],
                        ),
                        *recommendation_controls,
                    ],
                ),
            )
        ]

        rows = model.hourly_forecast(card.location_key)
        selected_date = model.selected_date
        date_label = f"{selected_date:%A, %d %B}" if selected_date else "selected date"
        detail_heading.value = f"Hourly Forecast · {card.location_name}"
        details_header.value = f"VIEWING DETAILS FOR: {card.location_name.upper()}"
        detail_context.value = (
            f"{date_label} · {ACTIVITY_PROFILE_LABELS[model.activity_profile]} · "
            "each row is one forecast hour"
        )
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
                                    f"Temperature {row.temperature} · Wind {row.wind}",
                                    color=TEXT_COLOR,
                                ),
                                ft.Text(
                                    f"Clouds {row.clouds} · Rain {row.precipitation}",
                                    color=TEXT_SECONDARY_COLOR,
                                ),
                                ft.Text(
                                    f"Rain Risk {row.rain_risk} · Humidity {row.humidity}",
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

    def choose_location(location_key: str) -> None:
        model.select_location(location_key)
        location_dropdown.value = location_key
        render_ranking()
        selected = model.selected_location()
        if selected:
            render_details(selected)
        page.update()
        page.scroll_to(key="details_panel", duration=300)

    def select_ranked_location(location_key: str):
        return lambda event: choose_location(location_key)

    def ranking_row(card: RankedLocationView, selected: bool):
        color = rating_color(card.rating)
        return ft.Container(
            padding=6,
            bgcolor=rating_background(card.rating) if selected else SURFACE_COLOR,
            border=ft.Border.all(2 if selected else 1, color),
            border_radius=9,
            ink=True,
            on_click=select_ranked_location(card.location_key),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"{card.rank}",
                        width=22,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.BOLD,
                        color=color,
                    ),
                    ft.Text(
                        expand=True,
                        value=("Selected · " if selected else "")
                        + f"{card.location_name} · {card.best_window}",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_COLOR,
                        max_lines=1,
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=0,
                        controls=[
                            ft.Text(
                                f"{card.normalized_score}/100",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                            ft.Text(card.rating, size=10, color=color),
                        ],
                    ),
                ],
            ),
        )

    def render_ranking() -> None:
        cards = model.ranked_locations()
        if not cards:
            ranking.controls = [
                ft.Text("No ranked locations are available for this date.")
            ]
            return
        ranking.controls = [
            ranking_row(card, card.location_key == model.selected_location_key)
            for card in cards
        ]

    def update_location_options() -> None:
        options = model.location_options()
        location_dropdown.options = [
            ft.DropdownOption(key=key, text=name) for key, name in options
        ]
        location_dropdown.disabled = not options
        location_dropdown.hint_text = "Choose a location"
        location_dropdown.value = model.selected_location_key or None

    def render_dashboard() -> None:
        update_location_options()
        render_ranking()
        card = model.selected_location()
        if card:
            render_details(card)
        else:
            detail_heading.value = "Location Forecast"
            details_header.value = "SELECTED LOCATION"
            detail_context.value = "No location is available for this date."
            selected_summary.controls = []
            hourly.controls = []
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
        location_dropdown.options = []
        location_dropdown.value = None
        location_dropdown.disabled = True
        ranking.controls = []
        selected_summary.controls = []
        hourly.controls = []
        detail_heading.value = "Location Forecast"
        detail_context.value = "Loading the selected region…"
        status.value = f"Loading {model.group_name} forecasts…"
        page.update()
        page.run_task(refresh_forecast)

    def on_location_select(event: Any) -> None:
        choose_location(event.control.value)

    def on_profile_select(event: Any) -> None:
        model.select_activity_profile(event.control.value)
        render_dashboard()

    def on_date_select(event: Any) -> None:
        model.select_date(date.fromisoformat(event.control.value))
        render_dashboard()

    async def refresh_forecast(event: Any = None) -> None:
        refresh_button.disabled = True
        group_dropdown.disabled = True
        progress.visible = True
        status.value = f"Loading {model.group_name} forecasts…"
        page.update()

        try:
            batch = await asyncio.to_thread(model.load)
            update_date_options()
            if batch.loaded_count:
                status.value = f"Loaded {batch.loaded_count} locations"
                if batch.errors:
                    status.value += f" · {len(batch.errors)} unavailable"
            else:
                status.value = (
                    "No forecasts could be loaded. Check your connection and try again."
                )
            render_dashboard()
        except Exception:
            status.value = "Unable to load forecasts right now. Please try again."
            ranking.controls = []
            selected_summary.controls = []
            hourly.controls = []
        finally:
            progress.visible = False
            refresh_button.disabled = False
            group_dropdown.disabled = False
            page.update()

    group_dropdown.on_select = on_group_select
    location_dropdown.on_select = on_location_select
    profile_dropdown.on_select = on_profile_select
    date_dropdown.on_select = on_date_select
    refresh_button.on_click = refresh_forecast

    filter_panel = ft.Container(
        col={"sm": 12, "md": 5},
        padding=16,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=14,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Plan Your Day", size=21, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Choose a region for the overview, or select any specific "
                    "location for its full forecast.",
                    color=TEXT_SECONDARY_COLOR,
                ),
                ft.ResponsiveRow(
                    columns=12,
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        ft.Container(col={"xs": 12, "sm": 6}, content=group_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=location_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=date_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=profile_dropdown),
                    ],
                ),
                refresh_button,
                progress,
                status,
            ],
        ),
    )
    ranking_panel = ft.Container(
        col={"sm": 12, "md": 7},
        padding=16,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=14,
        content=ft.Column(
            spacing=5,
            controls=[
                ft.Text("Regional Top 10", size=21, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "A quick whole-day comparison. Tap a row to inspect it; "
                    "the ranking stays in place.",
                    color=TEXT_SECONDARY_COLOR,
                ),
                ranking,
            ],
        ),
    )
    details_panel = ft.Container(
        key="details_panel",
        padding=16,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#cbd5e1"),
        border_radius=14,
        content=ft.Column(
            spacing=10,
            controls=[
                details_header,
                selected_summary,
                ft.Divider(),
                detail_heading,
                detail_context,
                hourly,
            ],
        ),
    )

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
                        "See the regional outlook, then inspect any place hour by hour.",
                        color=TEXT_SECONDARY_COLOR,
                    ),
                    ft.ResponsiveRow(
                        columns=12,
                        spacing=12,
                        run_spacing=12,
                        controls=[filter_panel, ranking_panel],
                    ),
                    details_panel,
                    ft.Markdown(
                        f"Data from [MET Norway]({MET_NORWAY_SOURCE_URL}), "
                        f"processed by Weather Helper · "
                        f"[license]({MET_NORWAY_LICENSE_URL})",
                        selectable=True,
                    ),
                ],
            ),
        )
    )
    page.run_task(refresh_forecast)


def main() -> None:
    """Run Weather Helper with Flet's desktop/mobile development host."""
    ft = _load_flet()
    ft.run(create_mobile_app)


if __name__ == "__main__":
    main()
