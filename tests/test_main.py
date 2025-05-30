from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock, call
import pytest
from collections import defaultdict

from src.main import (
    display_best_times_recommendation,
    display_location_rankings_by_date,
    display_hourly_forecast,
    process_forecast,
    extract_best_blocks,
    recommend_best_times,
    display_warning
)
from src.hourly_weather import HourlyWeather
from src.daily_report import DailyReport
from src.locations import LOCATIONS


# Mock the LOCATIONS dictionary for testing
@pytest.fixture
def mock_locations():
    """Mock the LOCATIONS dictionary for testing."""
    with patch('src.utils.LOCATIONS', {
        'location1': MagicMock(name='Test Location 1'),
        'location2': MagicMock(name='Test Location 2')
    }):
        yield


@pytest.fixture
def mock_get_current_datetime():
    """Mock the current datetime to a fixed value."""
    fixed_dt = datetime(2024, 3, 20, 12, 0)
    with patch('src.main.get_current_datetime') as mock:
        mock.return_value = fixed_dt
        yield mock


@pytest.fixture
def mock_get_location_display_name():
    """Mock the location display name function."""
    with patch('src.main.get_location_display_name') as mock:
        mock.side_effect = lambda loc_key: f"Test Location {loc_key}"
        yield mock


@pytest.fixture
def raw_forecast_data():
    """Fixture providing raw sample forecast data."""
    return {
        "properties": {
            "timeseries": [
                {
                    "time": "2024-03-20T08:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 20.0,
                                "wind_speed": 5.0,
                                "relative_humidity": 60,
                                "cloud_area_fraction": 0,
                                "fog_area_fraction": 0,
                                "wind_from_direction": 180,
                                "wind_speed_of_gust": 8.0
                            }
                        },
                        "next_1_hours": {
                            "details": {
                                "precipitation_amount": 0,
                                "probability_of_precipitation": 10
                            },
                            "summary": {
                                "symbol_code": "clearsky"
                            }
                        }
                    }
                },
                {
                    "time": "2024-03-20T12:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 22.0,
                                "wind_speed": 8.0,
                                "relative_humidity": 55,
                                "cloud_area_fraction": 50,
                                "fog_area_fraction": 0,
                                "wind_from_direction": 190,
                                "wind_speed_of_gust": 12.0
                            }
                        },
                        "next_1_hours": {
                            "details": {
                                "precipitation_amount": 0,
                                "probability_of_precipitation": 20
                            },
                            "summary": {
                                "symbol_code": "partlycloudy"
                            }
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def mock_processed_forecast_data(mock_get_current_datetime):
    """Fixture providing mocked processed forecast data."""
    today = mock_get_current_datetime.return_value.date()

    # Create hourly weather objects
    hourly_1 = HourlyWeather(
        time=datetime.combine(today, datetime.min.time()) + timedelta(hours=8),
        temp=20.0,
        wind=5.0,
        symbol="clearsky",
        precipitation_probability=10,
        weather_score=10,
        temp_score=8,
        wind_score=9,
        cloud_score=10,
        precip_prob_score=9
    )

    hourly_2 = HourlyWeather(
        time=datetime.combine(today, datetime.min.time()) + timedelta(hours=12),
        temp=22.0,
        wind=8.0,
        symbol="partlycloudy",
        precipitation_probability=20,
        weather_score=8,
        temp_score=7,
        wind_score=6,
        cloud_score=5,
        precip_prob_score=8
    )

    # Create daily report
    daily_report = DailyReport(today, [hourly_1, hourly_2], "Test Location")

    # Create processed data structure
    daily_forecasts = defaultdict(list)
    daily_forecasts[today] = [hourly_1, hourly_2]

    day_scores = {}
    day_scores[today] = daily_report

    return {
        "daily_forecasts": daily_forecasts,
        "day_scores": day_scores
    }


@pytest.fixture
def mock_all_locations_data(mock_get_current_datetime, mock_processed_forecast_data):
    """Fixture providing data for multiple locations."""
    return {
        "location1": mock_processed_forecast_data,
        "location2": mock_processed_forecast_data
    }


@pytest.fixture
def mock_recommendation_blocks(mock_get_current_datetime):
    """Fixture providing recommendation blocks."""
    today = mock_get_current_datetime.return_value.date()

    return [{
        "date": today,
        "start_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=8),
        "end_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=12),
        "final_score": 10.0,
        "location": "location1",
        "dominant_symbol": "clearsky"
    }]


@patch('builtins.print')
def test_display_best_times_recommendation(mock_print, mock_locations, mock_get_current_datetime,
                                          mock_all_locations_data, mock_recommendation_blocks):
    """Test display of best times recommendation."""
    with patch('src.main.recommend_best_times', return_value=mock_recommendation_blocks):
        display_best_times_recommendation(mock_all_locations_data)

    # Verify that print was called at least once
    assert mock_print.call_count > 0


@patch('builtins.print')
def test_display_location_rankings_by_date(mock_print, mock_locations, mock_get_current_datetime,
                                          mock_get_location_display_name, mock_all_locations_data):
    """Test display of location rankings by date."""
    today = mock_get_current_datetime.return_value.date()
    test_dates = [today]

    display_location_rankings_by_date(mock_all_locations_data, test_dates)

    # Verify that print was called at least once
    assert mock_print.call_count > 0


@patch('builtins.print')
def test_display_hourly_forecast(mock_print, mock_locations, mock_get_current_datetime,
                                mock_processed_forecast_data):
    """Test display of hourly forecast."""
    display_hourly_forecast(mock_processed_forecast_data, "Test Location")

    # Verify that print was called at least once
    assert mock_print.call_count > 0

    # Check that Test Location appears somewhere in the output (allowing for color codes)
    all_output = ''.join(str(call[0][0]) for call in mock_print.call_args_list)
    assert "Test Location" in all_output


@patch('src.main.get_timezone')
@patch('src.main.get_current_datetime')
@patch('src.main.datetime')
def test_process_forecast(mock_datetime, mock_current_datetime, mock_timezone, mock_locations, raw_forecast_data):
    """Test forecast data processing."""
    # Setup mocks
    today = datetime(2024, 3, 20, 12, 0)
    mock_current_datetime.return_value = today
    mock_timezone.return_value = datetime.now().astimezone().tzinfo

    # Mock datetime.now() used inside process_forecast
    mock_datetime.now.return_value = today
    mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x)

    # Process the forecast data
    result = process_forecast(raw_forecast_data, "location1")

    # Verify the structure
    assert result is not None
    assert "daily_forecasts" in result
    assert "day_scores" in result

    # Just verify there's any data in daily_forecasts
    assert len(result["daily_forecasts"]) > 0


