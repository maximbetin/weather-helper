"""Pure presentation state for the Flet Weather Helper screen."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.application.forecast_service import ForecastBatch, ForecastService
from src.application.presentation import (
    format_percentage,
    format_precipitation,
    format_temperature,
    format_wind_speed,
)
from src.core.evaluation import (
    get_available_dates,
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

DEFAULT_LOCATION_GROUP = "Asturias"


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

    @property
    def is_ranked(self) -> bool:
        """Return True when the location has a qualifying recommendation."""
        return self.rank is not None


@dataclass(frozen=True)
class HourlyForecastView:
    """Mobile-friendly summary of one hourly forecast row."""

    time: str
    temperature: str
    wind: str
    clouds: str
    precipitation: str
    rain_risk: str
    humidity: str
    normalized_score: int
    rating: str


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

    def load(self) -> ForecastBatch:
        """Load the selected group while preserving valid user selections."""
        previous_date = self.selected_date
        previous_location_key = self.selected_location_key
        batch = self.service.load_locations(self.locations)
        self.forecasts = batch.forecasts
        self.errors = batch.errors
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
                item
                for item in self.ranked_locations(len(self.forecasts))
                if item.location_key == self.selected_location_key
            ),
            None,
        )
        if ranked:
            return ranked
        if self.selected_location_key not in self.available_location_keys():
            return None
        return self._unranked_location_view(self.selected_location_key)

    def ranked_locations(self, top_n: int = 10) -> list[RankedLocationView]:
        if self.selected_date is None:
            return []
        ranked = get_top_locations_for_date(
            self.forecasts,
            self.selected_date,
            top_n=top_n,
            activity_profile=self.activity_profile,
        )
        return [
            self._ranked_location_view(index, item)
            for index, item in enumerate(ranked, 1)
        ]

    def hourly_forecast(self, location_key: str) -> list[HourlyForecastView]:
        if self.selected_date is None or location_key not in self.forecasts:
            return []
        hours = get_time_blocks_for_date(self.forecasts[location_key], self.selected_date)
        return [self._hourly_forecast_view(hour) for hour in hours]

    def _select_default_location(self) -> None:
        ranked = self.ranked_locations(1)
        if ranked:
            self.selected_location_key = ranked[0].location_key
            return
        available = self.available_location_keys()
        self.selected_location_key = available[0] if available else ""

    def _clear_forecasts(self) -> None:
        self.forecasts = {}
        self.errors = {}
        self.selected_date = None
        self.selected_location_key = ""

    def _ranked_location_view(self, rank: int, item: dict) -> RankedLocationView:
        raw_score = float(item["raw_score"])
        block = item["optimal_block"]
        end_time = block["end"] + timedelta(hours=1)
        best_window = f"{block['start']:%H:%M}–{end_time:%H:%M}"
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
                "No qualifying recommended window for this activity. "
                "Review the hourly conditions below."
            ),
        )

    def _hourly_forecast_view(self, hour) -> HourlyForecastView:
        raw_score = get_activity_score(hour, self.activity_profile)
        normalized = normalize_score(raw_score, self.activity_profile)
        return HourlyForecastView(
            time=f"{hour.time:%H:%M}",
            temperature=format_temperature(hour.temp),
            wind=format_wind_speed(hour.wind),
            clouds=format_percentage(hour.cloud_coverage),
            precipitation=format_precipitation(hour.precipitation_amount),
            rain_risk=format_percentage(hour.precipitation_probability),
            humidity=format_percentage(hour.relative_humidity),
            normalized_score=normalized,
            rating=get_rating_info(raw_score, self.activity_profile),
        )


def _format_best_window_details(block: dict) -> str:
    return (
        f"Temp: {format_temperature(block.get('temp'))} · "
        f"Wind: {format_wind_speed(block.get('wind'))} · "
        f"Clouds: {format_percentage(block.get('cloud'))} · "
        f"Rain: {format_precipitation(block.get('precip'))} · "
        f"Rain Risk: {format_percentage(block.get('precip_probability'))}"
    )
