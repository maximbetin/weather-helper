"""
Tests for data models (HourlyWeather and DailyReport).
Consolidates tests for the core data structures used throughout the application.
"""

import pytest
from datetime import datetime, date
from src.core.models import DailyReport, HourlyWeather


# Tests for DailyReport model
def test_daily_report_empty():
  """Test DailyReport with no daylight hours."""
  test_date = datetime(2024, 3, 15)
  report = DailyReport(test_date, [], "Test Location")

  assert report.date == test_date
  assert report.location_name == "Test Location"
  assert report.avg_score == float('-inf')
  assert report.likely_rain_hours == 0
  assert report.min_temp is None
  assert report.max_temp is None
  assert report.avg_temp is None


def test_daily_report_calculations():
  """Test DailyReport calculations with sample data."""
  # Create test data
  test_date = datetime(2024, 3, 15)
  base_time = datetime(2024, 3, 15, 8)  # Start at 8 AM

  # Create a mix of weather conditions
  hours = [
      HourlyWeather(
          time=base_time,
          temp=20,
          wind=5,
          cloud_coverage=20,
          temp_score=6,
          wind_score=-3,
          cloud_score=3,
          precip_amount_score=4,
          precipitation_amount=0.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=9),
          temp=22,
          wind=6,
          cloud_coverage=30,
          temp_score=6,
          wind_score=-3,
          cloud_score=2,
          precip_amount_score=4,
          precipitation_amount=0.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=10),
          temp=21,
          wind=7,
          cloud_coverage=50,
          temp_score=6,
          wind_score=-3,
          cloud_score=0,
          precip_amount_score=2,
          precipitation_amount=0.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=11),
          temp=19,
          wind=8,
          cloud_coverage=80,
          temp_score=4,
          wind_score=-5,
          cloud_score=-2,
          precip_amount_score=-3,
          precipitation_amount=1.0
      ),
      HourlyWeather(
          time=base_time.replace(hour=12),
          temp=18,
          wind=9,
          cloud_coverage=90,
          temp_score=4,
          wind_score=-5,
          cloud_score=-4,
          precip_amount_score=-6,
          precipitation_amount=2.0
      )
  ]

  report = DailyReport(test_date, hours, "Test Location")

  # Test calculated values
  assert report.date == test_date
  assert report.location_name == "Test Location"
  assert report.likely_rain_hours == 2  # Hours with >0.5mm precipitation

  # Test temperature calculations
  assert report.min_temp == 18
  assert report.max_temp == 22
  assert report.avg_temp == 20  # (20 + 22 + 21 + 19 + 18) / 5

  # Test average score calculation
  expected_scores = [10, 9, 5, -6, -11]  # Sum of individual scores for each hour
  expected_avg = sum(expected_scores) / len(expected_scores)
  assert abs(report.avg_score - expected_avg) < 0.001


def test_daily_report_weather_description():
  """Test weather description generation based on conditions."""
  test_date = datetime(2024, 3, 15)
  base_time = datetime(2024, 3, 15, 8)

  # Test pleasant weather description (based on temperature)
  pleasant_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          temp=20,
          temp_score=6,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=4,
          precipitation_amount=0.0
      )
      for h in range(8, 11)
  ]
  report = DailyReport(test_date, pleasant_hours, "Test Location")
  assert "Pleasant" in report.weather_description

  # Test rainy description (based on precipitation amount)
  rainy_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          temp=18,
          temp_score=4,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=-3,
          precipitation_amount=1.0
      )
      for h in range(8, 10)
  ]
  report = DailyReport(test_date, rainy_hours, "Test Location")
  assert "Rain" in report.weather_description

  # Test warm conditions
  warm_hours = [
      HourlyWeather(
          time=base_time.replace(hour=h),
          temp=25,
          temp_score=4,
          wind_score=0,
          cloud_score=0,
          precip_amount_score=4,
          precipitation_amount=0.0
      )
      for h in range(8, 10)
  ]
  report = DailyReport(test_date, warm_hours, "Test Location")
  assert "Warm" in report.weather_description


# Tests for HourlyWeather model
def test_hourly_weather_score_calculation():
  """Test that HourlyWeather correctly calculates total score."""
  hour = HourlyWeather(
      time=datetime(2024, 3, 15, 12),
      temp=20,
      wind=5,
      cloud_coverage=20,
      precipitation_amount=0,
      temp_score=6,
      wind_score=-3,
      cloud_score=3,
      precip_amount_score=4
  )

  # total_score should be sum of individual scores
  assert hour.total_score == 10  # 6 + (-3) + 3 + 4
  assert hour.hour == 12  # Should extract hour from time


def test_hourly_weather_hour_extraction():
  """Test that hour is correctly extracted from datetime."""
  for h in [0, 6, 12, 18, 23]:
    hour = HourlyWeather(
        time=datetime(2024, 3, 15, h),
        temp=20,
        temp_score=6,
        wind_score=0,
        cloud_score=0,
        precip_amount_score=0
    )
    assert hour.hour == h
