# Daily Helper

This is a weather forecasting tool that helps you find the best times and locations for outdoor activities in Asturias, Spain by providing detailed weather forecasts with activity ratings.

## Features

### Weather Forecast
- Provides 7-day weather forecast for multiple locations in Asturias with detailed ratings
- Shows temperature ranges, weather conditions, and best/worst time blocks for outdoor activities
- Forecasts are based on data from the Norwegian Meteorological Institute (MET Norway)
- Supports all major locations in Asturias including Oviedo, Gijón, Llanes, and more

### Location Comparison
- Compare weather conditions across multiple Asturian locations
- Quickly identify the best place for outdoor activities on a specific day
- Sort locations by overall rating from best to worst
- See at-a-glance summaries with temperature ranges and dominant weather patterns

### Activity Planning
The app helps you determine the best days and time ranges for outdoor activities:
- Analyzes temperature, wind conditions, precipitation probability, and weather patterns
- Rates each day for outdoor suitability (Excellent, Good, Fair, Poor, Avoid)
- Identifies specific time blocks that offer the best outdoor conditions
- Highlights periods to avoid when applicable
- Focuses on daylight hours (8:00-20:00) for optimal activity scheduling

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

### Basic Usage
Run the weather forecast for the default location (Oviedo):
```bash
python main.py
```

### Command-line Arguments

Check a specific location:
```bash
python main.py --location gijon
# or shorter form
python main.py -l llanes
```

Show forecasts for all available locations:
```bash
python main.py --all
# or shorter form
python main.py -a
```

Compare all locations to find the best place for outdoor activities:
```bash
python main.py --compare
# or shorter form
python main.py -c
```

Compare all locations for a specific date:
```bash
python main.py --compare --date 2024-07-15
# or shorter form
python main.py -c -d 2024-07-15
```

List all available locations:
```bash
python main.py --list
```

Don't clear the screen before displaying results:
```bash
python main.py --no-clear
```

## Available Locations

The application includes weather data for these Asturian locations:
- Oviedo
- Gijón
- Llanes
- Ribadesella
- Tapia de Casariego
- Avilés
- Cangas de Onís
- Lagos de Covadonga
- Somiedo
- Teverga
- Taramundi

## Dependencies

- Python 3.x
- requests==2.31.0
- pytz==2024.1
- colorama==0.4.6

## API Information

This project uses the MET Norway Weather API:
- Base URL: https://api.met.no/weatherapi/locationforecast/2.0
- Documentation: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Rate limiting: Please respect the API's rate limits and terms of use

## Contributing

Feel free to submit issues and enhancement requests!