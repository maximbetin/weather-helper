"""Utility functions for weather scoring and analysis."""

from config import WEATHER_SCORES

def temp_score(temp):
    """Rate temperature for outdoor comfort on a scale of -10 to 10."""
    if temp is None or not isinstance(temp, (int, float)):
        return 0

    # Optimal temperature range around 18-24°C
    if 18 <= temp <= 24:
        return 10
    elif 15 <= temp < 18 or 24 < temp <= 28:
        return 8
    elif 10 <= temp < 15 or 28 < temp <= 32:
        return 5
    elif 5 <= temp < 10 or 32 < temp <= 35:
        return 0
    elif 0 <= temp < 5 or 35 < temp <= 38:
        return -5
    else:
        return -10  # Too cold (< 0°C) or too hot (> 38°C)

def wind_score(wind_speed):
    """Rate wind speed comfort on a scale of -10 to 0."""
    if wind_speed is None or not isinstance(wind_speed, (int, float)):
        return 0

    if wind_speed < 2:
        return 0
    elif 2 <= wind_speed < 4:
        return -2
    elif 4 <= wind_speed < 6:
        return -4
    elif 6 <= wind_speed < 10:
        return -6
    else:
        return -10  # Very windy, not pleasant for outdoor activities

def cloud_score(cloud_coverage):
    """Rate cloud coverage for outdoor activities on a scale of -5 to 5."""
    if cloud_coverage is None or not isinstance(cloud_coverage, (int, float)):
        return 0

    # Lower cloud coverage is better for most outdoor activities
    if cloud_coverage < 20:
        return 5  # Nearly clear skies
    elif cloud_coverage < 40:
        return 3  # Mostly clear
    elif cloud_coverage < 60:
        return 1  # Partly cloudy
    elif cloud_coverage < 80:
        return -2  # Mostly cloudy
    else:
        return -5  # Overcast

def uv_score(uv_index):
    """Rate UV index for comfort/safety on a scale of -5 to 5."""
    if uv_index is None or not isinstance(uv_index, (int, float)):
        return 0

    # Moderate UV (3-5) is generally pleasant without excessive sun exposure risk
    if 2 <= uv_index <= 5:
        return 5  # Ideal for outdoor activities
    elif uv_index <= 2:
        return 3  # Low UV, safe but less warmth/light
    elif 5 < uv_index <= 7:
        return 0  # Higher UV, need sun protection
    elif 7 < uv_index <= 10:
        return -3  # Very high, risk of sunburn
    else:
        return -5  # Extreme, avoid midday sun

def precip_probability_score(probability):
    """Rate precipitation probability on a scale of -10 to 0."""
    if probability is None or not isinstance(probability, (int, float)):
        return 0

    # Lower probability is better for outdoor activities
    if probability < 10:
        return 0  # Very unlikely to rain
    elif probability < 30:
        return -2  # Slight chance of rain
    elif probability < 50:
        return -5  # Moderate chance of rain
    elif probability < 70:
        return -7  # High chance of rain
    else:
        return -10  # Very likely to rain

def get_standardized_weather_desc(symbol):
    """Return standardized weather description from symbol code."""
    if not symbol or not isinstance(symbol, str):
        return "Unknown"

    if symbol == "clearsky":
        return "Sunny"
    elif symbol == "fair":
        return "M.Sunny"
    elif symbol == "partlycloudy":
        return "P.Cloudy"
    elif symbol == "cloudy":
        return "Cloudy"
    elif "lightrain" in symbol:
        return "L.Rain"
    elif "heavyrain" in symbol:
        return "H.Rain"
    elif "rain" in symbol:
        return "Rain"
    elif "lightsnow" in symbol:
        return "L.Snow"
    elif "snow" in symbol:
        return "Snow"
    elif "fog" in symbol:
        return "Foggy"
    elif "thunder" in symbol:
        return "Thunder"
    else:
        # Fallback: Capitalize and replace underscores
        return symbol.replace("_", " ").capitalize()

def find_weather_blocks(hours):
    """Find blocks of hours with similar weather conditions."""
    if not hours:
        return []

    # Sort hours by time
    sorted_hours = sorted(hours, key=lambda x: x["hour"])

    blocks = []
    current_block = [sorted_hours[0]]
    current_type = "sunny" if sorted_hours[0]["symbol"] in ["clearsky", "fair"] else "rainy" if "rain" in sorted_hours[0]["symbol"] else "cloudy"

    for hour in sorted_hours[1:]:
        hour_type = "sunny" if hour["symbol"] in ["clearsky", "fair"] else "rainy" if "rain" in hour["symbol"] else "cloudy"

        # If same type, extend the current block
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