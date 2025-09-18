# Weather Helper

[![Build Executable](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml)

## Overview

The Weather Helper is a desktop application that provides detailed weather forecasts for various
locations. It allows users to compare weather conditions across multiple locations and find the best
time for outdoor activities.

## Features

- **Detailed Hourly Forecasts**: Get detailed hourly weather information, including temperature,
  wind speed, cloud coverage, precipitation amount, and relative humidity.
- **Location Comparison**: Compare weather forecasts for multiple locations side-by-side.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for outdoor activities
  based on a comprehensive scoring system that considers temperature, wind, clouds, precipitation,
  and humidity.
- **Clean and Intuitive Interface**: A user-friendly graphical interface built with Tkinter.
- **Comprehensive Data Display**: View all weather parameters including humidity in an organized
  table format.

## Installation and Usage

1. **Clone the repository**:

```bash
git clone https://github.com/maximbetin/weather-helper.git
cd weather-helper
```

2. **Create a virtual environment (recommended)**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

```bash
pip install .
```

4. **Run the application**:

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

- Tests are run on every commit
- When a commit is pushed to main:
  - Tests are run on Windows
  - Executables are built for Windows
  - A new release is created with the executables

## Project Structure

```bash
weather-helper/
├── src/
│   ├── core/           # Core business logic and data models
│   └── gui/            # GUI components and theming
├── tests/              # Test suite
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

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions for outdoor
activities. Each hour receives a total score based on five key factors.

### Individual Component Scores

#### 1. Temperature Score (-15 to +7 points)

Evaluates temperature comfort for outdoor activities:

| Temperature (°C) | Score | Description         |
| ---------------- | ----- | ------------------- |
| 20-24°C          | +7    | Ideal temperature   |
| 17-20°C, 24-27°C | +6    | Very pleasant       |
| 15-17°C, 27-30°C | +4    | Comfortable         |
| 10-15°C          | +2    | Cool but acceptable |
| 30-33°C          | +1    | Hot but manageable  |
| 5-10°C           | -1    | Cold                |
| 33-36°C          | -3    | Very hot            |
| 0-5°C            | -6    | Very cold           |
| 36-40°C, -5-0°C  | -9    | Extremely hot/cold  |
| <-5°C, >40°C     | -15   | Beyond extreme      |

#### 2. Wind Score (-8 to +2 points)

Assesses wind comfort for outdoor activities:

| Wind Speed (m/s) | Score | Description             |
| ---------------- | ----- | ----------------------- |
| 1-3 m/s          | +2    | Light breeze (ideal)    |
| 0-1 m/s          | +1    | Calm (good)             |
| 3-5 m/s          | 0     | Gentle breeze (neutral) |
| 5-8 m/s          | -2    | Moderate breeze         |
| 8-12 m/s         | -4    | Fresh breeze            |
| 12-16 m/s        | -6    | Strong breeze           |
| 16-20 m/s        | -7    | Near gale               |
| >20 m/s          | -8    | Gale and above          |

#### 3. Cloud Coverage Score (-3 to +4 points)

Evaluates sky conditions for outdoor activities:

| Cloud Coverage | Score | Description                     |
| -------------- | ----- | ------------------------------- |
| 10-30%         | +4    | Few to scattered clouds (ideal) |
| 0-10%          | +3    | Clear skies                     |
| 30-60%         | +2    | Partly cloudy                   |
| 60-80%         | 0     | Mostly cloudy                   |
| 80-95%         | -1    | Very cloudy                     |
| 95-100%        | -3    | Overcast                        |

#### 4. Precipitation Score (-15 to +5 points)

Assesses precipitation impact on outdoor activities:

| Precipitation (mm) | Score | Description           |
| ------------------ | ----- | --------------------- |
| 0 mm               | +5    | No precipitation      |
| 0-0.1 mm           | +3    | Trace amounts         |
| 0.1-0.5 mm         | 0     | Very light            |
| 0.5-1.0 mm         | -2    | Light drizzle         |
| 1.0-2.5 mm         | -5    | Light rain            |
| 2.5-5.0 mm         | -8    | Moderate rain         |
| 5.0-10.0 mm        | -11   | Heavy rain            |
| 10.0-20.0 mm       | -13   | Very heavy rain       |
| >20.0 mm           | -15   | Extreme precipitation |

#### 5. Humidity Score (-4 to +3 points)

Evaluates relative humidity comfort, optimized for maritime climates like Asturias:

| Relative Humidity | Score | Description                    |
| ----------------- | ----- | ------------------------------ |
| 40-60%            | +3    | Ideal humidity range           |
| 30-40%            | +2    | Low humidity (good)            |
| 60-70%            | +1    | Moderate humidity (acceptable) |
| 20-30%, 70-80%    | 0     | Very low/high (neutral)        |
| 80-85%, 15-20%    | -1    | Very high/low (noticeable)     |
| 85-90%, 10-15%    | -2    | Extremely high/low             |
| 90-95%, 5-10%     | -3    | Near saturation/zero           |
| >95%, <5%         | -4    | Beyond extreme levels          |

### Total Score Calculation

Each hour's **total score** is the sum of all five component scores:

```text
Total Score = Temperature Score + Wind Score + Cloud Score + Precipitation Score + Humidity Score
```

**Possible range**: -42 to +23 points per hour

### Overall Rating System

The total scores are converted to descriptive ratings:

| Score Range | Rating    |
| ----------- | --------- |
| 18+         | Excellent |
| 13-18       | Very Good |
| 7-13        | Good      |
| 2-7         | Fair      |
| <2          | Poor      |

### Optimal Weather Block Detection

The application also identifies the best continuous time periods:

1. **Quality Filter**: Only considers hours with non-negative scores for multi-hour blocks
2. **Duration Bonus**: Longer consistent periods receive logarithmic bonuses
3. **Consistency Check**: Prioritizes blocks with stable scores (low variance)
4. **Combined Scoring**: Balances quality, duration, and consistency

This system helps users find not just good individual hours, but sustained periods of favorable
weather for extended outdoor activities.
