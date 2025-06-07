# Weather Helper

## Overview

The Weather Helper is a desktop application that provides detailed weather forecasts for various locations. It allows users to compare weather conditions across multiple locations and find the best time for outdoor activities.

## Features

- **Detailed Hourly Forecasts**: Get detailed hourly weather information, including temperature, wind speed, humidity, and precipitation probability.
- **Location Comparison**: Compare weather forecasts for multiple locations side-by-side.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for outdoor activities based on a scoring system.
- **Clean and Intuitive Interface**: A user-friendly graphical interface built with Tkinter.

## Project Structure

The project is organized into the following directories:

- `src/`: Contains the main source code for the application.
  - `core/`: Core logic, including weather data processing, evaluation, and data models.
  - `gui/`: GUI components, including the main application window and custom themes.
  - `utils/`: Utility functions used across the application.
- `tests/`: Contains all the unit tests for the project.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/weather-helper.git
   cd weather-helper
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command from the root directory:

```bash
python main.py
```

## Running the Tests

To run the unit tests, use `pytest`:

```bash
pytest
```

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/maximbetin/weather-helper.git
   cd weather-helper
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python weather_helper.py
   ```

## Testing

The project uses pytest for testing. To run the tests:

```bash
pytest
```

The test suite includes:
- Unit tests for core functionality
- API integration tests (mocked)
- Data processing tests

## Building Executables

The application can be built into standalone executables using PyInstaller:

```bash
pyinstaller --onefile --windowed weather_helper.py
```

The executable will be created in the `dist` directory.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

[![Build and Release Executable](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml)

- Tests are run on every PR
- When a PR is merged to main:
  - Tests are run on Windows
  - Executables are built for Windows
  - A new release is created with the executables

## Project Structure

```
weather-helper/
├── src/
│   ├── core/           # Core business logic
│   ├── gui/            # GUI components
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── .github/            # GitHub Actions workflows
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.