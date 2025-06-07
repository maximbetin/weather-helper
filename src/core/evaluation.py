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


# Type alias for numeric types
NumericType = Union[int, float]


def _calculate_score(value: Optional[NumericType], ranges: List[tuple], inclusive: bool = False) -> int:
  """Helper to calculate score based on a value and a list of ranges."""
  if value is None or not isinstance(value, (int, float)):
    return 0

  for (range_tuple, score_value) in ranges:
    if range_tuple is None:  # Default case
      return score_value
    low, high = range_tuple
    if inclusive:
      if low <= value <= high:
        return score_value
    else:
      if low <= value < high:
        return score_value
  # Return the score of the last entry if it's a default, otherwise a fallback.
  return ranges[-1][1] if ranges and ranges[-1][0] is None else 0


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
  """Rate temperature for outdoor comfort on a scale of -10 to 8.

  Args:
      temp: Temperature in Celsius

  Returns:
      Integer score representing temperature comfort
  """
  temp_ranges = [
      ((18, 23), 8),    # Ideal temperature
      ((15, 18), 6),    # Slightly cool but pleasant
      ((23, 26), 6),    # Slightly warm but pleasant
      ((10, 15), 4),    # Cool
      ((26, 30), 3),    # Warm
      ((5, 10), 0),     # Cold
      ((30, 33), -2),   # Hot
      ((0, 5), -5),     # Very cold
      ((33, 36), -5),   # Very hot
      ((-5, 0), -8),    # Extremely cold
      ((36, 40), -8),   # Extremely hot
      (None, -10)       # Beyond extreme temperatures
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
  """Rate cloud coverage for outdoor activities on a scale of -5 to 5.

  Args:
      cloud_coverage: Cloud coverage percentage (0-100)

  Returns:
      Integer score representing cloud cover impact
  """
  cloud_ranges = [
      ((0, 10), 5),     # Clear
      ((10, 25), 3),    # Few clouds
      ((25, 50), 1),    # Partly cloudy
      ((50, 75), -2),   # Mostly cloudy
      ((75, 90), -3),   # Very cloudy
      (None, -5)        # Overcast
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


def get_block_type(hour_obj: HourlyWeather) -> str:
  """Determine weather block type from hour object.

  Args:
      hour_obj: HourlyWeather object

  Returns:
      str: Weather type ("sunny", "rainy", or "cloudy")
  """
  s = hour_obj.symbol  # symbol is already base form
  if s in ("clearsky", "fair"):
    return "sunny"
  if "rain" in s:
    return "rainy"
  return "cloudy"


def extract_blocks(hours: List[HourlyWeather], min_block_len: int = 2) -> list:
  """Find consecutive blocks of hours with similar weather type.

  Args:
      hours: List of HourlyWeather objects
      min_block_len: Minimum number of hours to consider a block

  Returns:
      List of (hour_block, weather_type) tuples
  """
  if not hours:
    return []

  # Ensure hours are HourlyWeather objects and sorted
  sorted_hours = sorted(hours, key=lambda x: x.time)  # Sort by full datetime
  blocks = []
  current_block = [sorted_hours[0]]

  current_type = get_block_type(sorted_hours[0])
  for hour_obj in sorted_hours[1:]:
    hour_type = get_block_type(hour_obj)
    # Check for consecutive hours (time difference of 1 hour)
    if hour_type == current_type and (hour_obj.time - current_block[-1].time) == timedelta(hours=1):
      current_block.append(hour_obj)
    else:
      if len(current_block) >= min_block_len:
        blocks.append((current_block, current_type))
      current_block = [hour_obj]
      current_type = hour_type

  # Don't forget the last block
  if len(current_block) >= min_block_len:
    blocks.append((current_block, current_type))

  return blocks


def get_rating_info(score: Union[int, float, None]) -> str:
  """Return standardized rating description based on score.

  Args:
      score: Numeric score to convert to rating

  Returns:
      Rating text (e.g., 'Excellent', 'Good', etc.)
  """
  if score is None:
    return "N/A"
  if score >= 18.0:
    return "Excellent"
  elif score >= 13.0:
    return "Very Good"
  elif score >= 8.0:
    return "Good"
  elif score >= 3.0:
    return "Fair"
  else:
    return "Poor"


def find_optimal_weather_block(hours: List[HourlyWeather]) -> Dict[str, Any]:
  """Find the optimal weather block for outdoor activities.

  This function identifies the highest scoring continuous block of weather,
  considering both quality and duration. It also identifies time ranges to avoid
  due to poor weather conditions.

  Args:
      hours: List of HourlyWeather objects for a given date

  Returns:
      Dict containing:
          - 'optimal_block': Dict with 'start', 'end', 'avg_score', 'duration', 'weather', 'temp', 'wind'
          - 'avoid_ranges': List of Dict with 'start', 'end', 'reason'
  """
  if not hours:
    return {
      'optimal_block': None,
      'avoid_ranges': []
    }

  # Sort hours by time
  sorted_hours = sorted(hours, key=lambda x: x.time)

  # Find continuous blocks with good scores (positive scores)
  good_blocks = []
  current_block = []

  for hour in sorted_hours:
    # Consider positive scores as good for outdoor activities
    if hour.total_score >= 0:
      current_block.append(hour)
    else:
      # End of a good block
      if current_block:
        good_blocks.append(current_block)
        current_block = []

  # Don't forget the last block
  if current_block:
    good_blocks.append(current_block)

  # Identify time ranges to avoid (very poor weather blocks)
  avoid_ranges = []
  current_avoid = []
  for hour in sorted_hours:
    if hour.total_score < -3:
      current_avoid.append(hour)
    else:
      if current_avoid:
        avoid_range = {
          'start': current_avoid[0].time,
          'end': current_avoid[-1].time,
          'reason': current_avoid[0].symbol,
          'duration': len(current_avoid),
          'worst_score': min(h.total_score for h in current_avoid)
        }
        avoid_ranges.append(avoid_range)
        current_avoid = []
  if current_avoid:
    avoid_range = {
      'start': current_avoid[0].time,
      'end': current_avoid[-1].time,
      'reason': current_avoid[0].symbol,
      'duration': len(current_avoid),
      'worst_score': min(h.total_score for h in current_avoid)
    }
    avoid_ranges.append(avoid_range)

  # Score the good blocks based on quality and duration
  scored_blocks = []
  for block in good_blocks:
    if len(block) >= 2:  # Only consider blocks of at least 2 hours
      avg_score = sum(h.total_score for h in block) / len(block)
      duration = len(block)

      # Calculate a combined score that favors both quality and duration
      # Use a more balanced approach to avoid inflating scores too much
      # Scale by log of duration to give diminishing returns for longer durations
      duration_factor = 1 + math.log(duration) / 2.5  # Gentler scaling
      combined_score = avg_score * duration_factor

      # Cap the combined score to avoid unrealistic ratings
      combined_score = min(combined_score, avg_score * 1.8)

      # Calculate average temperature and wind for the block
      avg_temp = sum(h.temp for h in block if h.temp is not None) / \
          len([h for h in block if h.temp is not None]) if any(h.temp is not None for h in block) else None
      avg_wind = sum(h.wind for h in block if h.wind is not None) / \
          len([h for h in block if h.wind is not None]) if any(h.wind is not None for h in block) else None

      # Get the most common weather type
      symbols = [h.symbol for h in block]
      weather_type = ""
      if symbols:
        symbol_counts = {}
        for s in symbols:
          if s:
            symbol_counts[s] = symbol_counts.get(s, 0) + 1
        weather_type = max(symbol_counts.items(), key=lambda x: x[1])[0]

      scored_blocks.append({
        'block': block,
        'start': block[0].time,
        'end': block[-1].time,
        'avg_score': avg_score,
        'duration': duration,
        'combined_score': combined_score,
        'weather': weather_type,
        'temp': avg_temp,
        'wind': avg_wind
      })

  # Find the optimal block
  optimal_block = None
  if scored_blocks:
    # Sort by combined score (higher is better)
    scored_blocks.sort(key=lambda x: x['combined_score'], reverse=True)
    optimal_block = scored_blocks[0]
  else:
    # If no 2+ hour good blocks found, find the single best hour (score >= 0)
    best_single_hour = None
    if sorted_hours:  # Check if there are any hours at all
      # Filter for hours with positive total_score
      positive_score_hours = [h for h in sorted_hours if h.total_score >= 0]
      if positive_score_hours:
        best_single_hour = max(positive_score_hours, key=lambda h: h.total_score)

    if best_single_hour:
      optimal_block = {
        'block': [best_single_hour],
        'start': best_single_hour.time,
        'end': best_single_hour.time,  # End is the same as start for a single hour
        'avg_score': best_single_hour.total_score,
        'duration': 1,
        'combined_score': best_single_hour.total_score,  # Combined score for single hour is just its total score
        'weather': best_single_hour.symbol,
        'temp': best_single_hour.temp,
        'wind': best_single_hour.wind
      }

  return {
    'optimal_block': optimal_block,
    'avoid_ranges': avoid_ranges
  }


def process_forecast(forecast_data: dict, location_name: str) -> Optional[dict]:
  """Process weather forecast data into daily summaries and hourly blocks."""
  if not forecast_data or 'properties' not in forecast_data or 'timeseries' not in forecast_data['properties']:
    return None

  forecast_timeseries = forecast_data['properties']['timeseries']
  daily_forecasts = defaultdict(list)
  today = datetime.now().date()
  end_date = today + timedelta(days=FORECAST_DAYS)

  for entry in forecast_timeseries:
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    local_time = time_utc
    forecast_date = local_time.date()
    if not (today <= forecast_date < end_date):
      continue
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
    hourly_weather = HourlyWeather(
        time=local_time,
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
    daily_forecasts[forecast_date].append(hourly_weather)
  day_scores_reports = {}
  for date, hours_list in daily_forecasts.items():
    daylight_h = [h for h in hours_list if DAYLIGHT_START_HOUR <= h.hour <= DAYLIGHT_END_HOUR]
    if not daylight_h:
      continue
    day_report = DailyReport(date, daylight_h, location_name)
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

      # Find optimal weather blocks and times to avoid
      weather_blocks_info = find_optimal_weather_block(hours_for_day)
      optimal_block = weather_blocks_info.get('optimal_block')
      avoid_ranges = weather_blocks_info.get('avoid_ranges', [])

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

        # If there are times to avoid, slightly reduce the score
        if avoid_ranges:
          combined_score = combined_score * 0.95

      results.append({
          "location_key": loc_key,
          "location_name": getattr(report, "location_name", loc_key),
          "avg_score": getattr(report, "avg_score", 0),
          "combined_score": combined_score,
          "min_temp": getattr(report, "min_temp", None),
          "max_temp": getattr(report, "max_temp", None),
          "weather_description": getattr(report, "weather_description", ""),
          "optimal_block": optimal_block,
          "avoid_ranges": avoid_ranges
      })

  # Sort by combined score to prioritize both quality and duration
  results.sort(key=lambda x: x["combined_score"], reverse=True)
  return results[:top_n]
