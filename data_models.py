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
    self.weather_score = weather_score
    self.temp_score = temp_score
    self.wind_score = wind_score
    self.cloud_score = cloud_score
    self.precip_prob_score = precip_prob_score
    self.total_score = self._calculate_total_score()

  def _calculate_total_score(self):
    return sum(score for score in [self.weather_score, self.temp_score, self.wind_score, self.cloud_score, self.precip_prob_score] if isinstance(score, (int, float)))


class DailyReport:
  def __init__(self, date, daylight_hours, location_name):
    self.date = date
    self.daylight_hours = daylight_hours
    self.location_name = location_name
    self.day_name = date.strftime("%A")

    if not daylight_hours:
      self.avg_score = -float('inf')
      self.sunny_hours = 0
      self.partly_cloudy_hours = 0
      self.rainy_hours = 0
      self.likely_rain_hours = 0
      self.avg_precip_prob = None
      self.total_score_sum = 0
      self.min_temp = None
      self.max_temp = None
      self.avg_temp = None
      return

    # Calculate weather condition hours
    self.sunny_hours = sum(1 for h in daylight_hours if h.symbol in ["clearsky", "fair"])
    self.partly_cloudy_hours = sum(1 for h in daylight_hours if h.symbol == "partlycloudy")
    self.rainy_hours = sum(1 for h in daylight_hours if "rain" in h.symbol or "shower" in h.symbol)
    self.likely_rain_hours = sum(1 for h in daylight_hours if isinstance(h.precipitation_probability, (int, float)) and h.precipitation_probability > 30)

    # Calculate precipitation probability average
    precip_probs = [h.precipitation_probability for h in daylight_hours if isinstance(h.precipitation_probability, (int, float))]
    self.avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else None

    # Calculate temperature statistics
    temps = [h.temp for h in daylight_hours if isinstance(h.temp, (int, float))]
    self.min_temp = min(temps) if temps else None
    self.max_temp = max(temps) if temps else None
    self.avg_temp = sum(temps) / len(temps) if temps else None

    # Calculate scores
    num_hours = len(daylight_hours)
    score_types = ["weather_score", "temp_score", "wind_score", "cloud_score", "precip_prob_score"]

    # Count how many score types are available (always at least 3: weather, temp, wind)
    available_score_types = []
    for score_type in score_types:
      if any(isinstance(getattr(h, score_type, None), (int, float)) for h in daylight_hours):
        available_score_types.append(score_type)

    # Calculate total score
    self.total_score_sum = sum(
        getattr(h, score_type)
        for h in daylight_hours
        for score_type in available_score_types
        if isinstance(getattr(h, score_type, None), (int, float))
    )

    # Calculate average score
    self.avg_score = self.total_score_sum / (num_hours * len(available_score_types)) if num_hours > 0 and available_score_types else 0
