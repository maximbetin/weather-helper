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
│   ├── core/           # Core business logic and data models
│   └── gui/            # GUI components and theming
├── tests/              # Consolidated test suite
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # This file
```

### Core Components

- **`src/core/config.py`**: Configuration constants and utility functions
- **`src/core/models.py`**: Data models (HourlyWeather, DailyReport)
- **`src/core/evaluation.py`**: Weather scoring and analysis logic
- **`src/core/weather_api.py`**: API integration for weather data
- **`src/core/locations.py`**: Location definitions and management
- **`src/gui/app.py`**: Main application window and logic
- **`src/gui/themes.py`**: UI theming and visual styling
- **`src/gui/formatting.py`**: Data formatting for display

## Weather Scoring System

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions for outdoor activities. Each hour receives a total score based on four key factors:

### Individual Component Scores

#### 1. Temperature Score (-12 to +6 points)
Evaluates temperature comfort for outdoor activities:

| Temperature (°C) | Score | Description         |
| ---------------- | ----- | ------------------- |
| 18-23°C          | +6    | Ideal temperature   |
| 15-18°C, 23-26°C | +4    | Pleasant            |
| 10-15°C          | +2    | Cool but acceptable |
| 26-30°C          | +1    | Warm                |
| 5-10°C           | -1    | Cold                |
| 30-33°C          | -3    | Hot                 |
| 0-5°C, 33-36°C   | -6    | Very cold/hot       |
| -5-0°C, 36-40°C  | -9    | Extremely cold/hot  |
| <-5°C, >40°C     | -12   | Beyond extreme      |

#### 2. Wind Score (-10 to 0 points)
Assesses wind comfort (higher wind = lower score):

| Wind Speed (m/s) | Score | Description       |
| ---------------- | ----- | ----------------- |
| 0-2 m/s          | 0     | Calm to light air |
| 2-3.5 m/s        | -1    | Light breeze      |
| 3.5-5 m/s        | -1    | Gentle breeze     |
| 5-8 m/s          | -3    | Moderate breeze   |
| 8-10.5 m/s       | -5    | Fresh breeze      |
| 10.5-13 m/s      | -7    | Strong breeze     |
| 13-15.5 m/s      | -8    | Near gale         |
| >15.5 m/s        | -10   | Gale and above    |

#### 3. Cloud Coverage Score (-4 to +4 points)
Evaluates sky conditions:

| Cloud Coverage | Score | Description   |
| -------------- | ----- | ------------- |
| 0-10%          | +4    | Clear skies   |
| 10-25%         | +3    | Few clouds    |
| 25-50%         | +2    | Partly cloudy |
| 50-75%         | 0     | Mostly cloudy |
| 75-90%         | -2    | Very cloudy   |
| 90-100%        | -4    | Overcast      |

#### 4. Precipitation Score (-15 to +6 points)
Assesses precipitation impact:

| Precipitation (mm) | Score | Description           |
| ------------------ | ----- | --------------------- |
| 0 mm               | +6    | No precipitation      |
| 0-0.1 mm           | +4    | Trace amounts         |
| 0.1-0.5 mm         | +2    | Very light            |
| 0.5-1.0 mm         | 0     | Light drizzle         |
| 1.0-2.5 mm         | -3    | Light rain            |
| 2.5-5.0 mm         | -6    | Moderate rain         |
| 5.0-10.0 mm        | -9    | Heavy rain            |
| 10.0-20.0 mm       | -12   | Very heavy rain       |
| >20.0 mm           | -15   | Extreme precipitation |

### Total Score Calculation

Each hour's **total score** is the sum of all four component scores:
```
Total Score = Temperature Score + Wind Score + Cloud Score + Precipitation Score
```

**Possible range**: -41 to +15 points per hour

### Overall Rating System

The total scores are converted to descriptive ratings:

| Score Range | Rating    |
| ----------- | --------- |
| 12+         | Excellent |
| 8-12        | Very Good |
| 4-8         | Good      |
| 1-4         | Fair      |
| <1          | Poor      |

### Optimal Weather Block Detection

The application also identifies the best continuous time periods:

1. **Quality Filter**: Only considers hours with non-negative scores for multi-hour blocks
2. **Duration Bonus**: Longer consistent periods receive logarithmic bonuses
3. **Consistency Check**: Prioritizes blocks with stable scores (low variance)
4. **Combined Scoring**: Balances quality, duration, and consistency

This system helps users find not just good individual hours, but sustained periods of favorable weather for extended outdoor activities.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.