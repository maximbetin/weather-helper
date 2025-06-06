# Weather Helper

This is a weather forecasting tool that helps you find the best times and locations for outdoor activities given the coordinates specified in the `locations.py` file. It provides detailed weather forecasts with activity ratings in a modern graphical user interface (GUI).

## Features

- Weather forecasts for multiple locations
- Location comparison to find the best place for outdoor activities
- Time recommendations for the best weather periods
- Hourly weather details including temperature, wind, and humidity
- Activity rating system that scores weather conditions
- Modern, interactive GUI (no command-line interface)
- Customizable viewing options (daily/hourly forecasts)
- Support for multiple locations with easy configuration
- Detailed weather metrics including temperature, wind speed, and more

## Project Structure

This project follows a modular layout under the `src/` directory to maintain a clean separation between source code, tests, and configuration files.

```graphql
weather-helper/
├── run_gui.py                    # App entry point: launches the Tkinter GUI
│
├── src/                          # All source code for the application
│   │
│   ├── gui/                      # GUI layer (Tkinter code only — no logic!)
│   │   ├── __init__.py
│   │   ├── app.py                # Main GUI class (subclass of tk.Tk), sets up window, widgets
│   │   └── themes.py             # Tkinter styles, themes, fonts, icons
│   │
│   ├── core/                     # Business logic and core functionality (no UI code!)
│   │   ├── __init__.py
│   │   ├── weather_api.py        # Handles HTTP requests and parses weather data from APIs
│   │   ├── daily_report.py       # Generates daily summary from weather data
│   │   ├── hourly_weather.py     # Handles parsing and formatting of hourly forecast data
│   │   ├── locations.py          # Manages saved/favorite locations, location validation
│   │   ├── config.py             # Configuration values (e.g., base URLs, headers, constants)
│   │   └── evaluation.py         # Forecast evaluation, scoring, and ranking logic
│   │
│   └── utils/                    # General-purpose helper functions not tied to core logic
│      ├── __init__.py
│      └── misc.py                # String formatters, error handlers, date utilities, etc.
│
├── assets/                       # Static assets used by the GUI (icons, images, splash screens)
│   └── app_icon.png
│
├── requirements.txt              # List of dependencies (`pip install -r requirements.txt`)
├── README.md                     # Project documentation: how to install, run, develop
├── LICENSE                       # Open-source license file
└── .gitignore                    # Files/folders to exclude from git tracking (e.g., __pycache__)
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/maximbetin/weather-helper.git
cd weather-helper
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

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Run the GUI
To launch the Weather Helper GUI, run:
```bash
python run_gui.py
```

- The GUI will open and allow you to select a location and date, view hourly forecasts, and see the top 5 recommended locations for each day.
- All evaluation and display logic is handled in the GUI.

### Screenshot

![Weather Helper GUI Screenshot](assets/app_screenshot.png)

## Testing

The project uses pytest for testing. To run the tests:

1. Make sure you have all dependencies installed:
```bash
pip install -r requirements.txt
```

2. For coverage reporting, install pytest-cov:
```bash
pip install pytest-cov
```

3. Run all tests:
```bash
pytest
```

4. Run tests with coverage report:
```bash
pytest --cov=src
```

## Dependencies

- Python 3.8 or higher (due to the use of type hints and f-strings)
- `pip` package manager for installing dependencies
- Dependencies are listed in the `requirements.txt` file
- The code runs on Windows, Linux and MacOS

## API Information

This project uses the MET Norway Weather API:
- Base URL: https://api.met.no/weatherapi/locationforecast/2.0
- Documentation: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Rate limiting: Please respect the API's rate limits and terms of use
- The API is free to use and doesn't require authentication
- Data is updated every hour

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.