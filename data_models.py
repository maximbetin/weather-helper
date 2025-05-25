"""
Defines the data models for HourlyWeather and DailyReport.
"""

# Forward declaration for type hinting, will be imported properly later
# from scoring_utils import get_weather_score, temp_score, wind_score, cloud_score, precip_probability_score
# from forecast_processing import extract_blocks # Needed for DailyReport, if we keep advanced stats there


class HourlyWeather:
  def __init__(self, time, temp, wind, humidity, cloud_coverage, fog, wind_direction, wind_gust, precipitation_amount, precipitation_probability, symbol, weather_score, temp_score, wind_score, cloud_score, precip_prob_score):
    self.time = time
    self.hour = time.hour
    self.temp = temp
    self.wind = wind
    self.humidity = humidity
    self.cloud_coverage = cloud_coverage
    self.fog = fog
    self.wind_direction = wind_direction
    self.wind_gust = wind_gust
    self.precipitation_amount = precipitation_amount
    self.precipitation_probability = precipitation_probability
    self.symbol = symbol
    self.weather_score = weather_score  # Passed in from scoring_utils
    self.temp_score = temp_score  # Passed in from scoring_utils
    self.wind_score = wind_score  # Passed in from scoring_utils
    self.cloud_score = cloud_score  # Passed in from scoring_utils
    self.precip_prob_score = precip_prob_score  # Passed in from scoring_utils
    self.total_score = self._calculate_total_score()

  def _calculate_total_score(self):
    return sum(score for score in [self.weather_score, self.temp_score, self.wind_score, self.cloud_score, self.precip_prob_score] if isinstance(score, (int, float)))


class DailyReport:
  def __init__(self, date, daylight_hours, location_name):
    self.date = date
    self.daylight_hours = daylight_hours  # List of HourlyWeather objects
    self.location_name = location_name
    self.day_name = date.strftime("%A")

    if not daylight_hours:
      self.avg_score = -float('inf')
      self.sunny_hours = 0
      self.partly_cloudy_hours = 0
      self.rainy_hours = 0
      self.likely_rain_hours = 0
      self.avg_precip_prob = None
      self.total_score_sum = 0  # Renamed from total_score to avoid confusion
      self.min_temp = None
      self.max_temp = None
      self.avg_temp = None
      return

    # Scores are already calculated in HourlyWeather objects
    total_weather_score = sum(h.weather_score for h in daylight_hours)
    total_temp_score = sum(h.temp_score for h in daylight_hours)
    total_wind_score = sum(h.wind_score for h in daylight_hours)
    total_cloud_score = sum(h.cloud_score for h in daylight_hours if isinstance(h.cloud_score, (int, float)))
    total_precip_prob_score = sum(h.precip_prob_score for h in daylight_hours if isinstance(h.precip_prob_score, (int, float)))

    self.sunny_hours = sum(1 for h in daylight_hours if h.symbol in ["clearsky", "fair"])
    self.partly_cloudy_hours = sum(1 for h in daylight_hours if h.symbol == "partlycloudy")
    self.rainy_hours = sum(1 for h in daylight_hours if "rain" in h.symbol or "shower" in h.symbol)  # Simplified from original, symbol is already base
    self.likely_rain_hours = sum(1 for h in daylight_hours if isinstance(h.precipitation_probability, (int, float)) and h.precipitation_probability > 30)

    precip_probs = [h.precipitation_probability for h in daylight_hours if isinstance(h.precipitation_probability, (int, float))]
    self.avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else None

    num_hours = len(daylight_hours)
    # Count how many types of scores are available across the daylight hours
    # Assumes weather, temp, and wind scores are always present from HourlyWeather
    has_cloud_scores = any(isinstance(h.cloud_score, (int, float)) for h in daylight_hours)
    has_precip_prob_scores = any(isinstance(h.precip_prob_score, (int, float)) for h in daylight_hours)
    total_available_factors = 3 + (1 if has_cloud_scores else 0) + (1 if has_precip_prob_scores else 0)

    temps = [h.temp for h in daylight_hours if isinstance(h.temp, (int, float))]
    self.min_temp = min(temps) if temps else None
    self.max_temp = max(temps) if temps else None
    self.avg_temp = sum(temps) / len(temps) if temps else None

    self.total_score_sum = (total_weather_score + total_temp_score + total_wind_score + total_cloud_score + total_precip_prob_score)
    self.avg_score = self.total_score_sum / (num_hours * total_available_factors) if num_hours > 0 and total_available_factors > 0 else 0
