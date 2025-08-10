"""
Tests for data models including HourlyWeather and DailyReport.
"""

from datetime import datetime

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
            precipitation_amount=0.0,
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
            precipitation_amount=0.0,
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
            precipitation_amount=0.0,
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
            precipitation_amount=1.0,
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
            precipitation_amount=2.0,
        ),
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

    # Test warm weather (22°C or higher)
    hours_warm = [
        HourlyWeather(
            time=base_time,
            temp=25,
            precipitation_amount=0.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_warm = DailyReport(test_date, hours_warm, "Test")
    assert report_warm.weather_description == "Warm"

    # Test pleasant weather (18-22°C)
    hours_pleasant = [
        HourlyWeather(
            time=base_time,
            temp=20,
            precipitation_amount=0.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_pleasant = DailyReport(test_date, hours_pleasant, "Test")
    assert report_pleasant.weather_description == "Pleasant"

    # Test cool weather (10-18°C)
    hours_cool = [
        HourlyWeather(
            time=base_time,
            temp=15,
            precipitation_amount=0.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_cool = DailyReport(test_date, hours_cool, "Test")
    assert report_cool.weather_description == "Cool"

    # Test cold weather (below 10°C)
    hours_cold = [
        HourlyWeather(
            time=base_time,
            temp=5,
            precipitation_amount=0.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_cold = DailyReport(test_date, hours_cold, "Test")
    assert report_cold.weather_description == "Cold"

    # Test rainy weather (precipitation > 0.5mm)
    hours_rain = [
        HourlyWeather(
            time=base_time,
            temp=20,
            precipitation_amount=1.5,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_rain = DailyReport(test_date, hours_rain, "Test")
    assert report_rain.weather_description == "Rain (1h)"

    # Test multiple rainy hours
    hours_multiple_rain = [
        HourlyWeather(
            time=base_time,
            temp=20,
            precipitation_amount=1.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        ),
        HourlyWeather(
            time=base_time.replace(hour=9),
            temp=20,
            precipitation_amount=2.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        ),
    ]
    report_multiple_rain = DailyReport(test_date, hours_multiple_rain, "Test")
    assert report_multiple_rain.weather_description == "Rain (2h)"

    # Test weather description with None temperature (fallback to "Mixed")
    hours_none_temp = [
        HourlyWeather(
            time=base_time,
            temp=None,
            precipitation_amount=0.0,
            temp_score=1,
            wind_score=1,
            cloud_score=1,
            precip_amount_score=1,
        )
    ]
    report_none_temp = DailyReport(test_date, hours_none_temp, "Test")
    assert report_none_temp.weather_description == "Mixed"


def test_hourly_weather_score_calculation():
    """Test that HourlyWeather calculates total score correctly."""
    hour = HourlyWeather(
        time=datetime(2024, 3, 15, 10),
        temp_score=5,
        wind_score=-2,
        cloud_score=3,
        precip_amount_score=1,
    )

    assert hour.total_score == 7  # 5 + (-2) + 3 + 1


def test_hourly_weather_hour_extraction():
    """Test that hour is correctly extracted from datetime."""
    test_time = datetime(2024, 3, 15, 14, 30)  # 2:30 PM
    hour = HourlyWeather(time=test_time)

    assert hour.hour == 14
