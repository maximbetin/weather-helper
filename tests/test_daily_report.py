import pytest
from datetime import datetime, date
from src.core.daily_report import DailyReport
from src.core.hourly_weather import HourlyWeather


def test_daily_report_empty():
  # Test with no daylight hours
  test_date = datetime(2024, 3, 15)
  report = DailyReport(test_date, [], "Test Location")

  assert report.date == test_date
  assert report.location_name == "Test Location"
  assert report.avg_score == float('-inf')
  assert report.sunny_hours == 0
  assert report.partly_cloudy_hours == 0
  assert report.rainy_hours == 0
  assert report.likely_rain_hours == 0
  assert report.avg_precip_prob is None
  assert report.min_temp is None
  assert report.max_temp is None
  assert report.avg_temp is None


def test_daily_report_calculations():
  # Create test data
  test_date = datetime(2024, 3, 15)
  base_time = datetime(2024, 3, 15, 8)  # Start at 8 AM

  # Create a mix of weather conditions
  hours = [
      # Sunny hours
      HourlyWeather(
          time=base_time,
          temp=20,
          wind=5,
          humidity=60,
          cloud_coverage=20,
          symbol="clearsky",
          weather_score=7,
          temp_score=8,
          wind_score=9,
          cloud_score=10,
          precip_amount_score=10,
          precipitation_amount=0.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=9),
          temp=22,
          wind=6,
          humidity=55,
          cloud_coverage=30,
          symbol="fair",
          weather_score=5,
          temp_score=9,
          wind_score=8,
          cloud_score=9,
          precip_amount_score=10,
          precipitation_amount=0.0
      ),
      # Partly cloudy hours
      HourlyWeather(
          time=base_time.replace(hour=10),
          temp=21,
          wind=7,
          humidity=65,
          cloud_coverage=50,
          symbol="partlycloudy",
          weather_score=3,
          temp_score=7,
          wind_score=7,
          cloud_score=7,
          precip_amount_score=8,
          precipitation_amount=0.0
      ),
      # Rainy hours
      HourlyWeather(
          time=base_time.replace(hour=11),
          temp=19,
          wind=8,
          humidity=75,
          cloud_coverage=80,
          symbol="lightrain",
          weather_score=-3,
          temp_score=6,
          wind_score=6,
          cloud_score=5,
          precip_amount_score=5,
          precipitation_amount=1.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=12),
          temp=18,
          wind=9,
          humidity=80,
          cloud_coverage=90,
          symbol="rain",
          weather_score=-6,
          temp_score=5,
          wind_score=5,
          cloud_score=4,
          precip_amount_score=4,
          precipitation_amount=2.0
      )
  ]

  report = DailyReport(test_date, hours, "Test Location")

  # Test calculated values
  assert report.date == test_date
  assert report.location_name == "Test Location"
  assert report.sunny_hours == 2
  assert report.partly_cloudy_hours == 1
  assert report.rainy_hours == 2
  assert report.likely_rain_hours == 2  # Hours with >0.5mm precipitation

  # Test temperature calculations
  assert report.min_temp == 18
  assert report.max_temp == 22
  assert report.avg_temp == 20  # (20 + 22 + 21 + 19 + 18) / 5

  # Test precipitation probability - no longer used
  assert report.avg_precip_prob is None

  # Test average score calculation
  expected_scores = [
      7 + 8 + 9 + 10 + 10,  # clearsky
      5 + 9 + 8 + 9 + 10,   # fair
      3 + 7 + 7 + 7 + 8,    # partlycloudy
      -3 + 6 + 6 + 5 + 5,   # lightrain
      -6 + 5 + 5 + 4 + 4    # rain
  ]
  expected_avg = sum(expected_scores) / len(expected_scores)
  assert abs(report.avg_score - expected_avg) < 0.001  # Allow for floating point imprecision


def test_daily_report_weather_description():
  test_date = datetime(2024, 3, 15)
  base_time = datetime(2024, 3, 15, 8)

  # Test sunny description
  sunny_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          symbol="clearsky",
          weather_score=7,
          temp_score=0,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=0
      )
      for h in range(8, 11)
  ]
  report = DailyReport(test_date, sunny_hours, "Test Location")
  assert "Sunny" in report.weather_description

  # Test rainy description
  rainy_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          symbol="lightrain",
          weather_score=-3,
          temp_score=0,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=0
      )
      for h in range(8, 10)
  ]
  report = DailyReport(test_date, rainy_hours, "Test Location")
  assert "Rain" in report.weather_description

  # Test mixed conditions
  mixed_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          symbol="partlycloudy",
          weather_score=3,
          temp_score=0,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=0
      )
      for h in range(8, 10)
  ]
  report = DailyReport(test_date, mixed_hours, "Test Location")
  assert "Partly Cloudy" in report.weather_description
