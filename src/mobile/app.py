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


def _get_cloud_icon(ft: Any, cloud_str: str) -> Any:
    try:
        val = float(cloud_str.replace('%', '').strip())
        if val < 20: return ft.Icon(ft.Icons.WB_SUNNY, color=ft.Colors.YELLOW_600, size=15)
        elif val < 60: return ft.Icon(ft.Icons.CLOUD_QUEUE, color=ft.Colors.GREY_400, size=15)
        else: return ft.Icon(ft.Icons.CLOUD, color=ft.Colors.GREY_500, size=15)
    except Exception:
        return ft.Icon(ft.Icons.CLOUD, color=ft.Colors.GREY_500, size=15)

def _get_rain_icon(ft: Any, rain_str: str) -> Any:
    try:
        val = float(rain_str.split()[0])
        if val == 0: return ft.Icon(ft.Icons.WATER_DROP_OUTLINED, color=ft.Colors.GREY_400, size=15)
        elif val < 2.0: return ft.Icon(ft.Icons.WATER_DROP, color=ft.Colors.LIGHT_BLUE_400, size=15)
        else: return ft.Icon(ft.Icons.WATER_DROP, color=ft.Colors.BLUE_600, size=15)
    except Exception:
        return ft.Icon(ft.Icons.WATER_DROP, color=ft.Colors.BLUE_600, size=15)

def _get_wind_icon(ft: Any, wind_str: str) -> Any:
    try:
        val = float(wind_str.split()[0])
        if val < 3: return ft.Icon(ft.Icons.AIR, color=ft.Colors.GREY_400, size=15)
        elif val < 8: return ft.Icon(ft.Icons.AIR, color=ft.Colors.BLUE_400, size=15)
        else: return ft.Icon(ft.Icons.WIND_POWER, color=ft.Colors.BLUE_600, size=15)
    except Exception:
        return ft.Icon(ft.Icons.AIR, color=ft.Colors.GREY_400, size=15)

def _get_temp_icon(ft: Any, temp_str: str) -> Any:
    try:
        val = float(temp_str.split()[0])
        if val < 10: return ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.BLUE_400, size=15)
        elif val < 25: return ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.ORANGE_400, size=15)
        else: return ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.RED_400, size=15)
    except Exception:
        return ft.Icon(ft.Icons.THERMOSTAT, color=ft.Colors.ORANGE_400, size=15)

def _get_humidity_icon(ft: Any, hum_str: str) -> Any:
    return ft.Icon(ft.Icons.WATER, color=ft.Colors.LIGHT_BLUE_400, size=15)


