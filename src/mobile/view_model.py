"""Pure presentation state for the Flet Weather Helper screen."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from src.application.forecast_service import ForecastBatch, ForecastService
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
    """Mobile-friendly summary of one ranked location."""

    rank: int
    location_key: str
    location_name: str
    normalized_score: int
    raw_score: float
    rating: str
    weather_description: str
    best_window: str
    best_window_details: str


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

    def load(self) -> ForecastBatch:
        """Load the selected group and choose its earliest available date."""
        batch = self.service.load_locations(self.locations)
        self.forecasts = batch.forecasts
        self.errors = batch.errors
        available_dates = self.available_dates()
        self.selected_date = available_dates[0] if available_dates else None
        self.selected_location_key = ""
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
        self.selected_location_key = ""

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
        self.selected_location_key = location_key
        hours = get_time_blocks_for_date(self.forecasts[location_key], self.selected_date)
        return [self._hourly_forecast_view(hour) for hour in hours]

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

    def _hourly_forecast_view(self, hour) -> HourlyForecastView:
        raw_score = get_activity_score(hour, self.activity_profile)
        normalized = normalize_score(raw_score, self.activity_profile)
        return HourlyForecastView(
            time=f"{hour.time:%H:%M}",
            temperature=_format_number(hour.temp, "°C"),
            wind=_format_number(hour.wind, " m/s"),
            clouds=_format_percentage(hour.cloud_coverage),
            precipitation=_format_precipitation(hour.precipitation_amount),
            rain_risk=_format_percentage(hour.precipitation_probability),
            humidity=_format_percentage(hour.relative_humidity),
            normalized_score=normalized,
            rating=get_rating_info(raw_score, self.activity_profile),
        )


def _format_number(value, suffix: str) -> str:
    return "N/A" if value is None else f"{value:.1f}{suffix}"


def _format_percentage(value) -> str:
    return "N/A" if value is None else f"{value:.0f}%"


def _format_precipitation(value) -> str:
    amount = 0 if value is None else value
    return f"{amount:.1f} mm"


def _format_best_window_details(block: dict) -> str:
    return (
        f"Temp: {_format_number(block.get('temp'), '°C')} · "
        f"Wind: {_format_number(block.get('wind'), ' m/s')} · "
        f"Clouds: {_format_percentage(block.get('cloud'))} · "
        f"Rain: {_format_precipitation(block.get('precip'))} · "
        f"Rain Risk: {_format_percentage(block.get('precip_probability'))}"
    )
