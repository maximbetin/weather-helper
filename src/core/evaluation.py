"""
Evaluation and scoring logic for weather forecasts.
Provides functions to process forecasts, evaluate time blocks, and rank locations for GUI use.
"""

from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Union
import math

from src.core.config import DAYLIGHT_END_HOUR, DAYLIGHT_START_HOUR, FORECAST_DAYS, WEATHER_SYMBOLS
from src.core.hourly_weather import HourlyWeather
from src.core.daily_report import DailyReport
from src.core.enums import WeatherBlockType
from src.core.types import NumericType, T


def _get_value_from_ranges(value: Optional[NumericType], ranges: List[tuple], inclusive: bool = False) -> Optional[T]:
  """Get a value from a list of ranges."""
  if value is None or not isinstance(value, (int, float)):
    return None

  for (range_tuple, result_value) in ranges:
    if range_tuple is None:  # Default case
      return result_value
    low, high = range_tuple
    if inclusive:
      if low <= value <= high:
        return result_value
    else:
      if low <= value < high:
        return result_value
  return ranges[-1][1] if ranges and ranges[-1][0] is None else None


def _calculate_score(value: Optional[NumericType], ranges: List[tuple], inclusive: bool = False) -> int:
  """Calculate score based on a value and a list of ranges."""
  return _get_value_from_ranges(value, ranges, inclusive) or 0


def get_weather_score(symbol: Optional[str]) -> int:
  """Return weather score from symbol code.

  Args:
      symbol: Weather symbol code

  Returns:
      Integer score representing the weather condition quality
  """
  if not symbol or not isinstance(symbol, str):
    return 0
  _, score = WEATHER_SYMBOLS.get(symbol, ("", 0))
  return score


def temp_score(temp: Optional[NumericType]) -> int:
  """Rate temperature for outdoor comfort on a scale of -12 to 6.

  Args:
      temp: Temperature in Celsius

  Returns:
      Integer score representing temperature comfort
  """
  temp_ranges = [
      ((18, 23), 6),    # Ideal temperature (reduced from 8)
      ((15, 18), 4),    # Slightly cool but pleasant (reduced from 6)
      ((23, 26), 4),    # Slightly warm but pleasant (reduced from 6)
      ((10, 15), 2),    # Cool (reduced from 4)
      ((26, 30), 1),    # Warm (reduced from 3)
      ((5, 10), -1),    # Cold (reduced from 0)
      ((30, 33), -3),   # Hot (reduced from -2)
      ((0, 5), -6),     # Very cold (reduced from -5)
      ((33, 36), -6),   # Very hot (reduced from -5)
      ((-5, 0), -9),    # Extremely cold (reduced from -8)
      ((36, 40), -9),   # Extremely hot (reduced from -8)
      (None, -12)       # Beyond extreme temperatures (reduced from -10)
  ]
  return _calculate_score(temp, temp_ranges, inclusive=True)


def wind_score(wind_speed: Optional[NumericType]) -> int:
  """Rate wind speed comfort on a scale of -10 to 0.

  Args:
      wind_speed: Wind speed in m/s

  Returns:
      Integer score representing wind comfort
  """
  wind_ranges = [
      ((0, 1), 0),      # Calm
      ((1, 2), -1),     # Light air
      ((2, 3.5), -2),   # Light breeze
      ((3.5, 5), -3),   # Gentle breeze
      ((5, 8), -5),     # Moderate breeze
      ((8, 10.5), -7),  # Fresh breeze
      ((10.5, 13), -8),  # Strong breeze
      ((13, 15.5), -9),  # Near gale
      (None, -10)       # Gale and above
  ]
  return _calculate_score(wind_speed, wind_ranges)


def cloud_score(cloud_coverage: Optional[NumericType]) -> int:
  """Rate cloud coverage for outdoor activities on a scale of -6 to 4.

  Args:
      cloud_coverage: Cloud coverage percentage (0-100)

  Returns:
      Integer score representing cloud cover impact
  """
  cloud_ranges = [
      ((0, 10), 4),     # Clear (reduced from 5)
      ((10, 25), 2),    # Few clouds (reduced from 3)
      ((25, 50), 0),    # Partly cloudy (reduced from 1)
      ((50, 75), -2),   # Mostly cloudy (unchanged)
      ((75, 90), -4),   # Very cloudy (reduced from -3)
      (None, -6)        # Overcast (reduced from -5)
  ]
  return _calculate_score(cloud_coverage, cloud_ranges)


def precip_probability_score(probability: Optional[NumericType]) -> int:
  """Rate precipitation probability on a scale of -10 to 0.

  Args:
      probability: Precipitation probability percentage (0-100)

  Returns:
      Integer score representing precipitation probability impact
  """
  precip_ranges = [
      ((0, 5), 0),      # Very unlikely
      ((5, 15), -1),    # Unlikely
      ((15, 30), -3),   # Slight chance
      ((30, 50), -5),   # Moderate chance
      ((50, 70), -7),   # Likely
      ((70, 85), -9),   # Very likely
      (None, -10)       # Almost certain
  ]
  return _calculate_score(probability, precip_ranges)


