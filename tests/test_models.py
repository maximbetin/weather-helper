"""
Tests for data models including HourlyWeather and DailyReport.
"""

from datetime import datetime

import pytest

from src.core.models import DailyReport, HourlyWeather


def test_daily_report_empty():
    """Test DailyReport with empty daylight hours."""
    test_date = datetime(2024, 3, 15)
    report = DailyReport(test_date, [], "Test Location")

    assert report.date == test_date
    assert report.location_name == "Test Location"
    assert report.avg_score == -float("inf")
    assert report.likely_rain_hours == 0
    assert report.min_temp is None
    assert report.max_temp is None
    assert report.avg_temp is None


def test_daily_report_calculations(create_hour):
    """Test DailyReport calculations with sample data."""
    # Create test data
    test_date = datetime(2024, 3, 15)
    base_time = datetime(2024, 3, 15, 8)  # Start at 8 AM

    hours = [
        create_hour(base_time, temp=20, wind=5, cloud_coverage=20, precipitation_amount=0.0,
                    temp_score=6, wind_score=-3, cloud_score=3, precip_amount_score=4),
        create_hour(base_time.replace(hour=9), temp=22, wind=6, cloud_coverage=30, precipitation_amount=0.0,
                    temp_score=6, wind_score=-3, cloud_score=2, precip_amount_score=4),
        create_hour(base_time.replace(hour=10), temp=21, wind=7, cloud_coverage=50, precipitation_amount=0.0,
                    temp_score=6, wind_score=-3, cloud_score=0, precip_amount_score=2),
        create_hour(base_time.replace(hour=11), temp=19, wind=8, cloud_coverage=80, precipitation_amount=1.0,
                    temp_score=4, wind_score=-5, cloud_score=-2, precip_amount_score=-3),
        create_hour(base_time.replace(hour=12), temp=18, wind=9, cloud_coverage=90, precipitation_amount=2.0,
                    temp_score=4, wind_score=-5, cloud_score=-4, precip_amount_score=-6),
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


@pytest.mark.parametrize(
    "temp, precip_list, expected_desc",
    [
        (25, [0.0], "Warm"),            # Warm weather (22°C or higher)
        (20, [0.0], "Pleasant"),        # Pleasant weather (18-22°C)
        (15, [0.0], "Cool"),            # Cool weather (10-18°C)
        (5, [0.0], "Cold"),             # Cold weather (below 10°C)
        (20, [1.5], "Rain (1h)"),       # Rainy weather (precipitation > 0.5mm)
        (20, [1.0, 2.0], "Rain (2h)"),  # Multiple rainy hours
        (None, [0.0], "Mixed"),         # None temperature
    ],
)
def test_daily_report_weather_description_parametrized(temp, precip_list, expected_desc, create_hour):
    """Test weather description generation based on conditions."""
    test_date = datetime(2024, 3, 15)
    base_time = datetime(2024, 3, 15, 8)

    hours = []
    for i, precip in enumerate(precip_list):
        hours.append(
            create_hour(
                time=base_time.replace(hour=8+i),
                temp=temp,
                precipitation_amount=precip,
                total_score=4 # Gives 1, 1, 1, 1
            )
        )

    report = DailyReport(test_date, hours, "Test")
    assert report.weather_description == expected_desc


def test_hourly_weather_score_calculation(create_hour):
    """Test that HourlyWeather calculates total score correctly."""
    hour = create_hour(
        time=datetime(2024, 3, 15, 10),
        temp_score=5,
        wind_score=-2,
        cloud_score=3,
        precip_amount_score=1,
    )

    assert hour.total_score == 7  # 5 + (-2) + 3 + 1


def test_hourly_weather_hour_extraction(create_hour):
    """Test that hour is correctly extracted from datetime."""
    test_time = datetime(2024, 3, 15, 14, 30)  # 2:30 PM
    hour = create_hour(time=test_time)

    assert hour.hour == 14
