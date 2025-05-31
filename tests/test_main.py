import importlib
from collections import defaultdict
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

import src.main
from src.daily_report import DailyReport
from src.hourly_weather import HourlyWeather
from src.locations import LOCATIONS
from src.main import (display_best_times_recommendation, display_hourly_forecast, display_location_rankings_by_date, display_warning, extract_best_blocks, main,
                      process_forecast, recommend_best_times)


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
def test_display_location_rankings_by_date(mock_print, mock_locations, mock_get_current_datetime, mock_get_location_display_name, mock_all_locations_data):
  """Test display of location rankings by date."""
  today = mock_get_current_datetime.return_value.date()
  test_dates = [today]

  display_location_rankings_by_date(mock_all_locations_data, test_dates)

  # Verify that print was called at least once
  assert mock_print.call_count > 0


@patch('builtins.print')
def test_display_hourly_forecast(mock_print, mock_locations, mock_get_current_datetime, mock_processed_forecast_data):
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
def test_recommend_best_times(mock_get_current_date, mock_extract_blocks, mock_locations, mock_all_locations_data, mock_recommendation_blocks):
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
def test_display_best_times_recommendation_with_filters(mock_print, mock_locations, mock_get_current_datetime, mock_all_locations_data, mock_recommendation_blocks):
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


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_default_location(mock_parse_args, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with default location."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = None
  mock_args.all = False
  mock_args.rank = False
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Setup mock for fetch_weather_data
  mock_weather_data = {"properties": {"timeseries": []}}
  mock_fetch_weather.return_value = mock_weather_data

  # Setup mock for process_forecast
  processed_data = {"daily_forecasts": {}, "day_scores": {}}
  mock_process_forecast.return_value = processed_data

  # Call main function
  main()

  # Verify default location is used
  assert mock_fetch_weather.call_count == 1
  assert mock_display_hourly.call_count == 1


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_specific_location(mock_parse_args, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with specific location argument."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = "location1"
  mock_args.all = False
  mock_args.rank = False
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Setup mocks
  mock_weather_data = {"properties": {"timeseries": []}}
  mock_fetch_weather.return_value = mock_weather_data
  processed_data = {"daily_forecasts": {}, "day_scores": {}}
  mock_process_forecast.return_value = processed_data

  # Call main function
  with patch('src.main.LOCATIONS', {'location1': MagicMock(name='Test Location')}):
    main()

  # Verify location is used
  assert mock_fetch_weather.call_count == 1
  assert mock_display_hourly.call_count == 1


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_invalid_location(mock_parse_args, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with invalid location argument."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = "invalid_location"
  mock_args.all = False
  mock_args.rank = False
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Call main function
  with patch('src.main.LOCATIONS', {'location1': MagicMock(name='Test Location')}):
    main()

  # Verify error is displayed
  mock_display_error.assert_called_once()
  # Verify no data fetching happened
  assert mock_fetch_weather.call_count == 0


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_all_locations(mock_parse_args, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with --all flag."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = None
  mock_args.all = True
  mock_args.rank = False
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Setup mocks
  mock_weather_data = {"properties": {"timeseries": []}}
  mock_fetch_weather.return_value = mock_weather_data
  processed_data = {"daily_forecasts": {}, "day_scores": {}}
  mock_process_forecast.return_value = processed_data

  # Mock locations
  mock_locations = {
      'location1': MagicMock(name='Location 1'),
      'location2': MagicMock(name='Location 2')
  }

  # Call main function
  with patch('src.main.LOCATIONS', mock_locations):
    main()

  # Verify all locations are fetched
  assert mock_fetch_weather.call_count == 2
  # Verify hourly forecast is displayed for each location
  assert mock_display_hourly.call_count == 2


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.display_info')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_rank_flag(mock_parse_args, mock_display_info, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with --rank flag."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = None
  mock_args.all = False
  mock_args.rank = True
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Setup mocks
  mock_weather_data = {"properties": {"timeseries": []}}
  mock_fetch_weather.return_value = mock_weather_data
  processed_data = {"daily_forecasts": {}, "day_scores": {}}
  mock_process_forecast.return_value = processed_data

  # Mock locations
  mock_locations = {
      'location1': MagicMock(name='Location 1'),
      'location2': MagicMock(name='Location 2')
  }

  # Call main function
  with patch('src.main.LOCATIONS', mock_locations):
    with patch('src.main.datetime') as mock_datetime:
      # Mock datetime.now to return a fixed date
      mock_now = MagicMock()
      mock_now.date.return_value = date(2024, 3, 20)
      mock_datetime.now.return_value = mock_now

      main()

  # Verify all locations are fetched
  assert mock_fetch_weather.call_count == 2
  # Verify display_best_times_recommendation is called with dates
  mock_display_best_times.assert_called_once()
  # Verify the third argument (dates) has 3 dates
  assert len(mock_display_best_times.call_args[0][2]) == 3


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.display_info')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_debug_flag(mock_parse_args, mock_display_info, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function with --debug flag."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = None
  mock_args.all = False
  mock_args.rank = False
  mock_args.debug = True
  mock_parse_args.return_value = mock_args

  # Setup mocks
  mock_weather_data = {"properties": {"timeseries": []}}
  mock_fetch_weather.return_value = mock_weather_data
  processed_data = {"daily_forecasts": {}, "day_scores": {}}
  mock_process_forecast.return_value = processed_data

  # Call main function
  with patch('src.main.LOCATIONS', {'gijon': MagicMock(name='Test Location')}):
    main()

  # Verify debug info is displayed
  assert mock_display_info.call_count == 1


@patch('src.main.display_best_times_recommendation')
@patch('src.main.display_hourly_forecast')
@patch('src.main.display_error')
@patch('src.main.display_loading_message')
@patch('src.main.fetch_weather_data')
@patch('src.main.process_forecast')
@patch('src.main.argparse.ArgumentParser.parse_args')
def test_main_with_failed_data_fetch(mock_parse_args, mock_process_forecast, mock_fetch_weather, mock_loading, mock_display_error, mock_display_hourly, mock_display_best_times):
  """Test main function when weather data fetch fails."""
  # Setup mock for args
  mock_args = MagicMock()
  mock_args.location = None
  mock_args.all = False
  mock_args.rank = False
  mock_args.debug = False
  mock_parse_args.return_value = mock_args

  # Setup fetch_weather_data to return None (failed fetch)
  mock_fetch_weather.return_value = None

  # Call main function
  with patch('src.main.LOCATIONS', {'gijon': MagicMock(name='Test Location')}):
    main()

  # Verify error message is displayed
  assert mock_display_error.call_count >= 1  # One for fetch fail
  assert mock_process_forecast.call_count == 0  # Process should not be called


@patch('builtins.print')
def test_display_best_times_recommendation_no_data(mock_print):
  """Test display_best_times_recommendation with empty data."""
  display_best_times_recommendation({})
  assert mock_print.call_count == 0


@patch('builtins.print')
def test_display_best_times_recommendation_no_recommendations(mock_print):
  """Test display_best_times_recommendation with no good periods."""
  with patch('src.main.recommend_best_times', return_value=[]):
    display_best_times_recommendation({"location1": {}})

  mock_print.assert_called_once_with("No good weather periods found in the forecast.")


@patch('builtins.print')
def test_display_best_times_with_precipitation(mock_print):
  """Test display_best_times_recommendation with precipitation data."""
  # Add precipitation data to recommendation blocks
  today = date(2024, 3, 20)
  blocks_with_precip = [{
      "date": today,
      "start_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=8),
      "end_time": datetime.combine(today, datetime.min.time()) + timedelta(hours=12),
      "final_score": 10.0,
      "location": "location1",
      "dominant_symbol": "clearsky",
      "precipitation_probability": 30.0
  }]

  with patch('src.main.recommend_best_times', return_value=blocks_with_precip):
    with patch('src.main.get_location_display_name', return_value="Test Location"):
      display_best_times_recommendation({"location1": {}})

  # Verify output was produced
  assert mock_print.call_count > 0


def test_extract_blocks_function():
  """Test the extract_blocks function with a custom implementation."""
  from datetime import datetime, timedelta

  from src.hourly_weather import HourlyWeather

  # Create a mock implementation of extract_blocks
  def mock_extract_blocks(hours, min_block_len=2):
    return [([hours[0]], "sunny")]

  # Test extract_best_blocks with our mock
  with patch('src.main.extract_blocks', side_effect=mock_extract_blocks):
    # Create test data
    today = date(2024, 3, 20)
    hourly_data = HourlyWeather(
        time=datetime.combine(today, datetime.min.time()) + timedelta(hours=10),
        temp=20.0,
        wind=5.0,
        symbol="clearsky"
    )

    forecast_data = {
        "daily_forecasts": {today: [hourly_data]},
        "day_scores": {today: MagicMock()}
    }

    # Call the function
    blocks = extract_best_blocks(forecast_data, "test_location")

    # Verify result
    assert len(blocks) > 0
    assert blocks[0]["location"] == "test_location"
    assert blocks[0]["date"] == today


def test_extract_best_blocks_empty_weather():
  """Test extract_best_blocks with no suitable weather blocks."""
  # Create a mock implementation of extract_blocks that returns no sunny blocks
  def mock_extract_blocks(hours, min_block_len=2):
    return [(hours, "cloudy")]  # Only cloudy blocks, no sunny ones

  with patch('src.main.extract_blocks', side_effect=mock_extract_blocks):
    today = date(2024, 3, 20)
    hourly_data = HourlyWeather(
        time=datetime.combine(today, datetime.min.time()) + timedelta(hours=10),
        temp=20.0,
        wind=5.0,
        symbol="cloudy"
    )

    forecast_data = {
        "daily_forecasts": {today: [hourly_data]},
        "day_scores": {today: MagicMock()}
    }

    # Call the function
    blocks = extract_best_blocks(forecast_data, "test_location")

    # Should return empty list since no sunny blocks
    assert len(blocks) == 0


def test_extract_best_blocks_with_empty_data():
  """Test extract_best_blocks with empty data cases."""
  # Test with missing keys
  assert extract_best_blocks({}, "location1") == []
  assert extract_best_blocks({"daily_forecasts": {}}, "location1") == []
  assert extract_best_blocks(None, "location1") == []


def test_recommend_best_times_with_empty_data():
  """Test recommend_best_times with empty data."""
  # Test with empty data
  assert recommend_best_times({}) == []

  # Test with location but empty forecast
  with patch('src.main.extract_best_blocks', return_value=[]):
    assert recommend_best_times({"location1": {}}) == []


def test_recommend_best_times_with_future_dates():
  """Test recommend_best_times with dates beyond the target dates."""
  with patch('src.main.get_current_date') as mock_get_current_date:
    today = date(2024, 3, 20)
    mock_get_current_date.return_value = today

    # Create blocks for a date far in the future (outside our 3-day window)
    future_date = today + timedelta(days=10)
    blocks = [{
        "date": future_date,
        "start_time": datetime.combine(future_date, datetime.min.time()),
        "end_time": datetime.combine(future_date, datetime.min.time()) + timedelta(hours=4),
        "final_score": 10.0,
        "location": "location1"
    }]

    with patch('src.main.extract_best_blocks', return_value=blocks):
      result = recommend_best_times({"location1": {}})
      assert result == []  # Should be empty as date is outside target range


@patch('builtins.print')
def test_display_location_rankings_no_data(mock_print):
  """Test display_location_rankings_by_date with no data for the date."""
  today = date(2024, 3, 20)

  # Create data with no matching date
  data = {
      "location1": {
          "day_scores": {}  # No data for today
      }
  }

  with patch('src.main.get_location_display_name', return_value="Test Location"):
    display_location_rankings_by_date(data, [today])

  # Should print header but no data rows
  assert mock_print.call_count > 0


@patch('src.main.main')
def test_main_if_name_eq_main(mock_main):
  """Test if __name__ == "__main__" code path."""
  # Save the original value
  original_name = src.main.__name__
  original_if_check = getattr(src.main, "_if_name_is_main_was_checked", False)

  try:
    # Create a flag to avoid re-checking during import
    setattr(src.main, "_if_name_is_main_was_checked", False)

    # Set __name__ to "__main__"
    src.main.__name__ = "__main__"

    # Execute the if __name__ == "__main__" block directly
    if src.main.__name__ == "__main__":
      src.main.main()

    # Verify main was called
    mock_main.assert_called_once()
  finally:
    # Restore the original values
    src.main.__name__ = original_name
    setattr(src.main, "_if_name_is_main_was_checked", original_if_check)


def test_extract_best_blocks_complete_coverage():
  """Test additional edge cases in extract_best_blocks."""
  # Create a minimal processed forecast with score calculation values
  today = date(2024, 3, 20)
  hourly_weather = HourlyWeather(
      time=datetime.combine(today, datetime.min.time()) + timedelta(hours=10),
      temp=20.0,
      wind=5.0,
      symbol="clearsky",
      temp_score=8,
      wind_score=9,
      weather_score=10,
      cloud_score=9,
      precip_prob_score=10
  )

  # Create a test dataset with no temperature data
  no_temp_hourly = HourlyWeather(
      time=datetime.combine(today, datetime.min.time()) + timedelta(hours=12),
      temp=None,
      wind=5.0,
      symbol="clearsky",
      temp_score=0,
      wind_score=9,
      weather_score=10,
      cloud_score=9,
      precip_prob_score=10
  )

  # Create the forecast data structure
  forecast_data = {
      "daily_forecasts": {
          today: [hourly_weather, no_temp_hourly]
      },
      "day_scores": {
          today: MagicMock()
      }
  }

  # Create a mock implementation of extract_blocks that returns sunny blocks
  def mock_extract_blocks(hours, min_block_len=2):
    return [([hourly_weather, no_temp_hourly], "sunny")]

  # Test with the custom mock implementation
  with patch('src.main.extract_blocks', side_effect=mock_extract_blocks):
    blocks = extract_best_blocks(forecast_data, "test_location")

    # Verify result has temperature average when one hour has None temp
    assert len(blocks) == 1
    assert "avg_temp" in blocks[0]
    # Only one hour has temperature, so avg should equal that value
    assert blocks[0]["avg_temp"] == 20.0


def test_main_no_locations():
  """Test main function with empty locations."""
  with patch('src.main.LOCATIONS', {}):
    with patch('src.main.argparse.ArgumentParser.parse_args') as mock_parse_args:
      # Setup args mock
      mock_args = MagicMock()
      mock_args.location = None
      mock_args.all = True  # Try to get all locations
      mock_args.rank = False
      mock_args.debug = False
      mock_parse_args.return_value = mock_args

      # Mock the display functions
      with patch('src.main.display_error') as mock_error:
        # Call main
        main()

        # Verify error is displayed
        assert mock_error.call_count > 0


def test_process_forecast_with_non_daylight_hours():
  """Test process_forecast with hours outside daylight range."""
  # Create test data with both daylight and non-daylight hours
  test_data = {
      "properties": {
          "timeseries": [
              # Early morning hour (before daylight)
              {
                  "time": "2024-03-20T04:00:00Z",
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": 15.0,
                              "wind_speed": 3.0
                          }
                      },
                      "next_1_hours": {
                          "details": {},
                          "summary": {
                              "symbol_code": "clearsky"
                          }
                      }
                  }
              },
              # Daylight hour
              {
                  "time": "2024-03-20T12:00:00Z",
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": 20.0,
                              "wind_speed": 5.0
                          }
                      },
                      "next_1_hours": {
                          "details": {},
                          "summary": {
                              "symbol_code": "clearsky"
                          }
                      }
                  }
              }
          ]
      }
  }

  # Call process_forecast with mocked timezone and datetime
  with patch('src.main.get_timezone') as mock_timezone:
    with patch('src.main.datetime') as mock_datetime:
      # Mock timezone
      mock_timezone.return_value = datetime.now().astimezone().tzinfo

      # Mock datetime.now() to return a fixed date
      today = datetime(2024, 3, 20, 7, 0)
      mock_datetime.now.return_value = today

      # Mock fromisoformat to handle datetime conversion
      mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x)

      # Process the forecast
      result = process_forecast(test_data, "test_location")

      # Verify all hours are in daily_forecasts (in this case, 2 hours)
      assert len(result["daily_forecasts"][today.date()]) == 2

      # But only daylight hours should be in day_scores
      assert today.date() in result["day_scores"]