def create_mobile_app(
    page: Any,
    *,
    ft: Any = None,
    view_model: Optional[MobileWeatherViewModel] = None,
) -> None:
    """Build a responsive forecast overview with persistent ranking and details."""
    ft = ft or _load_flet()
    assert ft is not None
    model = view_model or MobileWeatherViewModel()

    page.title = "Weather Helper"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = BACKGROUND_COLOR

    status = ft.Text(
        "Loading the default Asturias forecast\u2026",
        color=TEXT_SECONDARY_COLOR,
        size=13,
    )
    progress = ft.ProgressBar(visible=False)
    ranking = ft.Column(spacing=6)
    selected_summary = ft.Column(spacing=8)
    hourly = ft.Column(spacing=8)

    # --- Styled dropdowns with increased font and padding ---

    def style_dropdown(dd: Any) -> Any:
        dd.dense = True
        dd.border_radius = 10
        dd.content_padding = 12
        dd.border_color = "#cbd5e1"
        dd.text_size = 15
        dd.expand = True
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
        hint_text="Loading locations\u2026",
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

    # --- Refresh icon button ---
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=PRIMARY_COLOR,
        icon_size=24,
        tooltip="Refresh forecast",
    )

    # --- Details rendering ---

    def render_details(card: RankedLocationView) -> None:
        color = rating_color(card.rating)
        bg = rating_background(card.rating)

        # Apply rating tint to the details panel
        details_panel.bgcolor = bg
        details_panel.border = ft.Border.all(1, color)

        if card.is_ranked:
            summary_context = (
                f"#{card.rank} in {model.group_name} \u00b7 {card.weather_description}"
            )
            score_controls = [
                ft.Text(
                    f"{card.normalized_score}/100",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                ),
                ft.Text(card.rating, size=14, color=color),
            ]
            recommendation_controls = [
                ft.Divider(height=1, color=color),
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(ft.Icons.ACCESS_TIME, size=18, color=TEXT_COLOR),
                        ft.Text(card.best_window, size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ]
                ),
                ft.Text(card.best_window_details, size=13, color=TEXT_SECONDARY_COLOR),
            ]
        else:
            summary_context = (
                f"Not ranked in {model.group_name} \u00b7 {card.weather_description}"
            )
            score_controls = [
                ft.Text("Not ranked", weight=ft.FontWeight.BOLD, color=color),
            ]
            recommendation_controls = [
                ft.Divider(height=1, color=color),
                ft.Text(card.best_window_details, size=13, color=TEXT_SECONDARY_COLOR),
            ]
        selected_summary.controls = [
            ft.Container(
                padding=16,
                bgcolor=bg,
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
                                            size=13,
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
        hourly.controls = [
            ft.Container(
                padding=ft.Padding(left=0, top=10, right=12, bottom=10),
                bgcolor=SURFACE_COLOR,
                border_radius=10,
                content=ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    controls=[
                        # Color accent bar on the left
                        ft.Container(
                            width=5,
                            height=70,
                            bgcolor=rating_color(row.rating),
                            border_radius=ft.BorderRadius(
                                top_left=10, bottom_left=10,
                                top_right=0, bottom_right=0,
                            ),
                        ),
                        ft.Container(width=10),
                        # Weather info
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(
                                    row.time,
                                    size=17,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT_COLOR,
                                ),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        _get_temp_icon(ft, row.temperature),
                                        ft.Text(f"{row.temperature}", size=14, color=TEXT_COLOR),
                                        ft.Container(width=8),
                                        _get_wind_icon(ft, row.wind),
                                        ft.Text(f"{row.wind}", size=14, color=TEXT_COLOR),
                                    ],
                                ),
                                ft.Row(
                                    spacing=4,
                                    controls=[
                                        _get_cloud_icon(ft, row.clouds),
                                        ft.Text(f"{row.clouds}", size=13, color=TEXT_SECONDARY_COLOR),
                                        ft.Container(width=4),
                                        _get_rain_icon(ft, row.precipitation),
                                        ft.Text(f"{row.precipitation}", size=13, color=TEXT_SECONDARY_COLOR),
                                        ft.Container(width=4),
                                        _get_humidity_icon(ft, row.humidity),
                                        ft.Text(f"{row.humidity}", size=13, color=TEXT_SECONDARY_COLOR),
                                    ],
                                ),
                            ],
                        ),
                        # Score badge
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=0,
                            controls=[
                                ft.Text(
                                    f"{row.normalized_score}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=rating_color(row.rating),
                                ),
                                ft.Text(
                                    row.rating,
                                    size=11,
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
        page.run_task(page.scroll_to, scroll_key="details_panel", duration=300)

    # --- Top 10 ranking (read-only overview) ---

    def ranking_row(card: RankedLocationView) -> ft.Container:
        color = rating_color(card.rating)
        return ft.Container(
            padding=10,
            bgcolor=rating_background(card.rating),
            border=ft.Border.all(1, color),
            border_radius=10,
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                f"#{card.rank}",
                                width=30,
                                text_align=ft.TextAlign.CENTER,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=color,
                            ),
                            ft.Text(
                                card.location_name,
                                expand=True,
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_COLOR,
                            ),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=0,
                                controls=[
                                    ft.Text(
                                        f"{card.normalized_score}/100",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=color,
                                    ),
                                    ft.Text(card.rating, size=11, color=color),
                                ],
                            ),
                        ],
                    ),
                    # Centered optimal time
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.ACCESS_TIME, size=15, color=TEXT_SECONDARY_COLOR),
                            ft.Text(card.best_window, size=13, color=TEXT_SECONDARY_COLOR, text_align=ft.TextAlign.CENTER),
                        ]
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
        ranking.controls = [ranking_row(card) for card in cards]

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
            details_panel.bgcolor = SURFACE_COLOR
            details_panel.border = ft.Border.all(1, "#cbd5e1")
            selected_summary.controls = []
            hourly.controls = [
                ft.Text(
                    "No location is available for this date.",
                    color=TEXT_SECONDARY_COLOR,
                )
            ]
        page.update()

    def update_date_options() -> None:
        available_dates = model.available_dates()
        date_dropdown.options = [
            ft.DropdownOption(key=value.isoformat(), text=f"{value:%a, %d/%m}")
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
        status.value = f"Loading {model.group_name} forecasts\u2026"
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
        status.value = f"Loading {model.group_name} forecasts\u2026"
        page.update()

        try:
            batch = await asyncio.to_thread(model.load)
            update_date_options()
            if batch.loaded_count:
                status.value = f"Loaded {batch.loaded_count} locations"
                if batch.errors:
                    status.value += f" \u00b7 {len(batch.errors)} unavailable"
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

    # --- Filter panel content ---
    filter_content = ft.Container(
        padding=14,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=14,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Filters", size=16, weight=ft.FontWeight.BOLD),
                        refresh_button,
                    ],
                ),
                ft.ResponsiveRow(
                    columns=12,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.Container(col={"xs": 12, "sm": 6}, content=group_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=location_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=date_dropdown),
                        ft.Container(col={"xs": 12, "sm": 6}, content=profile_dropdown),
                    ],
                ),
                progress,
                status,
            ],
        ),
    )

    # --- Top 10 ranking panel content ---
    ranking_content = ft.Container(
        padding=14,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#e2e8f0"),
        border_radius=14,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text("Top 10", size=16, weight=ft.FontWeight.BOLD),
                ranking,
            ],
        ),
    )

    # --- Swipable tabs for Filters and Top 10 ---
    swipe_tabs = ft.Tabs(
        length=2,
        selected_index=0,
        animation_duration=300,
        content=ft.Column(
            height=450,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Filters"),
                        ft.Tab(label="Top 10"),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(
                            padding=ft.Padding(left=0, top=12, right=0, bottom=0),
                            content=filter_content,
                        ),
                        ft.Container(
                            padding=ft.Padding(left=0, top=12, right=0, bottom=0),
                            content=ft.Column(
                                [ranking_content],
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    # --- Details panel (color-tinted per selection) ---
    details_panel = ft.Container(
        key="details_panel",
        padding=16,
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, "#cbd5e1"),
        border_radius=14,
        content=ft.Column(
            spacing=10,
            controls=[
                selected_summary,
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
                    swipe_tabs,
                    details_panel,
                    ft.Markdown(
                        f"Data from [MET Norway]({MET_NORWAY_SOURCE_URL}), "
                        f"processed by Weather Helper \u00b7 "
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
