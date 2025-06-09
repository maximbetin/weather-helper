# Weather Helper

## Overview

The Weather Helper is a desktop application that provides detailed weather forecasts for various locations. It allows users to compare weather conditions across multiple locations and find the best time for outdoor activities.

## Features

- **Detailed Hourly Forecasts**: Get detailed hourly weather information, including temperature, wind speed, cloud coverage, and precipitation amount.
- **Location Comparison**: Compare weather forecasts for multiple locations side-by-side.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for outdoor activities based on a scoring system.
- **Clean and Intuitive Interface**: A user-friendly graphical interface built with Tkinter.

## Installation and Usage

1. **Clone the repository:**

   ```bash
   git clone https://github.com/maximbetin/weather-helper.git
   cd weather-helper
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install .
   ```

4. **Run the application:**

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
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request