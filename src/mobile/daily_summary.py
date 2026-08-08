"""Daily activity summaries shared by the mobile screen and notifications."""

from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

from src.core.evaluation import get_top_locations_for_date
from src.core.locations import Location
from src.core.scoring import (
    ACTIVITY_BEACH_DAY,
    ACTIVITY_HIKING,
    get_activity_profile_label,
    normalize_score,
)

PRIORITY_LOCATION_KEYS = ("oviedo", "gijon")
SUMMARY_ACTIVITY_PROFILES = (ACTIVITY_HIKING, ACTIVITY_BEACH_DAY)
DEFAULT_ALTERNATIVE_LIMIT = 3


@dataclass(frozen=True)
class DailySummaryRow:
    """One activity and location recommendation in the daily summary."""

    activity_profile: str
    activity_label: str
    location_key: str
    location_name: str
    normalized_score: Optional[int]
    best_window: str
    is_priority: bool

    @property
    def score_text(self) -> str:
        """Return a compact score suitable for a table or notification."""
        if self.normalized_score is None:
            return "N/A"
        return f"{self.normalized_score}/100"


def resolve_priority_keys(
    locations: Mapping[str, Location],
    forecasts: Mapping[str, dict] = MappingProxyType({}),
    priority_location_keys: Sequence[str] = PRIORITY_LOCATION_KEYS,
) -> list[str]:
    """Return the priority locations that exist in the current region.

    Regions outside Asturias contain neither Oviedo nor Gijon, so nothing is
    pinned there and the screen must not claim otherwise.
    """
    return [
        key
        for key in priority_location_keys
        if key in locations and (not forecasts or key in forecasts)
    ]


def build_daily_summary(
    forecasts: Mapping[str, dict],
    forecast_date: date,
    locations: Mapping[str, Location],
    *,
    activity_profiles: Sequence[str] = SUMMARY_ACTIVITY_PROFILES,
    priority_location_keys: Sequence[str] = PRIORITY_LOCATION_KEYS,
    alternative_limit: int = DEFAULT_ALTERNATIVE_LIMIT,
) -> list[DailySummaryRow]:
    """Build priority rows first, followed by the strongest alternatives.

    Pinned locations stay visible even when their conditions do not qualify for
    the normal ranking, which is the point of the panel: it answers "how is it
    at home, and where is better today" in one look. Alternatives are limited
    per activity so the result stays readable.
    """
    primary_rows: list[DailySummaryRow] = []
    alternative_rows: list[DailySummaryRow] = []
    priority_keys = set(
        resolve_priority_keys(locations, forecasts, priority_location_keys)
    )

    for activity_profile in activity_profiles:
        ranked = get_top_locations_for_date(
            dict(forecasts),
            forecast_date,
            top_n=max(len(forecasts), 1),
            activity_profile=activity_profile,
        )
        ranked_by_key = {item["location_key"]: item for item in ranked}

        for location_key in priority_location_keys:
            if location_key not in priority_keys:
                continue
            primary_rows.append(
                _row_from_result(
                    activity_profile,
                    location_key,
                    locations[location_key].name,
                    ranked_by_key.get(location_key),
                    is_priority=True,
                )
            )

        selected_alternatives = [
            item
            for item in ranked
            if item["location_key"] not in priority_keys
        ][: max(0, alternative_limit)]
        alternative_rows.extend(
            _row_from_result(
                activity_profile,
                item["location_key"],
                locations[item["location_key"]].name
                if item["location_key"] in locations
                else item["location_name"],
                item,
                is_priority=False,
            )
            for item in selected_alternatives
        )

    return primary_rows + alternative_rows


def format_daily_summary(
    rows: Sequence[DailySummaryRow],
    *,
    forecast_date: Optional[date] = None,
) -> str:
    """Format the summary as aligned plain text for notifications or sharing."""
    if not rows:
        return "No daily activity recommendations are available."

    activity_header = "Activity"
    location_header = "Location"
    score_header = "Score"
    window_header = "Best time"

    activity_width = max(
        len(activity_header), *(len(row.activity_label) for row in rows)
    )
    location_width = max(
        len(location_header), *(len(row.location_name) for row in rows)
    )
    score_width = max(len(score_header), *(len(row.score_text) for row in rows))
    window_width = max(len(window_header), *(len(row.best_window) for row in rows))

    lines = [
        _summary_title(forecast_date),
        (
            f"{activity_header:<{activity_width}}  "
            f"{location_header:<{location_width}}  "
            f"{score_header:>{score_width}}  "
            f"{window_header:<{window_width}}"
        ),
    ]
    priority_rows = [row for row in rows if row.is_priority]
    alternative_rows = [row for row in rows if not row.is_priority]
    lines.extend(
        _format_row(row, activity_width, location_width, score_width, window_width)
        for row in priority_rows
    )
    if alternative_rows:
        lines.extend(("", "Alternatives"))
        lines.extend(
            _format_row(row, activity_width, location_width, score_width, window_width)
            for row in alternative_rows
        )
    return "\n".join(lines)


def _row_from_result(
    activity_profile: str,
    location_key: str,
    location_name: str,
    result: Optional[dict],
    *,
    is_priority: bool,
) -> DailySummaryRow:
    if result is None:
        return DailySummaryRow(
            activity_profile=activity_profile,
            activity_label=get_activity_profile_label(activity_profile),
            location_key=location_key,
            location_name=location_name,
            normalized_score=None,
            best_window="Not available",
            is_priority=is_priority,
        )

    block = result["optimal_block"]
    end_time = block["end_time"]
    raw_score = float(result["raw_score"])
    return DailySummaryRow(
        activity_profile=activity_profile,
        activity_label=get_activity_profile_label(activity_profile),
        location_key=location_key,
        location_name=location_name,
        normalized_score=normalize_score(raw_score, activity_profile),
        best_window=f"{block['start']:%H:%M} - {end_time:%H:%M}",
        is_priority=is_priority,
    )


def _format_row(
    row: DailySummaryRow,
    activity_width: int,
    location_width: int,
    score_width: int,
    window_width: int,
) -> str:
    return (
        f"{row.activity_label:<{activity_width}}  "
        f"{row.location_name:<{location_width}}  "
        f"{row.score_text:>{score_width}}  "
        f"{row.best_window:<{window_width}}"
    )


def _summary_title(forecast_date: Optional[date]) -> str:
    if forecast_date is None:
        return "Daily outdoor windows"
    return f"Daily outdoor windows for {forecast_date:%a, %d %b}"
