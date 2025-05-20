import requests
import json
from datetime import datetime, timedelta

from config import HEADERS, LOCATIONS, API_URL

def get_hourly_forecast(municipality_code):
    if not municipality_code:
        return None

    url_forecast_api = f"{API_URL}/api/prediccion/especifica/municipio/horaria/{municipality_code}"
    response = requests.get(url_forecast_api, headers=HEADERS, verify=True)
    response.raise_for_status()

    # The first response from AEMET gives a URL to the actual data
    data_info = response.json()

    if data_info.get("estado") == 200 and "datos" in data_info:
        data_url = data_info["datos"]

        # Make a new request to the data URL
        data_response = requests.get(data_url, headers=HEADERS, verify=True)
        data_response.raise_for_status()
        forecast_data = data_response.json()
        return forecast_data

def display_hourly_forecast(forecast_data):
    """
    Displays the hourly forecast information in a readable format.
    """
    if not forecast_data or not isinstance(forecast_data, list) or not forecast_data:
        print("No forecast data to display or data is in unexpected format.")
        return

    # The forecast_data is usually a list with one main dictionary
    # that contains the predictions.
    if not isinstance(forecast_data[0], dict) or "prediccion" not in forecast_data[0]:
        print("Forecast data format is not as expected (missing 'prediccion' key).")
        print(f"Received data: {forecast_data[0]}")
        return

    prediction_details = forecast_data[0]["prediccion"]
    days = prediction_details.get("dia", [])

    print(f"\n--- Hourly Weather Forecast for {forecast_data[0].get('nombre', 'N/A')} ---")

    today = datetime.now().date()

    for day_data in days:
        date_str = day_data.get("fecha", "").split("T")[0]
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Only process up to 7 days from today
        if (current_date - today).days >= 7:
            break

        print(f"\nDate: {date_str}")

        # Hourly data is in 'estadoCielo', 'precipitacion', 'temperatura', etc.
        # These are lists where each item corresponds to an hour.

        # We need to find the length of one of these hourly lists to know how many hours are predicted
        # It seems 'temperatura' is a reliable one to check for its presence and length.
        if not day_data.get("temperatura"):
            print("  No temperature data for this day.")
            continue

        num_hours_predicted = len(day_data["temperatura"])

        for hour_index in range(num_hours_predicted):
            hour_str = f"{hour_index:02d}:00" # Format hour as HH:00

            temp_data = day_data.get("temperatura", [])
            temp = temp_data[hour_index].get("value", "N/A") if hour_index < len(temp_data) else "N/A"

            sky_state_data = day_data.get("estadoCielo", [])
            sky_description = sky_state_data[hour_index].get("descripcion", "N/A") if hour_index < len(sky_state_data) else "N/A"

            precip_data = day_data.get("precipitacion", [])
            precipitation_mm = precip_data[hour_index].get("value", "N/A") if hour_index < len(precip_data) else "N/A"

            wind_data = day_data.get("vientoAndRachaMax", [])
            wind_speed = "N/A"
            wind_direction = "N/A"
            if hour_index < len(wind_data) and isinstance(wind_data[hour_index], dict) and 'velocidad' in wind_data[hour_index]:
                 # vientoAndRachaMax can contain multiple 'velocidad' entries for different periods within the hour.
                 # We'll take the first one for simplicity.
                wind_speed_values = wind_data[hour_index].get("velocidad", [])
                wind_speed = wind_speed_values[0] if wind_speed_values else "N/A"
                wind_direction = wind_data[hour_index].get("direccion", ["N/A"])[0]


            humidity_data = day_data.get("humedadRelativa", [])
            humidity = humidity_data[hour_index].get("value", "N/A") if hour_index < len(humidity_data) else "N/A"

            print(f"  {hour_str}: Temp: {temp}°C, Sky: {sky_description}, Precip: {precipitation_mm}mm, Wind: {wind_speed} km/h ({wind_direction}), Humidity: {humidity}%")

if __name__ == "__main__":

    try:
      for location, code in LOCATIONS.items():
          print(f"Fetching forecast for {code}...")
          hourly_data = get_hourly_forecast(code)
          if hourly_data:
              display_hourly_forecast(hourly_data)
    except Exception as e:
        print(f"Error: {e}")
