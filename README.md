# Daily Helper

This is a simple helper app that helps you organize your day/week in a more efficient way by providing weather forecasts and planning assistance.

## Features

### Weather Forecast
- Provides 7-day weather forecast for Oviedo, Spain with hourly data
- Shows temperature, wind speed, humidity, and weather conditions for each hour
- Forecasts are based on data from the Norwegian Meteorological Institute (MET Norway)
- Displays comprehensive hourly data for planning your day

### Weekly Planner
The app helps you determine the best days/time ranges for outdoor activities based on the weather forecast for the next 7 days.

### Cooking Planner
TODO

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd daily-helper
```

2. Create and activate a virtual environment:
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/MacOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the weather forecast:
```bash
python main.py
```

The script will display a 7-day hourly forecast for Oviedo, including:
- Hourly temperature in Celsius
- Wind speed in meters per second
- Relative humidity percentage
- Weather conditions

## Dependencies

- Python 3.x
- requests==2.31.0
- pytz==2024.1

## API Information

This project uses the MET Norway Weather API:
- Base URL: https://api.met.no/weatherapi/locationforecast/2.0
- Documentation: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Rate limiting: Please respect the API's rate limits and terms of use

## Contributing

Feel free to submit issues and enhancement requests!