"""UI-independent orchestration for fetching and processing forecasts."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from src.core.evaluation import process_forecast
from src.core.locations import Location
from src.core.weather_api import fetch_weather_data

ProcessedForecast = dict[str, Any]
FetchForecast = Callable[[Location], Optional[dict[str, Any]]]
ProcessForecast = Callable[
    [dict[str, Any], str, Optional[str]], Optional[ProcessedForecast]
]
ProgressCallback = Callable[[int, int, Location], None]

logger = logging.getLogger(__name__)

# MET Norway asks clients to stay modest; a handful of parallel requests keeps
# a region loading quickly without hammering the service.
MAX_CONCURRENT_REQUESTS = 6

# How many failed locations to name before summarising the rest as a count.
MAX_NAMED_FAILURES = 3

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
    failed_names: dict[str, str] = field(default_factory=dict)

    @property
    def loaded_count(self) -> int:
        return len(self.forecasts)

    @property
    def failure_summary(self) -> str:
        """Return a readable list of the locations that could not be loaded."""
        names = sorted(self.failed_names.values())
        if not names:
            return ""
        if len(names) <= MAX_NAMED_FAILURES:
            return ", ".join(names)
        listed = ", ".join(names[:MAX_NAMED_FAILURES])
        return f"{listed} and {len(names) - MAX_NAMED_FAILURES} more"


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

            processed = self._process_forecast(
                raw_forecast, location.name, location.timezone
            )
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
        """Load a location group concurrently, keeping partial results.

        Locations were previously fetched one at a time, so a region of twenty
        could take minutes on a phone before anything appeared. Requests now
        overlap, and progress is reported as each one lands.
        """
        forecasts: dict[str, ProcessedForecast] = {}
        errors: dict[str, str] = {}
        failed_names: dict[str, str] = {}
        total = len(locations)
        if not total:
            return ForecastBatch()

        with ThreadPoolExecutor(max_workers=self._worker_count(total)) as executor:
            pending = {
                executor.submit(self.load_location, location): location_key
                for location_key, location in locations.items()
            }
            for completed, future in enumerate(as_completed(pending), start=1):
                location_key = pending[future]
                result = future.result()
                if result.forecast is not None:
                    forecasts[location_key] = result.forecast
                else:
                    errors[location_key] = result.error or "Unknown forecast error"
                    failed_names[location_key] = result.location.name
                if on_progress:
                    on_progress(completed, total, result.location)

        # Preserve the caller's ordering, which concurrency does not guarantee.
        ordered = {key: forecasts[key] for key in locations if key in forecasts}
        return ForecastBatch(
            forecasts=ordered, errors=errors, failed_names=failed_names
        )

    @staticmethod
    def _worker_count(total: int) -> int:
        """Return a request concurrency that stays polite to the data source."""
        return max(1, min(MAX_CONCURRENT_REQUESTS, total))