def extract_base_symbol(symbol_code: str) -> str:
  """Extract the base symbol from a symbol code.

  Args:
      symbol_code: The full symbol code (e.g., 'partlycloudy_day')

  Returns:
      str: Base symbol without time of day suffix
  """
  if not symbol_code:
    return "unknown"

  return symbol_code.split('_')[0] if '_' in symbol_code else symbol_code


def get_block_type(hour_obj: HourlyWeather) -> WeatherBlockType:
  """Determine weather block type from hour object.

  Args:
      hour_obj: HourlyWeather object

  Returns:
      WeatherBlockType: The weather type enum
  """
  s = hour_obj.symbol
  if s in ("clearsky", "fair"):
    return WeatherBlockType.SUNNY
  if "rain" in s:
    return WeatherBlockType.RAINY
  return WeatherBlockType.CLOUDY


def get_rating_info(score: Union[int, float, None]) -> str:
  """Return standardized rating description based on score.

  Args:
      score: Numeric score to convert to rating

  Returns:
      Rating text (e.g., 'Excellent', 'Good', etc.)
  """
  if score is None:
    return "N/A"

  rating_ranges = [
      ((12.0, float('inf')), "Excellent"),   # 80% of new max (15 points)
      ((8.0, 12.0), "Very Good"),            # 53-80% of max - more selective
      ((4.0, 8.0), "Good"),                  # 27-53% of max - reasonable threshold
      ((1.0, 4.0), "Fair"),                  # 7-27% of max - low but positive
      (None, "Poor")                         # Below 1.0 is poor
  ]
  return _get_value_from_ranges(score, rating_ranges, inclusive=False) or "N/A"


def _find_best_block(sorted_hours: List[HourlyWeather]) -> Optional[Dict[str, Any]]:
  """Find the best continuous block of weather."""
  best_block = None
  max_score = -float('inf')

  for i in range(len(sorted_hours)):
    for j in range(i, len(sorted_hours)):
      block = sorted_hours[i:j + 1]
      if not block:
        continue

      avg_score = sum(h.total_score for h in block) / len(block)
      duration = len(block)

      if avg_score < 0:
        continue

      duration_factor = 1 + math.log(duration) / 4.0 if duration > 1 else 1
      combined_score = avg_score * duration_factor
      combined_score = min(combined_score, avg_score * 1.5)

      if combined_score > max_score:
        max_score = combined_score
        avg_temp = sum(h.temp for h in block if h.temp is not None) / len(block) if any(h.temp is not None for h in block) else None
        avg_wind = sum(h.wind for h in block if h.wind is not None) / len(block) if any(h.wind is not None for h in block) else None
        symbols = [h.symbol for h in block if h.symbol]
        weather_type = max(set(symbols), key=symbols.count) if symbols else ""

        best_block = {
          'block': block,
          'start': block[0].time,
          'end': block[-1].time,
          'avg_score': avg_score,
          'duration': duration,
          'combined_score': combined_score,
          'weather': weather_type,
          'temp': avg_temp,
          'wind': avg_wind
        }
  return best_block


def find_optimal_weather_block(hours: List[HourlyWeather]) -> Optional[Dict[str, Any]]:
  """Find the optimal weather block for outdoor activities.

  This function identifies the highest scoring continuous block of weather,
  considering both quality and duration.

  Args:
      hours: List of HourlyWeather objects for a given date

  Returns:
      A dictionary containing the best weather block, or None.
  """
  if not hours:
    return None

  sorted_hours = sorted(hours, key=lambda x: x.time)

  return _find_best_block(sorted_hours)


