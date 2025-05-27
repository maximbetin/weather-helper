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

## Project Structure

The project is organized into three main packages:

- **core/**: Core functionality and utilities
  - `config.py`: Configuration settings
  - `core_utils.py`: Core utility functions
  - `main.py`: Main application logic

- **data/**: Data handling and processing
  - `data_models.py`: Data models for weather information
  - `locations.py`: Location definitions
  - `weather_api.py`: API interaction with MET Norway
  - `forecast_processing.py`: Process and analyze weather data
  - `scoring_utils.py`: Weather condition scoring algorithms

- **display/**: User interface and presentation
  - `colors.py`: Terminal color definitions
  - `display_core.py`: Core display functions
  - `display_forecast.py`: Forecast visualization
  - `display_comparison.py`: Location comparison visualization

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
Run the weather forecast for the default location (Gijón):
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

Get direct recommendations for when to go out this week:
```bash
python main.py --recommend
# or shorter form
python main.py -r
```

List all available locations:
```bash
python main.py --list
```

Show hourly forecast instead of daily:
```bash
python main.py --hourly
```

Show additional debug information:
```bash
python main.py --debug
```

## Dependencies

- The necessary dependencies are listed in the `requirements.txt` file.
- Aside from that, you need to have Python 3.10 or higher installed (due to the use of f-strings).
- As well as `pip` to install the dependencies themselves.
- The code runs on Windows, Linux and MacOS.

## API Information

This project uses the MET Norway Weather API:
- Base URL: https://api.met.no/weatherapi/locationforecast/2.0
- Documentation: https://api.met.no/weatherapi/locationforecast/2.0/documentation
- Rate limiting: Please respect the API's rate limits and terms of use

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.