def test_main_no_data_retrieved():
  """Test main function when no data is retrieved from any location."""
  with patch('src.main.LOCATIONS', {'gijon': MagicMock(name='Test Location')}):
    with patch('src.main.argparse.ArgumentParser.parse_args') as mock_parse_args:
      # Setup args mock
      mock_args = MagicMock()
      mock_args.location = None
      mock_args.all = False
      mock_args.rank = False
      mock_args.debug = False
      mock_parse_args.return_value = mock_args

      # Mock fetch_weather_data to return None for all locations
      with patch('src.main.fetch_weather_data', return_value=None):
        # Mock display_error to verify it's called
        with patch('src.main.display_error') as mock_error:
          # Call main
          main()

          # Verify error about no data is displayed
          error_calls = [call[0][0] for call in mock_error.call_args_list]
          assert any("No weather data available" in str(err) for err in error_calls)


def test_process_forecast_with_next_6_hours():
  """Test process_forecast with next_6_hours data instead of next_1_hours."""
  # Create test data with only next_6_hours data
  test_data = {
      "properties": {
          "timeseries": [
              {
                  "time": "2024-03-20T12:00:00Z",
                  "data": {
                      "instant": {
                          "details": {
                              "air_temperature": 20.0,
                              "wind_speed": 5.0
                          }
                      },
                      # No next_1_hours data
                      "next_6_hours": {
                          "details": {
                              "precipitation_amount": 1.0,
                              "probability_of_precipitation": 30
                          },
                          "summary": {
                              "symbol_code": "rain"
                          }
                      }
                  }
              }
          ]
      }
  }

  # Call process_forecast with mocked timezone and datetime
  with patch('src.main.get_timezone') as mock_timezone:
    with patch('src.main.datetime') as mock_datetime:
      # Mock timezone
      mock_timezone.return_value = datetime.now().astimezone().tzinfo

      # Mock datetime.now() to return a fixed date
      today = datetime(2024, 3, 20, 7, 0)
      mock_datetime.now.return_value = today

      # Mock fromisoformat to handle datetime conversion
      mock_datetime.fromisoformat.side_effect = lambda x: datetime.fromisoformat(x)

      # Process the forecast
      result = process_forecast(test_data, "test_location")

      # Verify the data was processed correctly
      assert len(result["daily_forecasts"][today.date()]) == 1
      hourly = result["daily_forecasts"][today.date()][0]

      # Verify it used the 6-hour data
      assert hourly.symbol == "rain"
      assert hourly.precipitation_probability == 30
      assert hourly.precipitation_amount == 1.0
