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

## Unified Scoring Mechanism

The application employs a unified scoring mechanism to provide consistent weather assessments across all its features. This ensures that recommendations and rankings are based on a single, reliable source of truth for how "good" the weather is at any given time.

### Core Hourly Score

The foundation of the scoring system is the `HourlyWeather.total_score`. This score is calculated for each hour of the weather forecast and represents an overall assessment of weather conditions for that specific hour.

The `total_score` is a sum of several component scores, each evaluating a different aspect of the weather:

*   **`weather_score`**: Derived from the weather symbol (e.g., "clearsky", "rain", "cloudy"). Clearer conditions generally receive higher scores.
*   **`temp_score`**: Assesses the comfort level of the air temperature.
*   **`wind_score`**: Evaluates the pleasantness of the wind speed (e.g., light breezes are preferred over strong winds).
*   **`cloud_score`**: Considers the impact of cloud coverage.
*   **`precip_prob_score`**: Factors in the probability of precipitation; lower probabilities score higher.

These individual component scores are determined by dedicated functions (primarily in `src/utils.py`) that interpret the raw forecast data.

### How Features Utilize the Unified Score

Different features of the Weather Helper leverage this core `HourlyWeather.total_score` in ways appropriate to their purpose:

*   **Hourly Forecast Display**: When viewing the detailed hourly forecast for a location (either by default or with the `-a` flag), the displayed rating for each hour directly reflects its `total_score`.
*   **Daily Rankings (`-r` flag)**: The daily ranking feature calculates an `avg_score` for each day. This is achieved by averaging the `total_score` of all daylight hours (as defined in `src/config.py`) for that day. Locations are then ranked based on these daily average scores.
*   **Best Times Recommendation**: This feature (default behavior or when using `-r` for detailed recommendations within ranked days) identifies continuous blocks of hours with favorable weather conditions. The "goodness" of these blocks is also determined by averaging the `total_score` of the constituent hours.

This centralized approach means that any adjustments to the scoring logic (e.g., changing how temperature affects the score) are made in one place and consistently propagate throughout all parts of the application, ensuring maintainability and reliability.

## Project Structure

This project follows a modular layout under the `src/` directory to maintain a clean separation between source code, tests, and configuration files.

```markdown
weather-helper/
│
├── src/                          # All source code for the application
│   │
│   ├── main.py                   # App entry point: initializes and runs the Tkinter GUI
│   │
│   ├── gui/                      # GUI layer (Tkinter code only — no logic!)
│   │   ├── \_\_init\_\_.py           # Marks this as a Python package
│   │   ├── app.py                # Main GUI class (subclass of tk.Tk), sets up window, widgets
│   │   ├── widgets.py            # Custom/reusable Tkinter components (e.g., input panels, layout frames)
│   │   └── themes.py             # Optional: Tkinter styles, themes, fonts, icons
│   │
│   ├── core/                     # ⚙ Business logic and core functionality (no UI code!)
│   │   ├── \_\_init\_\_.py           # Marks this as a Python package
│   │   ├── weather_api.py        # Handles HTTP requests and parses weather data from websites/APIs
│   │   ├── daily_report.py       # Generates daily summary from weather data
│   │   ├── hourly_weather.py     # Handles parsing and formatting of hourly forecast data
│   │   ├── locations.py          # Manages saved/favorite locations, location validation
│   │   └── config.py             # Configuration values (e.g., base URLs, headers, constants)
│   │
│   ├── utils/                    # General-purpose helper functions not tied to core logic
│   │   ├── \_\_init\_\_.py
│   │   └── misc.py               # String formatters, error handlers, date utilities, etc.
│
├── tests/                        # Automated tests for all modules
│   │
│   ├── \_\_init\_\_.py
│   ├── test_main.py              # Basic test for app startup / entry point
│   │
│   ├── gui/                      # GUI-specific unit/integration tests (if any)
│   │   ├── test_app.py           # Tests for GUI logic, widget loading, etc.
│   │   └── test_widgets.py       # Tests for any custom GUI widgets
│   │
│   ├── core/                     # Unit tests for the core logic layer
│   │   ├── test_weather_api.py
│   │   ├── test_daily_report.py
│   │   ├── test_hourly_weather.py
│   │   ├── test_locations.py
│   │   └── test_config.py
│   │
│   └── utils/                    # Tests for utility functions
│       └── test_misc.py
│
├── assets/                       # Static assets used by the GUI (icons, images, splash screens)
│   └── app_icon.png
│
├── requirements.txt              # List of dependencies (`pip install -r requirements.txt`)
├── README.md                     # Project documentation: how to install, run, develop
├── LICENSE                       # Open-source license file
├── .gitignore                    # Files/folders to exclude from git tracking (e.g., \_\_pycache\_\_)
├── pytest.ini                    # Pytest configuration (e.g., addopts, test paths)
└── .coverage                     # Code coverage report file (generated after running tests)
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