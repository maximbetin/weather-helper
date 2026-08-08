"""Responsive Flet interface for desktop previews and Android builds.

The screen is built around one question: where should I go, and when. The
answer is at the top in full, the ranked alternatives follow, and every score
on screen is traceable to the hours listed inside the card that produced it.
"""

import asyncio
from dataclasses import dataclass
from datetime import date
from importlib import import_module
from typing import Any, Callable, Optional

from src.application.presentation import (
    MISSING_VALUE,
    RATING_ORDER,
    format_optional,
    format_percentage,
    format_precipitation,
    format_relative_date,
    format_temperature,
    format_wind_speed,
)
from src.core.config import (
    DAYLIGHT_END_HOUR,
    DAYLIGHT_START_HOUR,
    MET_NORWAY_LICENSE_URL,
    MET_NORWAY_SOURCE_URL,
    get_current_date,
)
from src.core.locations import LOCATION_GROUPS
from src.core.scoring import ACTIVITY_PROFILE_LABELS
from src.mobile.theme import (
    BODY_SIZE,
    CARD_RADIUS,
    HEADLINE_SIZE,
    LABEL_SIZE,
    SPACING,
    SUBTITLE_SIZE,
    TITLE_SIZE,
    Palette,
)
from src.mobile.view_model import (
    HourlyForecastView,
    MobileWeatherViewModel,
    RankedLocationView,
)

FLET_INSTALL_HINT = (
    "Flet is not installed in the active environment. Activate a project virtual "
    "environment, install the mobile extra with `python -m pip install -e "
    "\".[mobile]\"`, then run `flet run weather_helper_mobile.py`."
)

RANKED_LOCATION_COUNT = 10


@dataclass(frozen=True)
class _Metric:
    """One weather reading: its icon, its spoken label and its formatter."""

    icon: str
    label: str
    formatter: Any


TEMPERATURE = _Metric("THERMOSTAT", "Temperature", format_temperature)
WIND = _Metric("AIR", "Wind", format_wind_speed)
CLOUDS = _Metric("CLOUD_QUEUE", "Cloud cover", format_percentage)
RAIN = _Metric("WATER_DROP_OUTLINED", "Precipitation", format_precipitation)
HUMIDITY = _Metric("WATER", "Humidity", format_percentage)


def _load_flet():
    try:
        return import_module("flet")
    except ModuleNotFoundError as exc:
        raise RuntimeError(FLET_INSTALL_HINT) from exc


def create_mobile_app(
    page: Any,
    *,
    ft: Any = None,
    view_model: Optional[MobileWeatherViewModel] = None,
) -> None:
    """Build the forecast screen: today's answer, then the ranked alternatives."""
    ft = ft or _load_flet()
    assert ft is not None
    model = view_model or MobileWeatherViewModel()
    screen = _Screen(page, ft, model)
    screen.build()


