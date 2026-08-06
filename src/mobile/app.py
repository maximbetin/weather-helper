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
BORDER_COLOR = "#cbd5e1"

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

def _get_activity_icon_name(profile_key: str) -> str:
    return "BEACH_ACCESS" if profile_key == "beach_day" else "HIKING"


def create_mobile_app(
    page: Any,
    *,
    ft: Any = None,
    view_model: Optional[MobileWeatherViewModel] = None,
) -> None:
    """Build a single-scroll forecast overview: filters, daily plan, and a
    ranked location list whose entries expand in place for full detail."""
    ft = ft or _load_flet()
    assert ft is not None
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
    forecast_list = ft.Column(spacing=10)
    daily_summary = ft.Column(spacing=4)

    # --- Styled dropdowns with increased font and padding ---

    def style_dropdown(dd: Any) -> Any:
        dd.dense = True
        dd.border_radius = 10
        dd.content_padding = 12
        dd.border_color = BORDER_COLOR
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

    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=ft.Colors.WHITE,
        icon_size=22,
        tooltip="Refresh forecast",
    )

    def elevated_card(content: Any, *, padding: int = 14) -> Any:
        """Wrap content in a consistently elevated, rounded surface."""
        return ft.Container(
            padding=padding,
            bgcolor=SURFACE_COLOR,
            border_radius=14,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.08, "#0f172a"),
                offset=ft.Offset(0, 2),
            ),
            content=content,
        )

    # --- Hourly forecast rows (shared by every expanded location card) ---

    def hourly_row(row: Any) -> Any:
        return ft.Container(
            padding=ft.Padding(left=0, top=10, right=12, bottom=10),
            bgcolor=BACKGROUND_COLOR,
            border_radius=10,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
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

    def expanded_body(card: RankedLocationView) -> list[Any]:
        color = rating_color(card.rating)
        if card.is_ranked:
            recommendation = [
                ft.Row(
                    spacing=4,
                    controls=[
                        ft.Icon(ft.Icons.ACCESS_TIME, size=18, color=TEXT_COLOR),
                        ft.Text(card.best_window, size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ],
                ),
                ft.Text(card.best_window_details, size=13, color=TEXT_SECONDARY_COLOR),
            ]
        else:
            recommendation = [
                ft.Text(card.best_window_details, size=13, color=TEXT_SECONDARY_COLOR),
            ]

        rows = model.hourly_forecast(card.location_key)
        hourly_controls = (
            [hourly_row(row) for row in rows]
            if rows
            else [ft.Text("No hourly forecast is available.", color=TEXT_SECONDARY_COLOR)]
        )

        return [
            ft.Container(
                padding=ft.Padding(left=16, top=8, right=16, bottom=12),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Divider(height=1, color=color),
                        *recommendation,
                        ft.Container(height=4),
                        *hourly_controls,
                    ],
                ),
            ),
        ]

    def location_tile(
        card: RankedLocationView,
        *,
        leading: Any,
        badge_text: str,
        is_selected: bool,
    ) -> Any:
        color = rating_color(card.rating)
        bg = rating_background(card.rating)
        summary_bits = card.rating if card.is_ranked else "Not ranked"
        subtitle = f"{summary_bits} · {card.weather_description}"

        def on_tile_change(event: Any) -> None:
            if event.data:
                choose_location(card.location_key)

        tile = ft.ExpansionTile(
            key=f"tile_{card.location_key}",
            title=ft.Text(card.location_name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            subtitle=ft.Text(subtitle, size=12, color=TEXT_SECONDARY_COLOR, no_wrap=True),
            leading=leading,
            trailing=ft.Text(badge_text, size=14, weight=ft.FontWeight.BOLD, color=color),
            expanded=is_selected,
            tile_padding=ft.Padding(left=12, top=6, right=12, bottom=6),
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.TRANSPARENT,
            icon_color=color,
            collapsed_icon_color=TEXT_SECONDARY_COLOR,
            on_change=on_tile_change,
            controls=expanded_body(card),
        )
        return ft.Container(
            key=f"card_{card.location_key}",
            bgcolor=bg,
            border=ft.Border.all(1.5 if is_selected else 1, color if is_selected else BORDER_COLOR),
            border_radius=14,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=tile,
        )

    def rank_badge(rank: int, color: str) -> Any:
        return ft.CircleAvatar(
            content=ft.Text(f"{rank}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=color,
            radius=15,
        )

    def choose_location(location_key: str) -> None:
        model.select_location(location_key)
        location_dropdown.value = location_key
        render_forecast_list()
        update_filters_summary()
        page.update()
        page.run_task(page.scroll_to, scroll_key=f"card_{location_key}", duration=300)

    # --- Daily summary ---

    def summary_table_row(summary: Any) -> ft.Row:
        return ft.Row(
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    getattr(ft.Icons, _get_activity_icon_name(summary.activity_profile)),
                    size=14,
                    color=TEXT_SECONDARY_COLOR,
                ),
                ft.Text(
                    summary.location_name,
                    width=96,
                    size=12,
                    color=TEXT_COLOR,
                    no_wrap=True,
                ),
                ft.Text(
                    summary.score_text,
                    width=58,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT,
                    color=PRIMARY_COLOR,
                    no_wrap=True,
                ),
                ft.Text(
                    summary.best_window,
                    expand=True,
                    size=12,
                    color=TEXT_SECONDARY_COLOR,
                    no_wrap=True,
                ),
            ],
        )

    def render_daily_summary() -> None:
        rows = model.daily_summary_rows()
        if not rows:
            daily_summary.controls = [
                ft.Text(
                    "No daily activity recommendations are available.",
                    size=13,
                    color=TEXT_SECONDARY_COLOR,
                )
            ]
            return

        controls = [
            ft.Row(
                spacing=6,
                controls=[
                    ft.Container(width=14),
                    ft.Text("Location", width=96, size=11, color=TEXT_SECONDARY_COLOR),
                    ft.Text("Score", width=58, size=11, color=TEXT_SECONDARY_COLOR),
                    ft.Text("Best time", expand=True, size=11, color=TEXT_SECONDARY_COLOR),
                ],
            )
        ]
        alternatives_started = False
        for summary in rows:
            if not summary.is_priority and not alternatives_started:
                controls.append(ft.Divider(height=8))
                controls.append(
                    ft.Text(
                        "Alternatives",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_SECONDARY_COLOR,
                    )
                )
                alternatives_started = True
            controls.append(summary_table_row(summary))
        daily_summary.controls = controls

    # --- Merged ranking + details list ---

    def render_forecast_list() -> None:
        ranked = model.ranked_locations()
        selected = model.selected_location()
        ranked_keys = {card.location_key for card in ranked}

        tiles = []
        if selected is not None and selected.location_key not in ranked_keys:
            tiles.append(
                location_tile(
                    selected,
                    leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=TEXT_SECONDARY_COLOR),
                    badge_text="N/A",
                    is_selected=True,
                )
            )
        for rank, card in enumerate(ranked, 1):
            tiles.append(
                location_tile(
                    card,
                    leading=rank_badge(rank, rating_color(card.rating)),
                    badge_text=f"{card.normalized_score}",
                    is_selected=card.location_key == model.selected_location_key,
                )
            )

        forecast_list.controls = tiles or [
            ft.Text(
                "No location is available for this date.",
                color=TEXT_SECONDARY_COLOR,
            )
        ]

    def update_location_options() -> None:
        options = model.location_options()
        location_dropdown.options = [
            ft.DropdownOption(key=key, text=name) for key, name in options
        ]
        location_dropdown.disabled = not options
        location_dropdown.hint_text = "Choose a location"
        location_dropdown.value = model.selected_location_key or None

    def update_filters_summary() -> None:
        selected = model.selected_location()
        location_bit = selected.location_name if selected else "no location"
        date_bit = model.selected_date.strftime("%a, %d %b") if model.selected_date else "no date"
        profile_bit = ACTIVITY_PROFILE_LABELS.get(model.activity_profile, model.activity_profile)
        filters_summary.value = f"{model.group_name} · {location_bit} · {date_bit} · {profile_bit}"

    def render_dashboard() -> None:
        update_location_options()
        update_filters_summary()
        render_daily_summary()
        render_forecast_list()
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
        forecast_list.controls = []
        daily_summary.controls = []
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
            forecast_list.controls = []
            daily_summary.controls = []
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

    # --- App bar ---
    page.appbar = ft.AppBar(
        title=ft.Text("Weather Helper", weight=ft.FontWeight.BOLD),
        center_title=False,
        bgcolor=PRIMARY_COLOR,
        color=ft.Colors.WHITE,
        actions=[refresh_button],
    )

    # --- Status row (always visible loading feedback) ---
    status_row = ft.Column(
        spacing=4,
        controls=[status, progress],
    )

    # --- Collapsible filters ---
    filters_summary = ft.Text(
        f"{model.group_name} · Loading…",
        size=12,
        color=TEXT_SECONDARY_COLOR,
        no_wrap=True,
    )
    filters_tile = ft.ExpansionTile(
        title=ft.Text("Filters", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
        subtitle=filters_summary,
        leading=ft.Icon(ft.Icons.TUNE, color=PRIMARY_COLOR),
        tile_padding=ft.Padding(left=14, top=4, right=14, bottom=4),
        collapsed_bgcolor=ft.Colors.TRANSPARENT,
        bgcolor=ft.Colors.TRANSPARENT,
        controls=[
            ft.Container(
                padding=ft.Padding(left=14, top=0, right=14, bottom=14),
                content=ft.ResponsiveRow(
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
            ),
        ],
    )
    filters_card = ft.Container(
        bgcolor=SURFACE_COLOR,
        border=ft.Border.all(1, BORDER_COLOR),
        border_radius=14,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=filters_tile,
    )

    daily_summary_panel = elevated_card(
        ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=18, color=PRIMARY_COLOR),
                        ft.Text("Today's best windows", size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                    ],
                ),
                ft.Text(
                    "Oviedo and Gijón are shown first for hiking and beach plans.",
                    size=12,
                    color=TEXT_SECONDARY_COLOR,
                ),
                daily_summary,
            ],
        )
    )

    ranking_header = ft.Row(
        spacing=6,
        controls=[
            ft.Icon(ft.Icons.LEADERBOARD, size=18, color=PRIMARY_COLOR),
            ft.Text("Ranked locations", size=16, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
        ],
    )
    ranking_hint = ft.Text(
        "Tap a location for its full hourly breakdown.",
        size=12,
        color=TEXT_SECONDARY_COLOR,
    )

    page.add(
        ft.SafeArea(
            expand=True,
            content=ft.ListView(
                expand=True,
                spacing=12,
                padding=12,
                controls=[
                    status_row,
                    filters_card,
                    daily_summary_panel,
                    ranking_header,
                    ranking_hint,
                    forecast_list,
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