def _create_hourly_weather(entry: Dict[str, Any]) -> HourlyWeather:
  """Create an HourlyWeather object from a forecast timeseries entry."""
  time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))

  instant_details = entry["data"]["instant"]["details"]
  temp = instant_details.get("air_temperature")
  wind = instant_details.get("wind_speed")
  humidity = instant_details.get("relative_humidity")
  cloud_coverage = instant_details.get("cloud_area_fraction")
  fog = instant_details.get("fog_area_fraction")
  wind_direction = instant_details.get("wind_from_direction")
  wind_gust = instant_details.get("wind_speed_of_gust")

  next_1h = entry["data"].get("next_1_hours", {})
  next_1h_details = next_1h.get("details", {})
  precipitation_1h = next_1h_details.get("precipitation_amount")
  precipitation_prob_1h = next_1h_details.get("probability_of_precipitation")

  next_6h = entry["data"].get("next_6_hours", {})
  next_6h_details = next_6h.get("details", {})
  precipitation_prob_6h = next_6h_details.get("probability_of_precipitation")

  precipitation_prob = precipitation_prob_1h if precipitation_prob_1h is not None else precipitation_prob_6h
  final_precipitation_amount = precipitation_1h
  if final_precipitation_amount is None and next_6h_details:
    final_precipitation_amount = next_6h_details.get("precipitation_amount")

  symbol_code = next_1h.get("summary", {}).get("symbol_code")
  if not symbol_code and next_6h.get("summary"):
    symbol_code = next_6h["summary"].get("symbol_code")

  base_symbol = extract_base_symbol(symbol_code) if symbol_code else ""

  return HourlyWeather(
      time=time_utc,
      temp=temp,
      wind=wind,
      humidity=humidity,
      cloud_coverage=cloud_coverage,
      fog=fog,
      wind_direction=wind_direction,
      wind_gust=wind_gust,
      precipitation_amount=final_precipitation_amount,
      precipitation_probability=precipitation_prob,
      symbol=base_symbol,
      weather_score=get_weather_score(base_symbol),
      temp_score=temp_score(temp),
      wind_score=wind_score(wind),
      cloud_score=cloud_score(cloud_coverage),
      precip_prob_score=precip_probability_score(precipitation_prob)
  )


def _process_timeseries(forecast_timeseries: List[Dict[str, Any]]) -> Dict[date, List[HourlyWeather]]:
  """Process forecast timeseries data into a dictionary of daily forecasts."""
  daily_forecasts = defaultdict(list)
  today = datetime.now().date()
  end_date = today + timedelta(days=FORECAST_DAYS)

  for entry in forecast_timeseries:
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    forecast_date = time_utc.date()
    if not (today <= forecast_date < end_date):
      continue

    hourly_weather = _create_hourly_weather(entry)
    daily_forecasts[forecast_date].append(hourly_weather)

  return daily_forecasts


def process_forecast(forecast_data: dict, location_name: str) -> Optional[dict]:
  """Process weather forecast data into daily summaries and hourly blocks."""
  if not forecast_data or 'properties' not in forecast_data or 'timeseries' not in forecast_data['properties']:
    return None

  forecast_timeseries = forecast_data['properties']['timeseries']
  daily_forecasts = _process_timeseries(forecast_timeseries)

  day_scores_reports = {}
  for date, hours_list in daily_forecasts.items():
    daylight_h = [h for h in hours_list if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR]
    if not daylight_h:
      continue
    day_report = DailyReport(datetime.combine(date, datetime.min.time()), daylight_h, location_name)
    day_scores_reports[date] = day_report

  return {
      "daily_forecasts": daily_forecasts,
      "day_scores": day_scores_reports
  }


def get_available_dates(processed_forecast: dict) -> List[date]:
  """Return all available dates for a processed forecast."""
  if not processed_forecast or "daily_forecasts" not in processed_forecast:
    return []
  return sorted(processed_forecast["daily_forecasts"].keys())


def get_time_blocks_for_date(processed_forecast: dict, d: date) -> List[HourlyWeather]:
  """Return all HourlyWeather blocks for a given date."""
  if not processed_forecast or "daily_forecasts" not in processed_forecast:
    return []
  return sorted(processed_forecast["daily_forecasts"].get(d, []), key=lambda h: h.hour)


def get_top_locations_for_date(all_location_processed: Dict[str, dict], d: date, top_n: int = 5) -> List[dict]:
  """Return the top N locations for a given date, sorted by daily score and optimal weather blocks."""
  results = []
  for loc_key, processed in all_location_processed.items():
    day_scores = processed.get("day_scores", {})
    daily_forecasts = processed.get("daily_forecasts", {})

    if d in day_scores:
      report = day_scores[d]

      # Get hourly data for the day to analyze optimal blocks
      hours_for_day = daily_forecasts.get(d, [])

      # Find optimal weather blocks
      optimal_block = find_optimal_weather_block(hours_for_day)

      # Use combined score (quality + duration) if available, otherwise use avg_score
      # Start with the basic average score
      base_score = getattr(report, "avg_score", 0)
      combined_score = base_score

      # If we have an optimal block, use it to calculate a more refined score
      if optimal_block:
        # For very short optimal blocks (less than 3 hours), reduce the score enhancement
        if optimal_block['duration'] < 3:
          combined_score = optimal_block['combined_score'] * 0.85
        else:
          combined_score = optimal_block['combined_score']

      results.append({
          "location_key": loc_key,
          "location_name": getattr(report, "location_name", loc_key),
          "avg_score": getattr(report, "avg_score", 0),
          "combined_score": combined_score,
          "min_temp": getattr(report, "min_temp", None),
          "max_temp": getattr(report, "max_temp", None),
          "weather_description": getattr(report, "weather_description", ""),
          "optimal_block": optimal_block
      })

  # Sort by combined score to prioritize both quality and duration
  results.sort(key=lambda x: x["combined_score"], reverse=True)
  return results[:top_n]
