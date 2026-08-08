"""Pure presentation state for the Flet Weather Helper screen."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from src.application.forecast_service import (
    ForecastBatch,
    ForecastService,
    ProgressCallback,
)
from src.application.presentation import (
    format_percentage,
    format_precipitation,
    format_temperature,
    format_wind_speed,
)
from src.core.evaluation import (
    daylight_bounds,
    get_available_dates,
    get_recommendation_hours,
    get_time_blocks_for_date,
    get_top_locations_for_date,
)
from src.core.locations import LOCATION_GROUPS
from src.core.scoring import (
    ACTIVITY_PROFILE_LABELS,
    DEFAULT_ACTIVITY_PROFILE,
    get_activity_score,
    get_rating_info,
    normalize_score,
)
from src.mobile.daily_summary import (
    DailySummaryRow,
    build_daily_summary,
    format_daily_summary,
    resolve_priority_keys,
)

DEFAULT_LOCATION_GROUP = "Asturias"

# Forecasts older than this are flagged, so a screen opened the next morning
# never presents yesterday's plan as if it were current.
STALE_AFTER = timedelta(hours=1)


@dataclass(frozen=True)
class RankedLocationView:
    """Mobile-friendly selected-location or ranking summary."""

    rank: Optional[int]
    location_key: str
    location_name: str
    normalized_score: Optional[int]
    raw_score: Optional[float]
    rating: str
    weather_description: str
    best_window: str
    best_window_details: str
    window_hours: int = 0
    window_score: Optional[int] = None
    window_rating: str = "N/A"

    @property
    def is_ranked(self) -> bool:
        """Return True when the location has a qualifying recommendation."""
        return self.rank is not None

    @property
    def window_length_label(self) -> str:
        """Return how long the recommended window lasts."""
        if not self.window_hours:
            return ""
        return "1 hour" if self.window_hours == 1 else f"{self.window_hours} hours"


@dataclass(frozen=True)
class HourlyForecastView:
    """Mobile-friendly summary of one forecast entry."""

    time: str
    temperature: Optional[float]
    wind: Optional[float]
    clouds: Optional[float]
    precipitation: Optional[float]
    humidity: Optional[float]
    normalized_score: int
    rating: str
    coverage_hours: int
    in_best_window: bool

    @property
    def is_hourly(self) -> bool:
        """Return True when this row describes a single hour."""
        return self.coverage_hours == 1

    @property
    def span_label(self) -> str:
        """Return a label stating the period a row covers."""
        return "" if self.is_hourly else f"{self.coverage_hours}h block"


class MobileWeatherViewModel:
    """Selection and display state with no dependency on Flet or Tkinter."""

    def __init__(self, service: Optional[ForecastService] = None) -> None:
        self.service = service or ForecastService()
        self.group_name = DEFAULT_LOCATION_GROUP
        self.activity_profile = DEFAULT_ACTIVITY_PROFILE
        self.selected_date: Optional[date] = None
        self.selected_location_key = ""
        self.forecasts: dict[str, dict] = {}
        self.errors: dict[str, str] = {}
        self.loaded_at: Optional[datetime] = None
        self._ranking_cache: dict[tuple, list[dict]] = {}

    @property
    def locations(self):
        return LOCATION_GROUPS[self.group_name]

    def select_group(self, group_name: str) -> None:
        if group_name not in LOCATION_GROUPS:
            raise ValueError(f"Unknown location group: {group_name}")
        if group_name == self.group_name:
            return
        self.group_name = group_name
        self._clear_forecasts()

    def select_activity_profile(self, profile_key: str) -> None:
        if profile_key not in ACTIVITY_PROFILE_LABELS:
            raise ValueError(f"Unknown activity profile: {profile_key}")
        self.activity_profile = profile_key
        if self.selected_location_key not in self.available_location_keys():
            self._select_default_location()

    def _ranked_results(self, top_n: int) -> list[dict]:
        """Return ranked results for the current selection, computed once.

        Ranking scans every location's forecast, and a single screen refresh
        asks for it several times. Caching per selection keeps changing a
        filter responsive on a phone.
        """
        if self.selected_date is None:
            return []
        cache_key = (self.selected_date, self.activity_profile, top_n)
        if cache_key not in self._ranking_cache:
            self._ranking_cache[cache_key] = get_top_locations_for_date(
                self.forecasts,
                self.selected_date,
                top_n=top_n,
                activity_profile=self.activity_profile,
            )
        return self._ranking_cache[cache_key]

    def invalidate_rankings(self) -> None:
        """Drop cached rankings so time-sensitive results are recomputed."""
        self._ranking_cache.clear()

    def load(self, on_progress: Optional[ProgressCallback] = None) -> ForecastBatch:
        """Load the selected group while preserving valid user selections."""
        previous_date = self.selected_date
        previous_location_key = self.selected_location_key
        batch = self.service.load_locations(self.locations, on_progress)
        self.forecasts = batch.forecasts
        self.errors = batch.errors
        self.loaded_at = datetime.now()
        self.invalidate_rankings()
        available_dates = self.available_dates()
        self.selected_date = (
            previous_date if previous_date in available_dates
            else available_dates[0] if available_dates else None
        )
        if previous_location_key in self.available_location_keys():
            self.selected_location_key = previous_location_key
        else:
            self._select_default_location()
        return batch

    def available_dates(self) -> list[date]:
        dates = {
            forecast_date
            for processed in self.forecasts.values()
            for forecast_date in get_available_dates(processed)
        }
        return sorted(dates)

    def select_date(self, value: date) -> None:
        if value not in self.available_dates():
            raise ValueError(f"Date is not available: {value.isoformat()}")
        self.selected_date = value
        if self.selected_location_key not in self.available_location_keys():
            self._select_default_location()

    def available_location_keys(self) -> list[str]:
        """Return loaded locations with hourly data for the selected date."""
        if self.selected_date is None:
            return []
        return [
            key
            for key, forecast in self.forecasts.items()
            if key in self.locations
            and get_time_blocks_for_date(forecast, self.selected_date)
        ]

    def location_options(self) -> list[tuple[str, str]]:
        """Return selectable locations sorted by their display name."""
        options = [
            (key, self.locations[key].name)
            for key in self.available_location_keys()
            if key in self.locations
        ]
        return sorted(options, key=lambda item: item[1].casefold())

    def select_location(self, location_key: str) -> None:
        """Select any loaded location, including one outside the Top 10."""
        if location_key not in self.available_location_keys():
            raise ValueError(f"Location is not available: {location_key}")
        self.selected_location_key = location_key

    def selected_location(self) -> Optional[RankedLocationView]:
        """Return a summary even when the selected location is unranked."""
        if not self.selected_location_key:
            return None
        ranked = next(
            (
                self._ranked_location_view(index, item)
                for index, item in enumerate(
                    self._ranked_results(max(1, len(self.forecasts))), 1
                )
                if item["location_key"] == self.selected_location_key
            ),
            None,
        )
        if ranked:
            return ranked
        if self.selected_location_key not in self.available_location_keys():
            return None
        return self._unranked_location_view(self.selected_location_key)

    def ranked_locations(self, top_n: int = 10) -> list[RankedLocationView]:
        return [
            self._ranked_location_view(index, item)
            for index, item in enumerate(self._ranked_results(top_n), 1)
        ]

    def hourly_forecast(self, location_key: str) -> list[HourlyForecastView]:
        """Return the entries the recommendation for this location is based on.

        These are exactly the hours the ranking considered, so the breakdown
        can never show a glowing 03:00 that the recommendation ignored, nor
        hours that have already passed.
        """
        if self.selected_date is None or location_key not in self.forecasts:
            return []
        hours = get_recommendation_hours(
            self.forecasts[location_key], self.selected_date
        )
        window = self._best_window_bounds(location_key)
        return [self._hourly_forecast_view(hour, window) for hour in hours]

    def selected_hourly_forecast(self) -> list[HourlyForecastView]:
        """Return the breakdown for the currently selected location."""
        if not self.selected_location_key:
            return []
        return self.hourly_forecast(self.selected_location_key)

    def _best_window_bounds(
        self, location_key: str
    ) -> Optional[tuple[datetime, datetime]]:
        """Return the start and end of the recommended window, if any."""
        ranked = next(
            (
                item
                for item in self._ranked_results(len(self.forecasts))
                if item["location_key"] == location_key
            ),
            None,
        )
        if ranked is None:
            return None
        block = ranked["optimal_block"]
        return block["start"], block["end_time"]

    def _select_default_location(self) -> None:
        ranked = self._ranked_results(1)
        if ranked:
            self.selected_location_key = ranked[0]["location_key"]
            return
        available = self.available_location_keys()
        self.selected_location_key = available[0] if available else ""

    def daily_summary_rows(self) -> list[DailySummaryRow]:
        """Return the pinned locations and best alternatives for the activity.

        The summary follows the selected activity, so it can never recommend a
        beach window while the rest of the screen is ranked for hiking.
        """
        if self.selected_date is None:
            return []
        return build_daily_summary(
            self.forecasts,
            self.selected_date,
            self.locations,
            activity_profiles=(self.activity_profile,),
        )

    def top_recommendation(self) -> Optional[RankedLocationView]:
        """Return the single best place to be, which is the app's whole point."""
        ranked = self.ranked_locations(1)
        return ranked[0] if ranked else None

    def is_stale(self, max_age: timedelta = STALE_AFTER) -> bool:
        """Return True when the loaded data is too old to trust for today."""
        if self.loaded_at is None:
            return True
        if datetime.now().date() != self.loaded_at.date():
            return True
        return datetime.now() - self.loaded_at > max_age

    def freshness_label(self) -> str:
        """Return a short description of how current the data is."""
        if self.loaded_at is None:
            return "Not loaded yet"
        if self.is_stale():
            return f"Updated {self.loaded_at:%H:%M} · may be out of date"
        return f"Updated {self.loaded_at:%H:%M}"

    def activity_label(self) -> str:
        """Return the display label for the selected activity."""
        return ACTIVITY_PROFILE_LABELS.get(
            self.activity_profile, self.activity_profile
        )

    def priority_location_names(self) -> list[str]:
        """Return the names of the locations pinned in the current region."""
        return [
            self.locations[key].name
            for key in resolve_priority_keys(self.locations, self.forecasts)
        ]

    def daily_summary_text(self) -> str:
        """Return the aligned summary text used by a notification or preview."""
        return format_daily_summary(
            self.daily_summary_rows(),
            forecast_date=self.selected_date,
        )

    def _clear_forecasts(self) -> None:
        self.forecasts = {}
        self.errors = {}
        self.selected_date = None
        self.selected_location_key = ""
        self.loaded_at = None
        self.invalidate_rankings()

    def _ranked_location_view(self, rank: int, item: dict) -> RankedLocationView:
        raw_score = float(item["raw_score"])
        block = item["optimal_block"]
        best_window = format_window(block["start"], block["end_time"])
        return RankedLocationView(
            rank=rank,
            location_key=item["location_key"],
            location_name=item["location_name"],
            normalized_score=normalize_score(raw_score, self.activity_profile),
            raw_score=raw_score,
            rating=get_rating_info(raw_score, self.activity_profile),
            weather_description=item["weather_desc"],
            best_window=best_window,
            best_window_details=_format_best_window_details(block),
            window_hours=block.get("duration_hours", block.get("duration", 0)),
            window_score=normalize_score(
                item["window_score"], self.activity_profile
            ),
            window_rating=get_rating_info(
                item["window_score"], self.activity_profile
            ),
        )

    def _unranked_location_view(self, location_key: str) -> RankedLocationView:
        """Build a useful summary for data that has no qualifying block."""
        processed = self.forecasts[location_key]
        report = processed.get("day_scores", {}).get(self.selected_date)
        description = (
            report.weather_description if report is not None
            else "Hourly forecast available"
        )
        return RankedLocationView(
            rank=None,
            location_key=location_key,
            location_name=self.locations[location_key].name,
            normalized_score=None,
            raw_score=None,
            rating="N/A",
            weather_description=description,
            best_window="",
            best_window_details=(
                "No window here is good enough to recommend for this activity. "
                "The hours below are what was considered."
            ),
            window_hours=0,
        )

    def _hourly_forecast_view(
        self, hour, window: Optional[tuple[datetime, datetime]]
    ) -> HourlyForecastView:
        raw_score = get_activity_score(hour, self.activity_profile)
        visible_start, visible_end = daylight_bounds(hour)
        return HourlyForecastView(
            time=f"{hour.time:%H:%M}"
            if hour.is_hourly
            else format_window(visible_start, visible_end),
            temperature=hour.temp,
            wind=hour.wind,
            clouds=hour.cloud_coverage,
            precipitation=hour.precipitation_amount,
            humidity=hour.relative_humidity,
            normalized_score=normalize_score(raw_score, self.activity_profile),
            rating=get_rating_info(raw_score, self.activity_profile),
            coverage_hours=int(
                round((visible_end - visible_start).total_seconds() / 3600)
            )
            or 1,
            in_best_window=_is_inside_window(hour, window),
        )


def format_window(start: datetime, end: datetime) -> str:
    """Format a recommended window as a start and end time."""
    return f"{start:%H:%M} - {end:%H:%M}"


def _is_inside_window(hour, window: Optional[tuple[datetime, datetime]]) -> bool:
    """Return True when an entry overlaps the recommended window.

    The comparison uses the daylight part of the entry, so the first entry of a
    window that began before dawn is still marked as part of it.
    """
    if window is None:
        return False
    window_start, window_end = window
    entry_start, entry_end = daylight_bounds(hour)
    return entry_start < window_end and entry_end > window_start


def _format_best_window_details(block: dict) -> str:
    return (
        f"Temp: {format_temperature(block.get('temp'))} · "
        f"Wind: {format_wind_speed(block.get('wind'))} · "
        f"Clouds: {format_percentage(block.get('cloud'))} · "
        f"Rain: {format_precipitation(block.get('precip'))}"
    )
