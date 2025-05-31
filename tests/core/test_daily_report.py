from datetime import datetime

import pytest

from src.core.daily_report import DailyReport
from src.core.hourly_weather import HourlyWeather


@pytest.fixture
def sample_date():
  """Fixture providing a sample date."""
  return datetime(2024, 3, 20)


@pytest.fixture
def sample_hourly_weathers():
  """Fixture providing a list of sample HourlyWeather instances."""
  return [
      HourlyWeather(
          time=datetime(2024, 3, 20, 8, 0),
          temp=15.0,
          wind=5.0,
          symbol="clearsky",
          weather_score=10,
          temp_score=8,
          wind_score=9,
          cloud_score=10,
          precip_prob_score=10,
          precipitation_probability=10
      ),
      HourlyWeather(
          time=datetime(2024, 3, 20, 12, 0),
          temp=20.0,
          wind=8.0,
          symbol="partlycloudy",
          weather_score=7,
          temp_score=9,
          wind_score=7,
          cloud_score=7,
          precip_prob_score=10,
          precipitation_probability=20
      ),
      HourlyWeather(
          time=datetime(2024, 3, 20, 16, 0),
          temp=18.0,
          wind=12.0,
          symbol="rain",
          weather_score=4,
          temp_score=8,
          wind_score=5,
          cloud_score=4,
          precip_prob_score=2,
          precipitation_probability=80
      )
  ]


def test_empty_report_initialization(sample_date):
  """Test initialization of an empty report."""
  report = DailyReport(sample_date, [], "Test Location")

  assert report.date == sample_date
  assert report.location_name == "Test Location"
  assert report.day_name == "Wednesday"
  assert report.avg_score == -float('inf')
  assert report.sunny_hours == 0
  assert report.partly_cloudy_hours == 0
  assert report.rainy_hours == 0
  assert report.likely_rain_hours == 0
  assert report.avg_precip_prob is None
  assert report.min_temp is None
  assert report.max_temp is None
  assert report.avg_temp is None


def test_report_with_weather_data(sample_date, sample_hourly_weathers):
  """Test report initialization with weather data."""
  report = DailyReport(sample_date, sample_hourly_weathers, "Test Location")

  # Test weather condition counts
  assert report.sunny_hours == 1
  assert report.partly_cloudy_hours == 1
  assert report.rainy_hours == 1

  # Test temperature calculations
  assert report.min_temp == 15.0
  assert report.max_temp == 20.0
  assert report.avg_temp == pytest.approx(17.67, rel=1e-2)

  # Test precipitation probability
  assert report.avg_precip_prob == pytest.approx(36.67, rel=1e-2)
  assert report.likely_rain_hours == 1  # Only one hour has >30% probability


def test_report_with_invalid_data(sample_date):
  """Test report initialization with invalid weather data."""
  hourly_weathers = [
      HourlyWeather(
          time=datetime(2024, 3, 20, 8, 0),
          temp=None,  # Invalid temperature
          wind=None,  # Invalid wind
          symbol="clearsky",
          weather_score=10,
          temp_score=8,
          wind_score=9,
          cloud_score=10,
          precip_prob_score=10,
          precipitation_probability=None  # Invalid precipitation probability
      )
  ]

  report = DailyReport(sample_date, hourly_weathers, "Test Location")

  assert report.min_temp is None
  assert report.max_temp is None
  assert report.avg_temp is None
  assert report.avg_precip_prob is None
  assert report.likely_rain_hours == 0


def test_weather_description(sample_date, sample_hourly_weathers):
  """Test weather description generation."""
  report = DailyReport(sample_date, sample_hourly_weathers, "Test Location")
  description = report.weather_description

  # Since we have one rainy hour, the description should be "Rain (1h)"
  assert description == "Rain (1h)"


def test_weather_description_no_rain(sample_date):
  """Test weather description generation with no rain."""
  hourly_weathers = [
      HourlyWeather(
          time=datetime(2024, 3, 20, 8, 0),
          temp=15.0,
          wind=5.0,
          symbol="clearsky",
          weather_score=10,
          temp_score=8,
          wind_score=9,
          cloud_score=10,
          precip_prob_score=10,
          precipitation_probability=10
      ),
      HourlyWeather(
          time=datetime(2024, 3, 20, 12, 0),
          temp=20.0,
          wind=8.0,
          symbol="partlycloudy",
          weather_score=7,
          temp_score=9,
          wind_score=7,
          cloud_score=7,
          precip_prob_score=10,
          precipitation_probability=20
      )
  ]

  report = DailyReport(sample_date, hourly_weathers, "Test Location")
  description = report.weather_description

  # With no rain, it should show the dominant condition
  assert description == "Sunny"


def test_weather_description_with_precip_warning(sample_date):
  """Test weather description with high precipitation probability."""
  hourly_weathers = [
      HourlyWeather(
          time=datetime(2024, 3, 20, 8, 0),
          temp=15.0,
          wind=5.0,
          symbol="clearsky",
          weather_score=10,
          temp_score=8,
          wind_score=9,
          cloud_score=10,
          precip_prob_score=10,
          precipitation_probability=45  # High precipitation probability
      )
  ]

  report = DailyReport(sample_date, hourly_weathers, "Test Location")
  description = report.weather_description

  # Should include precipitation warning
  assert description == "Sunny - 45% rain"


def test_score_calculation(sample_date, sample_hourly_weathers):
  """Test average score calculation."""
  report = DailyReport(sample_date, sample_hourly_weathers, "Test Location")

  # Calculate expected average score
  expected_scores = [47, 40, 23]  # Sum of individual scores for each hour
  expected_avg = sum(expected_scores) / len(expected_scores)

  assert report.avg_score == pytest.approx(expected_avg, rel=1e-2)
