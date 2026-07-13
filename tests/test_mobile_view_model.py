from datetime import datetime, timedelta

import pytest

from src.application.forecast_service import ForecastBatch
from src.core.config import get_current_date
from src.core.models import DailyReport, HourlyWeather
from src.core.scoring import ACTIVITY_BEACH_DAY
from src.mobile.view_model import MobileWeatherViewModel


class StubForecastService:
    def __init__(self, batch):
        self.batch = batch
        self.requested_locations = None

    def load_locations(self, locations):
        self.requested_locations = locations
        return self.batch


def _processed_forecast(location_name, forecast_date, total_score):
    hour = HourlyWeather(
        time=datetime.combine(forecast_date, datetime.min.time()).replace(hour=12),
        temp=24,
        wind=2,
        cloud_coverage=20,
        precipitation_amount=0,
        precipitation_probability=10,
        relative_humidity=60,
        temp_score=total_score,
    )
    report = DailyReport(
        datetime.combine(forecast_date, datetime.min.time()),
        [hour],
        location_name,
    )
    return {
        "daily_forecasts": {forecast_date: [hour]},
        "day_scores": {forecast_date: report},
    }


def test_load_exposes_dates_rankings_and_hourly_details():
    forecast_date = get_current_date() + timedelta(days=1)
    batch = ForecastBatch(
        forecasts={
            "gijon": _processed_forecast("Gijón", forecast_date, 18),
            "oviedo": _processed_forecast("Oviedo", forecast_date, 8),
        },
        errors={"llanes": "offline"},
    )
    service = StubForecastService(batch)
    model = MobileWeatherViewModel(service=service)

    loaded = model.load()
    ranked = model.ranked_locations()
    hourly = model.hourly_forecast(ranked[0].location_key)

    assert loaded is batch
    assert model.selected_date == forecast_date
    assert model.selected_location_key == "gijon"
    assert model.location_options() == [("gijon", "Gijón"), ("oviedo", "Oviedo")]
    assert [item.location_name for item in ranked] == ["Gijón", "Oviedo"]
    assert ranked[0].raw_score == 18
    assert ranked[0].best_window == "12:00–13:00"
    assert "Temp: 24.0°C" in ranked[0].best_window_details
    assert "Rain Risk: 10%" in ranked[0].best_window_details
    assert hourly[0].time == "12:00"
    assert hourly[0].temperature == "24.0°C"
    assert hourly[0].wind == "2.0 m/s"
    assert hourly[0].clouds == "20%"
    assert hourly[0].precipitation == "0.0 mm"
    assert hourly[0].rain_risk == "10%"
    assert hourly[0].humidity == "60%"
    assert hourly[0].normalized_score == 90
    assert hourly[0].rating == "Excellent"
    assert service.requested_locations == model.locations


def test_any_loaded_location_can_be_selected_outside_a_short_ranking():
    forecast_date = get_current_date() + timedelta(days=1)
    forecasts = {
        key: _processed_forecast(
            location.name, forecast_date, 20 - index
        )
        for index, (key, location) in enumerate(
            MobileWeatherViewModel().locations.items()
        )
    }
    model = MobileWeatherViewModel(
        service=StubForecastService(ForecastBatch(forecasts=forecasts))
    )
    model.load()

    outside_top_ten = model.ranked_locations(12)[-1]
    model.select_location(outside_top_ten.location_key)

    assert outside_top_ten.location_key not in {
        item.location_key for item in model.ranked_locations(10)
    }
    assert model.selected_location() == outside_top_ten


def test_loaded_location_without_qualifying_block_is_selectable():
    forecast_date = get_current_date() + timedelta(days=1)
    poor_forecast = _processed_forecast("Gijón", forecast_date, -20)
    model = MobileWeatherViewModel(
        service=StubForecastService(
            ForecastBatch(forecasts={"gijon": poor_forecast})
        )
    )

    model.load()
    model.select_location("gijon")
    selected = model.selected_location()

    assert model.location_options() == [("gijon", "Gijón")]
    assert model.ranked_locations() == []
    assert selected is not None
    assert not selected.is_ranked
    assert selected.normalized_score is None
    assert "No qualifying recommended window" in selected.best_window_details
    assert model.hourly_forecast("gijon")[0].time == "12:00"


def test_refresh_preserves_selected_location_when_data_remains_available():
    forecast_date = get_current_date() + timedelta(days=1)
    batch = ForecastBatch(
        forecasts={
            "gijon": _processed_forecast("Gijón", forecast_date, 18),
            "oviedo": _processed_forecast("Oviedo", forecast_date, 8),
        }
    )
    service = StubForecastService(batch)
    model = MobileWeatherViewModel(service=service)
    model.load()
    model.select_location("oviedo")

    service.batch = ForecastBatch(forecasts=dict(batch.forecasts))
    model.load()

    assert model.selected_location_key == "oviedo"


def test_profile_change_keeps_valid_unranked_selection_visible():
    forecast_date = get_current_date() + timedelta(days=1)
    model = MobileWeatherViewModel(
        service=StubForecastService(
            ForecastBatch(
                forecasts={
                    "gijon": _processed_forecast("Gijón", forecast_date, -20)
                }
            )
        )
    )
    model.load()

    model.select_activity_profile(ACTIVITY_BEACH_DAY)

    assert model.selected_location_key == "gijon"
    assert model.selected_location() is not None


def test_profile_and_group_changes_reset_only_relevant_state():
    model = MobileWeatherViewModel(service=StubForecastService(ForecastBatch()))
    model.forecasts = {"existing": {}}
    model.select_activity_profile(ACTIVITY_BEACH_DAY)

    assert model.activity_profile == ACTIVITY_BEACH_DAY
    assert model.forecasts == {"existing": {}}

    model.select_group("Spain")

    assert model.group_name == "Spain"
    assert model.forecasts == {}
    assert model.selected_date is None


def test_invalid_mobile_selections_fail_clearly():
    model = MobileWeatherViewModel(service=StubForecastService(ForecastBatch()))

    with pytest.raises(ValueError, match="Unknown location group"):
        model.select_group("Atlantis")
    with pytest.raises(ValueError, match="Unknown activity profile"):
        model.select_activity_profile("surfing")

    with pytest.raises(ValueError, match="Location is not available"):
        model.select_location("nowhere")
