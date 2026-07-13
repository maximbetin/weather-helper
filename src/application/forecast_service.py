"""UI-independent orchestration for fetching and processing forecasts."""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from src.core.evaluation import process_forecast
from src.core.locations import Location
from src.core.weather_api import fetch_weather_data

ProcessedForecast = dict[str, Any]
FetchForecast = Callable[[Location], Optional[dict[str, Any]]]
ProcessForecast = Callable[[dict[str, Any], str], Optional[ProcessedForecast]]
ProgressCallback = Callable[[int, int, Location], None]

logger = logging.getLogger(__name__)

DOWNLOAD_ERROR = "Could not download forecast data. Check your connection and try again."
PROCESSING_ERROR = "The forecast response did not contain usable weather data."
UNEXPECTED_ERROR = "Could not load this forecast. Please try again."


@dataclass(frozen=True)
class LocationForecastResult:
    """Outcome of loading one location without exposing UI concerns."""

    location: Location
    forecast: Optional[ProcessedForecast] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.forecast is not None


@dataclass(frozen=True)
class ForecastBatch:
    """Processed forecasts and per-location failures for a location group."""

    forecasts: dict[str, ProcessedForecast] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def loaded_count(self) -> int:
        return len(self.forecasts)


class ForecastService:
    """Fetch forecasts and pass them through the existing core evaluator."""

    def __init__(
        self,
        fetch_forecast: Optional[FetchForecast] = None,
        process: Optional[ProcessForecast] = None,
    ) -> None:
        self._fetch_forecast = fetch_forecast or fetch_weather_data
        self._process_forecast = process or process_forecast

    def load_location(self, location: Location) -> LocationForecastResult:
        """Load and process a single location, converting failures to data."""
        try:
            raw_forecast = self._fetch_forecast(location)
            if raw_forecast is None:
                return LocationForecastResult(
                    location=location,
                    error=DOWNLOAD_ERROR,
                )

            processed = self._process_forecast(raw_forecast, location.name)
            if processed is None:
                return LocationForecastResult(
                    location=location,
                    error=PROCESSING_ERROR,
                )
            return LocationForecastResult(location=location, forecast=processed)
        except Exception:
            logger.exception("Unexpected forecast loading error for %s", location.name)
            return LocationForecastResult(location=location, error=UNEXPECTED_ERROR)

    def load_locations(
        self,
        locations: Mapping[str, Location],
        on_progress: Optional[ProgressCallback] = None,
    ) -> ForecastBatch:
        """Load a location group, retaining successful partial results."""
        forecasts: dict[str, ProcessedForecast] = {}
        errors: dict[str, str] = {}
        total = len(locations)

        for index, (location_key, location) in enumerate(locations.items(), start=1):
            result = self.load_location(location)
            if result.forecast is not None:
                forecasts[location_key] = result.forecast
            else:
                errors[location_key] = result.error or "Unknown forecast error"
            if on_progress:
                on_progress(index, total, location)

        return ForecastBatch(forecasts=forecasts, errors=errors)
