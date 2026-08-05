from datetime import date, datetime

from src.core.locations import ASTURIAS_LOCATIONS
from src.mobile.daily_summary import build_daily_summary, format_daily_summary


def _ranked_result(location_key, location_name, raw_score, start_hour):
    start = datetime(2026, 8, 6, start_hour)
    return {
        "location_key": location_key,
        "location_name": location_name,
        "raw_score": raw_score,
        "optimal_block": {
            "start": start,
            "end": start,
        },
    }


def test_daily_summary_keeps_priority_cities_first(monkeypatch):
    def fake_rank(forecasts, forecast_date, top_n, activity_profile):
        if activity_profile == "hiking":
            return [
                _ranked_result("llanes", "Llanes", 22, 11),
                _ranked_result("gijon", "Gijon", 18, 12),
                _ranked_result("oviedo", "Oviedo", 8, 13),
            ]
        return [
            _ranked_result("salinas", "Salinas", 20, 14),
            _ranked_result("gijon", "Gijon", 16, 15),
            _ranked_result("oviedo", "Oviedo", 6, 16),
        ]

    monkeypatch.setattr(
        "src.mobile.daily_summary.get_top_locations_for_date",
        fake_rank,
    )
    forecasts = {key: {} for key in ("oviedo", "gijon", "llanes", "salinas")}

    rows = build_daily_summary(
        forecasts,
        date(2026, 8, 6),
        ASTURIAS_LOCATIONS,
        alternative_limit=1,
    )

    assert [(row.activity_profile, row.location_key) for row in rows] == [
        ("hiking", "oviedo"),
        ("hiking", "gijon"),
        ("beach_day", "oviedo"),
        ("beach_day", "gijon"),
        ("hiking", "llanes"),
        ("beach_day", "salinas"),
    ]
    assert rows[0].score_text.endswith("/100")
    assert rows[0].best_window == "13:00 - 14:00"
    assert all(row.is_priority for row in rows[:4])
    assert not any(row.is_priority for row in rows[4:])


def test_daily_summary_keeps_missing_priority_city_visible(monkeypatch):
    monkeypatch.setattr(
        "src.mobile.daily_summary.get_top_locations_for_date",
        lambda *args, **kwargs: [],
    )

    rows = build_daily_summary(
        {"oviedo": {}},
        date(2026, 8, 6),
        ASTURIAS_LOCATIONS,
    )

    assert [(row.activity_profile, row.location_key) for row in rows] == [
        ("hiking", "oviedo"),
        ("beach_day", "oviedo"),
    ]
    assert rows[0].score_text == "N/A"
    assert rows[0].best_window == "Not available"


def test_daily_summary_text_uses_aligned_columns_without_em_dash():
    rows = build_daily_summary(
        {"oviedo": {}, "gijon": {}},
        date(2026, 8, 6),
        ASTURIAS_LOCATIONS,
    )
    text = format_daily_summary(rows, forecast_date=date(2026, 8, 6))
    table_lines = [
        line for line in text.splitlines()
        if line and not line.startswith("Daily ") and line != "Alternatives"
    ]

    assert "\u2014" not in text
    assert table_lines[0].index("Location") == table_lines[1].index("Oviedo")
    assert table_lines[0].index("Score") + len("Score") == table_lines[1].index(
        rows[0].score_text
    ) + len(rows[0].score_text)
    assert "Daily outdoor windows for Thu, 06 Aug" in text
