"""Utility functions for weather scoring and analysis."""

from config import WEATHER_SCORES

def temp_score(temp):
    """Rate temperature for outdoor comfort on a scale of -10 to 10.

    Args:
        temp: Temperature in Celsius

    Returns:
        int: Score between -10 and 10, where higher is better
    """
    if temp is None or not isinstance(temp, (int, float)):
        return 0

    # Optimal temperature range around 18-24°C
    if 18 <= temp <= 24:
        return 10  # Ideal temperature range
    elif 15 <= temp < 18 or 24 < temp <= 28:
        return 8   # Very comfortable
    elif 10 <= temp < 15 or 28 < temp <= 32:
        return 5   # Acceptable
    elif 5 <= temp < 10 or 32 < temp <= 35:
        return 0   # Not ideal but tolerable
    elif 0 <= temp < 5 or 35 < temp <= 38:
        return -5  # Uncomfortable
    else:
        return -10  # Too cold (< 0°C) or too hot (> 38°C)

def wind_score(wind_speed):
    """Rate wind speed comfort on a scale of -10 to 0.

    Args:
        wind_speed: Wind speed in m/s

    Returns:
        int: Score between -10 and 0, where 0 is no wind (best)
    """
    if wind_speed is None or not isinstance(wind_speed, (int, float)):
        return 0

    if wind_speed < 2:
        return 0       # Calm to light breeze
    elif 2 <= wind_speed < 4:
        return -2      # Light breeze
    elif 4 <= wind_speed < 6:
        return -4      # Moderate breeze
    elif 6 <= wind_speed < 10:
        return -6      # Fresh breeze
    else:
        return -10     # Strong wind or higher

def cloud_score(cloud_coverage):
    """Rate cloud coverage for outdoor activities on a scale of -5 to 5.

    Args:
        cloud_coverage: Percentage of cloud coverage (0-100)

    Returns:
        int: Score between -5 and 5, where higher is better (clearer)
    """
    if cloud_coverage is None or not isinstance(cloud_coverage, (int, float)):
        return 0

    # Lower cloud coverage is better for most outdoor activities
    if cloud_coverage < 20:
        return 5       # Nearly clear skies
    elif cloud_coverage < 40:
        return 3       # Mostly clear
    elif cloud_coverage < 60:
        return 1       # Partly cloudy
    elif cloud_coverage < 80:
        return -2      # Mostly cloudy
    else:
        return -5      # Overcast

def uv_score(uv_index):
    """Rate UV index for comfort/safety on a scale of -5 to 5.

    Args:
        uv_index: UV index value

    Returns:
        int: Score between -5 and 5, where moderate UV (3-5) is best
    """
    if uv_index is None or not isinstance(uv_index, (int, float)):
        return 0

    # Moderate UV (3-5) is generally pleasant without excessive sun exposure risk
    if 2 <= uv_index <= 5:
        return 5       # Ideal for outdoor activities
    elif uv_index <= 2:
        return 3       # Low UV, safe but less warmth/light
    elif 5 < uv_index <= 7:
        return 0       # Higher UV, need sun protection
    elif 7 < uv_index <= 10:
        return -3      # Very high, risk of sunburn
    else:
        return -5      # Extreme, avoid midday sun

def precip_probability_score(probability):
    """Rate precipitation probability on a scale of -10 to 0.

    Args:
        probability: Percentage chance of precipitation (0-100)

    Returns:
        int: Score between -10 and 0, where 0 is no chance of rain (best)
    """
    if probability is None or not isinstance(probability, (int, float)):
        return 0

    # Lower probability is better for outdoor activities
    if probability < 10:
        return 0       # Very unlikely to rain
    elif probability < 30:
        return -2      # Slight chance of rain
    elif probability < 50:
        return -5      # Moderate chance of rain
    elif probability < 70:
        return -7      # High chance of rain
    else:
        return -10     # Very likely to rain

def get_standardized_weather_desc(symbol):
    """Return standardized weather description from symbol code.

    Args:
        symbol: Weather symbol code from API

    Returns:
        str: Short standardized description for display
    """
    if not symbol or not isinstance(symbol, str):
        return "Unknown"

    # Map weather symbols to standardized short descriptions
    weather_map = {
        "clearsky": "Sunny",
        "fair": "M.Sunny",
        "partlycloudy": "P.Cloudy",
        "cloudy": "Cloudy",
        "fog": "Foggy",
    }

    # Return mapped value if exists
    if symbol in weather_map:
        return weather_map[symbol]

    # Handle common pattern-based symbols
    if "lightrain" in symbol:
        return "L.Rain"
    elif "heavyrain" in symbol:
        return "H.Rain"
    elif "rain" in symbol:
        return "Rain"
    elif "lightsnow" in symbol:
        return "L.Snow"
    elif "snow" in symbol:
        return "Snow"
    elif "thunder" in symbol:
        return "Thunder"

    # Fallback: Capitalize and replace underscores
    return symbol.replace("_", " ").capitalize()

def find_weather_blocks(hours):
    """Find blocks of hours with similar weather conditions.

    Groups consecutive hours with similar weather patterns (sunny, rainy, cloudy)
    to identify meaningful time blocks.

    Args:
        hours: List of hourly forecast dictionaries

    Returns:
        list: Tuples of (hour_block, weather_type) where each block contains
              consecutive hours with similar weather
    """
    if not hours:
        return []

    # Sort hours by time
    sorted_hours = sorted(hours, key=lambda x: x["hour"])

    # Weather classification function
    def classify_weather(symbol):
        if symbol in ["clearsky", "fair"]:
            return "sunny"
        elif "rain" in symbol or "snow" in symbol or "sleet" in symbol:
            return "rainy"
        else:
            return "cloudy"

    blocks = []
    current_block = [sorted_hours[0]]
    current_type = classify_weather(sorted_hours[0]["symbol"])

    for hour in sorted_hours[1:]:
        hour_type = classify_weather(hour["symbol"])

        # If same type and consecutive hour, extend the current block
        if hour_type == current_type and hour["hour"] == current_block[-1]["hour"] + 1:
            current_block.append(hour)
        else:
            # Save the completed block and start a new one
            blocks.append((current_block, current_type))
            current_block = [hour]
            current_type = hour_type

    # Add the last block
    blocks.append((current_block, current_type))

    return blocks