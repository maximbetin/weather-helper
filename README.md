# Weather Helper

[![Build Executable](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/maximbetin/weather-helper/actions/workflows/ci.yml)

## Overview

The Weather Helper is a desktop application that provides detailed weather forecasts for various
locations. It allows users to compare weather conditions across multiple locations and find the best
time for outdoor activities.

## Features

- **Detailed Hourly Forecasts**: Get detailed hourly weather information, including temperature,
  wind speed, cloud coverage, and precipitation amount.
- **Location Comparison**: Compare weather forecasts for multiple locations side-by-side.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for outdoor activities
  based on a scoring system.
- **Clean and Intuitive Interface**: A user-friendly graphical interface built with Tkinter.

## Installation and Usage

### 1. **Clone the repository:**

```bash
git clone https://github.com/maximbetin/weather-helper.git
cd weather-helper
```

### 2. **Create a virtual environment (recommended):**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. **Install dependencies:**

```bash
pip install .
```

### 4. **Run the application:**

```bash
python weather_helper.py
```

### Testing

The project uses pytest for testing. To run the tests:

```bash
pytest
```

The test suite includes:

- Unit tests for core functionality
- API integration tests (mocked)
- Data processing tests

### Building Executables

The application can be built into standalone executables using PyInstaller:

```bash
pyinstaller --onefile --windowed weather_helper.py
```

The executable will be created in the `dist` directory.

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

- Tests are run on every commit
- When a commit is pushed to main:
  - Tests are run on Windows
  - Executables are built for Windows
  - A new release is created with the executables

### Project Structure

```bash
weather-helper/
├── src/
│   ├── core/           # Core business logic and data models
│   └── gui/            # GUI components and theming
├── tests/              # Test suite
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # This file
```

#### Core Components

- **`src/core/config.py`**: Configuration constants and utility functions
- **`src/core/models.py`**: Data models (HourlyWeather, DailyReport)
- **`src/core/evaluation.py`**: Weather scoring and analysis logic
- **`src/core/weather_api.py`**: API integration for weather data
- **`src/core/locations.py`**: Location definitions and management
- **`src/gui/app.py`**: Main application window and logic
- **`src/gui/themes.py`**: UI theming and visual styling
- **`src/gui/formatting.py`**: Data formatting for display

### Weather Scoring System

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions for outdoor
activities. Each hour receives a total score based on four key factors.

#### Individual Component Scores

#### 1. Temperature Score (-15 to +8 points)

Evaluates temperature comfort for outdoor activities:

| Temperature (°C) | Score | Description         |
| ---------------- | ----- | ------------------- |
| 20-24°C          | +8    | Ideal temperature   |
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

#### 4. Precipitation Score (-12 to +6 points)

Assesses precipitation impact on outdoor activities:

| Precipitation (mm) | Score | Description           |
| ------------------ | ----- | --------------------- |
| 0 mm               | +6    | No precipitation      |
| 0-0.1 mm           | +4    | Trace amounts         |
| 0.1-0.5 mm         | +2    | Very light            |
| 0.5-1.0 mm         | 0     | Light drizzle         |
| 1.0-2.5 mm         | -2    | Light rain            |
| 2.5-5.0 mm         | -4    | Moderate rain         |
| 5.0-10.0 mm        | -6    | Heavy rain            |
| 10.0-20.0 mm       | -8    | Very heavy rain       |
| >20.0 mm           | -12   | Extreme precipitation |

#### Total Score Calculation

Each hour's **total score** is the sum of all four component scores:

```text
Total Score = Temperature Score + Wind Score + Cloud Score + Precipitation Score
```

**Possible range**: -38 to +20 points per hour

#### Overall Rating System

The total scores are converted to descriptive ratings:

| Score Range | Rating    |
| ----------- | --------- |
| 12+         | Excellent |
| 8-12        | Very Good |
| 4-8         | Good      |
| 1-4         | Fair      |
| <1          | Poor      |

#### Optimal Weather Block Detection

The application also identifies the best continuous time periods:

1. **Quality Filter**: Only considers hours with non-negative scores for multi-hour blocks
2. **Duration Bonus**: Longer consistent periods receive logarithmic bonuses
3. **Consistency Check**: Prioritizes blocks with stable scores (low variance)
4. **Combined Scoring**: Balances quality, duration, and consistency

This system helps users find not just good individual hours, but sustained periods of favorable
weather for extended outdoor activities.