class _Screen:
    """Owns the Flet controls and keeps them in step with the view model."""

    def __init__(self, page: Any, ft: Any, model: MobileWeatherViewModel) -> None:
        self.page = page
        self.ft = ft
        self.model = model
        self.palette = Palette(dark=self._prefers_dark())
        self._load_generation = 0
        self._expanded_keys: set[str] = set()

    # --- Colour and theme -------------------------------------------------

    def _prefers_dark(self) -> bool:
        """Return True when the device is currently in dark mode."""
        ft = self.ft
        return getattr(self.page, "platform_brightness", None) == ft.Brightness.DARK

    def _apply_theme(self) -> None:
        ft = self.ft
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.bgcolor = self.palette.background

    # --- Small shared building blocks -------------------------------------

    def _text(
        self,
        value: str,
        *,
        size: int = BODY_SIZE,
        color: Optional[str] = None,
        weight: Any = None,
        **kwargs: Any,
    ) -> Any:
        ft = self.ft
        return ft.Text(
            value,
            size=size,
            color=color or self.palette.text,
            weight=weight or ft.FontWeight.NORMAL,
            **kwargs,
        )

    def _secondary(self, value: str, *, size: int = LABEL_SIZE, **kwargs: Any) -> Any:
        return self._text(value, size=size, color=self.palette.text_secondary, **kwargs)

    def _card(self, content: Any, *, padding: int = SPACING + 2, **kwargs: Any) -> Any:
        ft = self.ft
        return ft.Container(
            padding=padding,
            bgcolor=self.palette.surface,
            border_radius=CARD_RADIUS,
            border=ft.Border.all(1, self.palette.border),
            content=content,
            **kwargs,
        )

    def _metric(self, metric: "_Metric", value: Optional[float]) -> Any:
        """Render one weather reading with its icon and an accessible label.

        A missing reading keeps the muted colour and a dash. It is never given
        the appearance of a real value, which is what previously made an
        absent rainfall figure look like heavy rain.
        """
        ft = self.ft
        missing = value is None
        text = format_optional(value, metric.formatter)
        colour = self.palette.text_secondary if missing else self.palette.text
        described = f"{metric.label}: {text if not missing else 'not available'}"
        return ft.Row(
            spacing=4,
            tight=True,
            tooltip=described,
            controls=[
                ft.Icon(
                    getattr(ft.Icons, metric.icon),
                    size=16,
                    color=self.palette.text_secondary,
                    semantics_label=metric.label,
                ),
                self._text(text, size=LABEL_SIZE, color=colour, semantics_label=described),
            ],
        )

    # --- Header -----------------------------------------------------------

    def _build_header(self) -> Any:
        ft = self.ft
        self.refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            icon_color=ft.Colors.WHITE,
            icon_size=24,
            tooltip="Refresh forecast",
            on_click=self.on_refresh_click,
        )
        self.page.appbar = ft.AppBar(
            title=ft.Text(
                "Weather Helper",
                weight=ft.FontWeight.BOLD,
                size=TITLE_SIZE,
                color=ft.Colors.WHITE,
            ),
            center_title=False,
            bgcolor=self.palette.primary,
            color=ft.Colors.WHITE,
            actions=[self.refresh_button],
        )

    # --- Status -----------------------------------------------------------

    def _build_status(self) -> Any:
        ft = self.ft
        self.status = self._secondary("Loading forecasts…", size=BODY_SIZE)
        self.freshness = self._secondary("")
        self.progress = ft.ProgressBar(visible=False, color=self.palette.primary)
        self.status_row = ft.Column(
            spacing=4,
            controls=[self.status, self.freshness, self.progress],
        )
        return self.status_row

    # --- Filters ----------------------------------------------------------

    def _style_dropdown(self, dropdown: Any) -> Any:
        dropdown.border_radius = 10
        dropdown.content_padding = SPACING
        dropdown.border_color = self.palette.border
        dropdown.text_size = BODY_SIZE
        dropdown.color = self.palette.text
        dropdown.expand = True
        return dropdown

    def _build_filters(self) -> Any:
        ft = self.ft
        self.group_dropdown = self._style_dropdown(
            ft.Dropdown(
                label="Region",
                value=self.model.group_name,
                options=[
                    ft.DropdownOption(key=name, text=name) for name in LOCATION_GROUPS
                ],
                on_select=self.on_group_select,
            )
        )
        self.date_dropdown = self._style_dropdown(
            ft.Dropdown(label="Day", disabled=True, options=[], on_select=self.on_date_select)
        )
        self.profile_dropdown = self._style_dropdown(
            ft.Dropdown(
                label="Activity",
                value=self.model.activity_profile,
                options=[
                    ft.DropdownOption(key=key, text=label)
                    for key, label in ACTIVITY_PROFILE_LABELS.items()
                ],
                on_select=self.on_profile_select,
            )
        )
        return self._card(
            ft.ResponsiveRow(
                columns=12,
                spacing=8,
                run_spacing=8,
                controls=[
                    ft.Container(col={"xs": 12, "sm": 4}, content=self.group_dropdown),
                    ft.Container(col={"xs": 6, "sm": 4}, content=self.date_dropdown),
                    ft.Container(col={"xs": 6, "sm": 4}, content=self.profile_dropdown),
                ],
            ),
            padding=SPACING,
        )

    # --- The answer -------------------------------------------------------

    def _build_headline(self) -> Any:
        self.headline = self.ft.Column(spacing=6)
        self.headline_card = self._card(self.headline)
        return self.headline_card

    def render_headline(self) -> None:
        """Render the single best recommendation as the top of the screen."""
        ft = self.ft
        best = self.model.top_recommendation()
        activity = self.model.activity_label()
        day = self._selected_day_label()

        if best is None:
            self.headline.controls = [
                self._text(
                    f"No {activity.lower()} window worth recommending {day.lower()}",
                    size=SUBTITLE_SIZE,
                    weight=ft.FontWeight.BOLD,
                ),
                self._secondary(
                    "Nothing in this region scores well enough for this activity. "
                    "Try another day, activity or region.",
                    size=BODY_SIZE,
                ),
            ]
            self.headline_card.bgcolor = self.palette.surface
            return

        colour = self.palette.rating(best.rating)
        self.headline.controls = [
            self._secondary(f"Best for {activity.lower()} · {day}"),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACING,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            self._text(
                                best.location_name,
                                size=HEADLINE_SIZE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(
                                        ft.Icons.SCHEDULE,
                                        size=20,
                                        color=self.palette.text,
                                    ),
                                    self._text(
                                        best.best_window,
                                        size=SUBTITLE_SIZE,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    self._secondary(
                                        f"({best.window_length_label})"
                                        if best.window_length_label
                                        else ""
                                    ),
                                ],
                            ),
                        ],
                    ),
                    self._score_badge(best.normalized_score, best.rating, large=True),
                ],
            ),
            self._secondary(best.best_window_details, size=BODY_SIZE),
            ft.Container(
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
                bgcolor=self.palette.rating_background(best.rating),
                border_radius=8,
                content=self._text(
                    f"{best.rating} · {best.weather_description}",
                    size=LABEL_SIZE,
                    color=colour,
                    weight=ft.FontWeight.BOLD,
                ),
            ),
        ]

    def _score_badge(
        self, score: Optional[int], rating: str, *, large: bool = False
    ) -> Any:
        """Render a score as a number out of 100 with its rating word."""
        ft = self.ft
        colour = self.palette.rating(rating)
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.END,
            spacing=0,
            tight=True,
            controls=[
                ft.Row(
                    spacing=1,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[
                        self._text(
                            MISSING_VALUE if score is None else str(score),
                            size=HEADLINE_SIZE if large else SUBTITLE_SIZE + 3,
                            weight=ft.FontWeight.BOLD,
                            color=colour,
                        ),
                        self._secondary("/100", size=LABEL_SIZE - 1),
                    ],
                ),
                self._text(rating, size=LABEL_SIZE, color=colour),
            ],
        )

    # --- Pinned locations -------------------------------------------------

    def _build_pinned(self) -> Any:
        self.pinned = self.ft.Column(spacing=8)
        self.pinned_card = self._card(self.pinned)
        return self.pinned_card

    def render_pinned(self) -> None:
        """Render the pinned locations for the current region, if any."""
        ft = self.ft
        rows = self.model.daily_summary_rows()
        names = self.model.priority_location_names()
        if not rows:
            self.pinned_card.visible = False
            return

        self.pinned_card.visible = True
        heading = (
            f"{' and '.join(names)} · {self.model.activity_label().lower()}"
            if names
            else f"Best alternatives for {self.model.activity_label().lower()}"
        )
        controls: list[Any] = [
            ft.Row(
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.PUSH_PIN_OUTLINED, size=18, color=self.palette.primary),
                    self._text(heading, size=SUBTITLE_SIZE, weight=ft.FontWeight.BOLD),
                ],
            )
        ]
        alternatives_started = False
        for row in rows:
            if not row.is_priority and not alternatives_started and names:
                controls.append(
                    self._secondary("Better elsewhere today", size=LABEL_SIZE)
                )
                alternatives_started = True
            controls.append(self._pinned_row(row))
        self.pinned.controls = controls

    def _pinned_row(self, row: Any) -> Any:
        ft = self.ft
        unavailable = row.normalized_score is None
        return ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Container(
                    expand=True,
                    content=self._text(row.location_name, size=BODY_SIZE),
                ),
                self._text(
                    row.best_window,
                    size=BODY_SIZE,
                    color=(
                        self.palette.text_secondary if unavailable else self.palette.text
                    ),
                ),
                ft.Container(
                    width=52,
                    alignment=ft.Alignment.CENTER_RIGHT,
                    content=self._text(
                        MISSING_VALUE if unavailable else str(row.normalized_score),
                        size=BODY_SIZE,
                        weight=ft.FontWeight.BOLD,
                        color=self.palette.text_secondary
                        if unavailable
                        else self.palette.primary,
                    ),
                ),
            ],
        )

    # --- Ranked list ------------------------------------------------------

    def _build_ranking(self) -> Any:
        ft = self.ft
        self.forecast_list = ft.Column(spacing=10)
        return ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Icon(
                            ft.Icons.LEADERBOARD,
                            size=18,
                            color=self.palette.primary,
                        ),
                        self._text(
                            "All locations, ranked",
                            size=SUBTITLE_SIZE,
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                self._secondary(
                    "Tap a location to see the hours behind its score."
                ),
                self.forecast_list,
            ],
        )

    def render_forecast_list(self) -> None:
        ranked = self.model.ranked_locations(RANKED_LOCATION_COUNT)
        selected = self.model.selected_location()
        ranked_keys = {card.location_key for card in ranked}

        tiles = [
            self._location_tile(card, rank=index)
            for index, card in enumerate(ranked, 1)
        ]
        if selected is not None and selected.location_key not in ranked_keys:
            # An explicitly chosen location stays reachable, but below the
            # ranking rather than pretending to lead it.
            tiles.append(self._location_tile(selected, rank=None))

        self.forecast_list.controls = tiles or [
            self._secondary(
                "No location has usable forecast data for this day.",
                size=BODY_SIZE,
            )
        ]

    def _location_tile(self, card: RankedLocationView, *, rank: Optional[int]) -> Any:
        ft = self.ft
        colour = self.palette.rating(card.rating)
        is_expanded = card.location_key in self._expanded_keys

        def on_change(event: Any) -> None:
            self.on_tile_toggle(card.location_key, bool(event.data))

        tile = ft.ExpansionTile(
            title=self._text(
                card.location_name, size=SUBTITLE_SIZE, weight=ft.FontWeight.BOLD
            ),
            subtitle=self._secondary(
                card.best_window if card.is_ranked else "No window to recommend",
                size=BODY_SIZE,
            ),
            leading=self._rank_marker(rank, colour),
            trailing=self._score_badge(card.normalized_score, card.rating),
            expanded=is_expanded,
            maintain_state=False,
            tile_padding=ft.Padding(left=SPACING, top=8, right=SPACING, bottom=8),
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.TRANSPARENT,
            icon_color=colour,
            collapsed_icon_color=self.palette.text_secondary,
            on_change=on_change,
            # Bodies are built only for the card the user opened; building all
            # ten with their hourly rows made every filter change stutter.
            controls=self._expanded_body(card) if is_expanded else [],
        )
        return ft.Container(
            key=ft.ScrollKey(f"card_{card.location_key}"),
            bgcolor=self.palette.surface,
            border=ft.Border.all(
                2 if is_expanded else 1,
                colour if is_expanded else self.palette.border,
            ),
            border_radius=CARD_RADIUS,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=tile,
        )

    def _rank_marker(self, rank: Optional[int], colour: str) -> Any:
        ft = self.ft
        if rank is None:
            return ft.Icon(
                ft.Icons.PLACE_OUTLINED, color=self.palette.text_secondary, size=22
            )
        return ft.Container(
            width=30,
            height=30,
            alignment=ft.Alignment.CENTER,
            bgcolor=self.palette.rating_background(
                _rating_for_rank_marker(rank)
            ),
            border=ft.Border.all(1, colour),
            border_radius=15,
            content=self._text(
                str(rank), size=LABEL_SIZE, weight=ft.FontWeight.BOLD, color=colour
            ),
        )

    def _expanded_body(self, card: RankedLocationView) -> list[Any]:
        ft = self.ft
        rows = self.model.hourly_forecast(card.location_key)
        if rows:
            hours_note = (
                f"Hours considered ({DAYLIGHT_START_HOUR:02d}:00–"
                f"{DAYLIGHT_END_HOUR:02d}:00, upcoming only)"
            )
            body: list[Any] = [self._secondary(hours_note)]
            body.extend(self._hourly_row(row) for row in rows)
        else:
            body = [
                self._secondary(
                    "No upcoming daylight hours left for this day.", size=BODY_SIZE
                )
            ]

        return [
            ft.Container(
                padding=ft.Padding(left=SPACING, top=0, right=SPACING, bottom=SPACING),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Divider(height=1, color=self.palette.border),
                        self._secondary(card.best_window_details, size=BODY_SIZE),
                        ft.Container(height=2),
                        *body,
                    ],
                ),
            )
        ]

    def _hourly_row(self, row: HourlyForecastView) -> Any:
        """Render one forecast entry, marking the recommended window."""
        ft = self.ft
        colour = self.palette.rating(row.rating)
        highlighted = row.in_best_window
        time_line: list[Any] = [
            self._text(
                row.time,
                size=SUBTITLE_SIZE,
                weight=ft.FontWeight.BOLD,
            )
        ]
        if not row.is_hourly:
            time_line.append(self._secondary(row.span_label))
        if highlighted:
            time_line.append(
                ft.Container(
                    padding=ft.Padding(left=6, top=1, right=6, bottom=1),
                    bgcolor=colour,
                    border_radius=6,
                    content=ft.Text(
                        "BEST",
                        size=LABEL_SIZE - 3,
                        weight=ft.FontWeight.BOLD,
                        color=self.palette.surface,
                    ),
                )
            )

        return ft.Container(
            padding=ft.Padding(left=0, top=8, right=10, bottom=8),
            bgcolor=(
                self.palette.rating_background(row.rating)
                if highlighted
                else self.palette.background
            ),
            border_radius=10,
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                controls=[
                    ft.Container(width=5, height=64, bgcolor=colour),
                    ft.Container(width=10),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Row(spacing=6, controls=time_line),
                            ft.Row(
                                spacing=10,
                                wrap=True,
                                controls=[
                                    self._metric(TEMPERATURE, row.temperature),
                                    self._metric(WIND, row.wind),
                                    self._metric(CLOUDS, row.clouds),
                                    self._metric(RAIN, row.precipitation),
                                    self._metric(HUMIDITY, row.humidity),
                                ],
                            ),
                        ],
                    ),
                    self._score_badge(row.normalized_score, row.rating),
                ],
            ),
        )

    # --- Legend and footer ------------------------------------------------

    def _build_legend(self) -> Any:
        ft = self.ft
        chips = [
            ft.Container(
                padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                bgcolor=self.palette.rating_background(rating),
                border_radius=6,
                content=self._text(
                    rating,
                    size=LABEL_SIZE,
                    color=self.palette.rating(rating),
                    weight=ft.FontWeight.BOLD,
                ),
            )
            for rating in RATING_ORDER
        ]
        return self._card(
            ft.Column(
                spacing=6,
                controls=[
                    self._secondary(
                        "Scores run 0-100 for the selected activity: higher is better."
                    ),
                    ft.Row(spacing=6, wrap=True, run_spacing=6, controls=chips),
                ],
            ),
            padding=SPACING,
        )

    def _build_footer(self) -> Any:
        return self.ft.Markdown(
            f"Data from [MET Norway]({MET_NORWAY_SOURCE_URL}), "
            f"processed by Weather Helper · "
            f"[license]({MET_NORWAY_LICENSE_URL})",
            selectable=True,
        )

    # --- Rendering --------------------------------------------------------

    def render_dashboard(self) -> None:
        """Redraw every part of the screen from the current model state."""
        self._update_date_options()
        self.render_headline()
        self.render_pinned()
        self.render_forecast_list()
        self.freshness.value = self.model.freshness_label()
        self.page.update()

    def _selected_day_label(self) -> str:
        if self.model.selected_date is None:
            return "today"
        return format_relative_date(self.model.selected_date, get_current_date())

    def _update_date_options(self) -> None:
        ft = self.ft
        today = get_current_date()
        available_dates = self.model.available_dates()
        self.date_dropdown.options = [
            ft.DropdownOption(
                key=value.isoformat(), text=format_relative_date(value, today)
            )
            for value in available_dates
        ]
        self.date_dropdown.disabled = not available_dates
        self.date_dropdown.value = (
            self.model.selected_date.isoformat() if self.model.selected_date else None
        )

    # --- Events -----------------------------------------------------------

    def _guard(self, action: Callable[[], None]) -> None:
        """Run a handler, turning an unexpected failure into a visible message.

        An exception inside a Flet event handler is otherwise silent, which
        would leave the screen looking as though the tap did nothing.
        """
        try:
            action()
        except Exception:
            self.status.value = "That selection is no longer available. Refreshing…"
            self.page.update()
            self.page.run_task(self.refresh_forecast)

    def on_tile_toggle(self, location_key: str, expanded: bool) -> None:
        def apply() -> None:
            if expanded:
                self._expanded_keys = {location_key}
                self.model.select_location(location_key)
            else:
                self._expanded_keys.discard(location_key)
            self.render_forecast_list()
            self.page.update()
            if expanded:
                self.page.run_task(self._scroll_to_card, location_key)

        self._guard(apply)

    async def _scroll_to_card(self, location_key: str) -> None:
        """Bring a newly opened card into view inside the scrolling list."""
        await self.list_view.scroll_to(
            scroll_key=self.ft.ScrollKey(f"card_{location_key}"), duration=300
        )

    def on_group_select(self, event: Any) -> None:
        def apply() -> None:
            self.model.select_group(event.control.value)
            self.forecast_list.controls = []
            self._expanded_keys.clear()
            self.page.update()
            self.page.run_task(self.refresh_forecast)

        self._guard(apply)

    def on_profile_select(self, event: Any) -> None:
        def apply() -> None:
            self.model.select_activity_profile(event.control.value)
            self.render_dashboard()

        self._guard(apply)

    def on_date_select(self, event: Any) -> None:
        def apply() -> None:
            self.model.select_date(date.fromisoformat(event.control.value))
            self._expanded_keys.clear()
            self.render_dashboard()

        self._guard(apply)

    def on_refresh_click(self, event: Any) -> None:
        self.page.run_task(self.refresh_forecast)

    def on_brightness_change(self, event: Any) -> None:
        """Follow the device between light and dark mode."""
        self.palette = Palette(dark=self._prefers_dark())
        self.build(initial_load=False)
        self.render_dashboard()

    def on_lifecycle_change(self, event: Any) -> None:
        """Refresh stale data when the app comes back to the foreground."""
        if event.data == self.ft.AppLifecycleState.RESUME and self.model.is_stale():
            self.page.run_task(self.refresh_forecast)

    # --- Loading ----------------------------------------------------------

    async def refresh_forecast(self, event: Any = None) -> None:
        """Reload the selected region, ignoring results from a superseded load."""
        self._load_generation += 1
        generation = self._load_generation
        self._set_loading(True)
        self.status.value = f"Loading {self.model.group_name}…"
        self.page.update()

        def report_progress(current: int, total: int, location: Any) -> None:
            if generation == self._load_generation:
                self.status.value = f"Loading {self.model.group_name}… {current}/{total}"

        try:
            self.model.invalidate_rankings()
            batch = await asyncio.to_thread(self.model.load, report_progress)
        except Exception:
            if generation == self._load_generation:
                self.status.value = (
                    "Could not load forecasts. Check your connection and try again."
                )
                self._set_loading(False)
                self.page.update()
            return

        if generation != self._load_generation:
            return  # A newer load is already in flight; its result wins.

        self.status.value = _load_summary(batch, self.model.group_name)
        self._set_loading(False)
        self.render_dashboard()

    def _set_loading(self, loading: bool) -> None:
        self.progress.visible = loading
        self.refresh_button.disabled = loading
        self.group_dropdown.disabled = loading

    # --- Assembly ---------------------------------------------------------

    def build(self, initial_load: bool = True) -> None:
        ft = self.ft
        self._apply_theme()
        self.page.title = "Weather Helper"
        self.page.padding = 0
        self._build_header()

        self.list_view = ft.ListView(
            expand=True,
            spacing=SPACING,
            padding=SPACING,
            controls=[
                self._build_status(),
                self._build_filters(),
                self._build_headline(),
                self._build_pinned(),
                self._build_ranking(),
                self._build_legend(),
                self._build_footer(),
            ],
        )
        self.page.controls = []
        self.page.add(ft.SafeArea(expand=True, content=self.list_view))
        self.page.on_platform_brightness_change = self.on_brightness_change
        self.page.on_app_lifecycle_state_change = self.on_lifecycle_change

        if initial_load:
            self.page.run_task(self.refresh_forecast)


def _rating_for_rank_marker(rank: int) -> str:
    """Return a rating whose tint suits a rank position."""
    if rank == 1:
        return "Excellent"
    if rank <= 3:
        return "Very Good"
    return "Good"


def _load_summary(batch: Any, group_name: str) -> str:
    """Describe the outcome of a load, naming anything that failed."""
    if not batch.loaded_count:
        return f"No {group_name} forecasts could be loaded. Check your connection."
    summary = f"{batch.loaded_count} locations loaded"
    if batch.failure_summary:
        summary += f" · unavailable: {batch.failure_summary}"
    return summary


def main() -> None:
    """Run Weather Helper with Flet's desktop/mobile development host."""
    ft = _load_flet()
    ft.run(create_mobile_app)


if __name__ == "__main__":
    main()