@patch('src.main.extract_best_blocks')
@patch('src.main.get_current_date')
def test_recommend_best_times(mock_get_current_date, mock_extract_blocks, mock_locations,
                             mock_all_locations_data, mock_recommendation_blocks):
    """Test recommendation of best times."""
    # Setup mocks
    today = date(2024, 3, 20)
    mock_get_current_date.return_value = today

    # Mock extract_best_blocks to return blocks with actual date (not datetime object)
    blocks_to_return = [{
        "date": today,
        "start_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=8),
        "end_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=12),
        "final_score": 10.0,
        "location": "location1",
        "dominant_symbol": "clearsky"
    }]
    mock_extract_blocks.return_value = blocks_to_return

    recommendations = recommend_best_times(mock_all_locations_data)
    assert len(recommendations) > 0


@patch('builtins.print')
def test_display_best_times_recommendation_with_filters(mock_print, mock_locations,
                                                      mock_get_current_datetime,
                                                      mock_all_locations_data,
                                                      mock_recommendation_blocks):
    """Test display of best times with location and date filters."""
    today = mock_get_current_datetime.return_value.date()

    with patch('src.main.recommend_best_times', return_value=mock_recommendation_blocks):
        # Test with location filter
        display_best_times_recommendation(mock_all_locations_data, location_key="location1")
        assert mock_print.call_count > 0

        # Reset mock
        mock_print.reset_mock()

        # Test with date filter
        display_best_times_recommendation(mock_all_locations_data, date_filters=[today])
        assert mock_print.call_count > 0


@patch('src.main.display_warning')
def test_display_hourly_forecast_no_data(mock_display_warning):
    """Test display of hourly forecast with no data."""
    # The function just returns without calling display_warning when data is None
    display_hourly_forecast(None, "Test Location")
    assert not mock_display_warning.called

    # With daily_forecasts dict but no data for today
    with patch('src.main.get_current_datetime') as mock_datetime:
        today = date(2024, 3, 20)
        mock_datetime.return_value.date.return_value = today

        # This should call display_warning
        display_hourly_forecast({"daily_forecasts": {}}, "Test Location")
        mock_display_warning.assert_called_with("No hourly data available for today.")


def test_process_forecast_empty_data():
    """Test processing of empty forecast data."""
    result = process_forecast(None, "Test Location")
    assert result is None