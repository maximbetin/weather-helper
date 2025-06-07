import pytest
from datetime import date, datetime, timezone
from src.core.evaluation import process_forecast, get_top_locations_for_date

# Mock forecast data for testing


def create_mock_forecast(air_temp):
  now = datetime.now(timezone.utc)
  return {
      "properties": {
          "timeseries": [
              {
                  "time": now.isoformat().replace("+00:00", "Z"),
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": air_temp,
                              "wind_speed": 1.0,
                              "relative_humidity": 50.0,
                              "cloud_area_fraction": 20.0,
                          }
                      },
                      "next_1_hours": {
                          "summary": {"symbol_code": "clearsky_day"},
                          "details": {"precipitation_amount": 0.0, "probability_of_precipitation": 0.0},
                      },
                  },
              }
          ]
      }
  }


def test_process_forecast():
  forecast_data = create_mock_forecast(20)
  processed_data = process_forecast(forecast_data, "Test Location")
  assert processed_data is not None
  assert "daily_forecasts" in processed_data
  assert "day_scores" in processed_data
  assert len(processed_data["daily_forecasts"]) == 1


def test_process_forecast_empty():
  processed_data = process_forecast({}, "Test Location")
  assert processed_data is None


def test_get_top_locations_for_date():
  all_locations_processed = {
      "loc1": process_forecast(create_mock_forecast(25), "Location 1"),  # Warmer, so higher score
      "loc2": process_forecast(create_mock_forecast(15), "Location 2"),
  }
  # Filter out None values before passing to the function
  processed_data = {k: v for k, v in all_locations_processed.items() if v is not None}
  top_locations = get_top_locations_for_date(processed_data, date.today())
  assert len(top_locations) == 2
  assert top_locations[0]["location_name"] == "Location 1"
  assert top_locations[1]["location_name"] == "Location 2"


def test_get_top_locations_for_date_no_data():
  top_locations = get_top_locations_for_date({}, date.today())
  assert len(top_locations) == 0


def test_get_top_locations_for_date_less_than_n():
  all_locations_processed = {
      "loc1": process_forecast(create_mock_forecast(25), "Location 1"),
  }
  processed_data = {k: v for k, v in all_locations_processed.items() if v is not None}
  top_locations = get_top_locations_for_date(processed_data, date.today(), top_n=5)
  assert len(top_locations) == 1


def test_get_top_locations_for_date_no_matching_date():
  all_locations_processed = {
      "loc1": process_forecast(create_mock_forecast(25), "Location 1"),
  }
  processed_data = {k: v for k, v in all_locations_processed.items() if v is not None}
  top_locations = get_top_locations_for_date(processed_data, date(2000, 1, 1), top_n=5)
  assert len(top_locations) == 0
