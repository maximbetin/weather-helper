# Weather Helper

This is a weather forecasting tool that helps you find the best times and locations for outdoor activities given the coordinates specified in the `locations.py` file. It provides detailed weather forecasts with activity ratings.

## Features

- Weather forecasts for multiple locations
- Location comparison to find the best place for outdoor activities
- Time recommendations for the best weather periods
- Hourly weather details including temperature, wind, and precipitation probability
- Activity rating system that scores weather conditions
- Customizable viewing options (daily/hourly forecasts)
- Command-line interface with various filtering options
- Support for multiple locations with easy configuration
- Detailed weather metrics including temperature, wind speed, and precipitation

## Project Structure

This project follows a modular layout under the `src/` directory to maintain a clean separation between source code, tests, and configuration files.

```graphql
weather-helper/
├── main.py                        # App entry point: initializes and runs the Tkinter GUI
│
├── src/                           # All source code for the application
│   │
│   ├── gui/                       # GUI layer (Tkinter code only — no logic!)
│   │   ├── __init__.py            # Marks this as a Python package
│   │   ├── app.py                 # Main GUI class (subclass of tk.Tk), sets up window, widgets
│   │   ├── widgets.py             # Custom/reusable Tkinter components (e.g., input panels, layout frames)
│   │   └── themes.py              # Optional: Tkinter styles, themes, fonts, icons
│   │
│   ├── core/                      # Business logic and core functionality (no UI code!)
│   │   ├── __init__.py            # Marks this as a Python package
│   │   ├── weather_api.py         # Handles HTTP requests and parses weather data from websites/APIs
│   │   ├── daily_report.py        # Generates daily summary from weather data
│   │   ├── hourly_weather.py      # Handles parsing and formatting of hourly forecast data
│   │   ├── locations.py           # Manages saved/favorite locations, location validation
│   │   └── config.py              # Configuration values (e.g., base URLs, headers, constants)
│   │
│   └── utils/                     # General-purpose helper functions not tied to core logic
│      ├── __init__.py
│      └── misc.py                # String formatters, error handlers, date utilities, etc.
│
├── assets/                        # Static assets used by the GUI (icons, images, splash screens)
│   └── app_icon.png
│
├── requirements.txt               # List of dependencies (`pip install -r requirements.txt`)
├── README.md                      # Project documentation: how to install, run, develop
├── LICENSE                        # Open-source license file
└── .gitignore                     # Files/folders to exclude from git tracking (e.g., \_\_pycache\_\_)
```

## VSCode Extensions

This project has been implemented using the following VSCode extensions:

- [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [autopep8](https://marketplace.visualstudio.com/items?itemName=ms-python.autopep8)
- [gitignore](https://marketplace.visualstudio.com/items?itemName=codezombiech.gitignore)
- [Sort lines](https://marketplace.visualstudio.com/items?itemName=Tyriar.sort-lines)
- [Git History](https://marketplace.visualstudio.com/items?itemName=donjayamanne.githistory)
- [IntelliCode](https://marketplace.visualstudio.com/items?itemName=VisualStudioExptTeam.vscodeintellicode)
- [indent-rainbow](https://marketplace.visualstudio.com/items?itemName=oderwat.indent-rainbow)
- [Test Explorer UI](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer)
- [Remove empty lines](https://marketplace.visualstudio.com/items?itemName=aaron-bond.better-comments)
- [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one)
- [Python Test Explorer](https://marketplace.visualstudio.com/items?itemName=hbenl.vscode-test-explorer)
- [Selected Lines Count](https://marketplace.visualstudio.com/items?itemName=aaron-bond.better-comments)
- [Test Adapter Converter](https://marketplace.visualstudio.com/items?itemName=ms-vscode.test-adapter-converter)
- [Coloured Status Bar Problems](https://marketplace.visualstudio.com/items?itemName=bradzacher.vscode-coloured-status-bar-problems)

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

### Basic Usage
Run the weather forecast for the first location in the `locations.py` file:
```bash
python src/main.py
```

### Command-line Arguments

Check a specific location:
```bash
python src/main.py -l gijon
```

Show forecasts for all available locations:
```bash
python src/main.py -a
```

Get direct recommendations for when and where to go out this week:
```bash
python src/main.py -r
```

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

5. Run a specific test file:
```bash
pytest tests/test_weather_api.py
```

6. Run tests with verbose output:
```bash
pytest -v
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