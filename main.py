import requests
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import sys

# Coordinates for Oviedo
lat = 43.3619
lon = -5.8494

# Request headers - required by Met.no API
headers = {
    "User-Agent": "DailyHelper/1.0"
}

# API URL
url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={lat}&lon={lon}"

# Fetch data with error handling
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching weather data: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"Error parsing JSON response: {e}")
    sys.exit(1)

# Filter timeseries
forecast = data['properties']['timeseries']

# Organize forecasts by day and hour
madrid_tz = pytz.timezone("Europe/Madrid")
daily_forecasts = defaultdict(list)
today = datetime.now(madrid_tz).date()
end_date = today + timedelta(days=7)

for entry in forecast:
    time_utc = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    local_time = time_utc.astimezone(madrid_tz)
    forecast_date = local_time.date()

    # Only include forecasts for the next 7 days
    if forecast_date >= today and forecast_date < end_date:
        # Extract values with proper error handling
        temp = entry["data"]["instant"]["details"].get("air_temperature", "n/a")
        wind = entry["data"]["instant"]["details"].get("wind_speed", "n/a")
        humidity = entry["data"]["instant"]["details"].get("relative_humidity", "n/a")

        # Get weather symbol with fallbacks
        symbol = entry["data"].get("next_1_hours", {}).get("summary", {}).get("symbol_code",
                 entry["data"].get("next_6_hours", {}).get("summary", {}).get("symbol_code", "n/a"))

        daily_forecasts[forecast_date].append({
            "hour": local_time.hour,
            "time": local_time,
            "temp": temp,
            "wind": wind,
            "humidity": humidity,
            "symbol": symbol
        })

# Print hourly forecasts for each day
print("7-Day Hourly Forecast for Oviedo:")
for date in sorted(daily_forecasts.keys()):
    print(f"\n{date.strftime('%A, %d %b')}")
    print("--------------------------------------------------")
    print("Hour  | Temp (°C) | Wind (m/s) | Humidity | Weather")
    print("--------------------------------------------------")

    # Sort by hour and print each hourly forecast
    for forecast in sorted(daily_forecasts[date], key=lambda x: x["hour"]):
        temp_str = f"{forecast['temp']:6.1f}°" if isinstance(forecast['temp'], (int, float)) else f"{forecast['temp']:8}"
        wind_str = f"{forecast['wind']:9.1f}" if isinstance(forecast['wind'], (int, float)) else f"{forecast['wind']:9}"
        humidity_str = f"{forecast['humidity']:7.1f}%" if isinstance(forecast['humidity'], (int, float)) else f"{forecast['humidity']:8}"

        print(f"{forecast['time'].strftime('%H:%M')} | {temp_str} | {wind_str} | {humidity_str} | {forecast['symbol']}")
