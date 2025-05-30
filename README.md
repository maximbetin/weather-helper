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

The project's Python code is found in the `src` directory:

- **src/**: Source code of the application
  - `main.py`: Main entry point and CLI interface
  - `config.py`: Configuration settings
  - `utils.py`: Utility functions
  - `weather_api.py`: API interaction with MET Norway
  - `locations.py`: Location definitions
  - `daily_report.py`: Daily weather report generation
  - `hourly_weather.py`: Hourly weather data handling
  - `__init__.py`: Package initialization file

Additional project files:
- `requirements.txt`: Project dependencies
- `pytest.ini`: Test configuration
- `tests/`: Test suite directory
- `LICENSE`: MIT License file
- `.gitignore`: Git ignore rules

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