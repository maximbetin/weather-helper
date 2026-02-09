# Weather Helper

[![Build Executable](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml)

## Overview

The Weather Helper is a desktop application that provides detailed weather forecasts and analysis for optimal trip planning. It allows users to compare weather conditions across multiple regions (Europe, Americas, etc.) and automatically identifies the best time blocks for outdoor activities using a sophisticated scoring system.

## Features

- **Detailed Hourly Forecasts**: Comprehensive weather data including temperature, wind speed, cloud coverage, precipitation, and relative humidity.
- **Multi-Region Support**: Compare locations across different regions (e.g., Asturias, Spain, Worldwide) to plan trips effectively.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for outdoor activities based on a weighted scoring system.
- **Visual Scoring Analysis**: Color-coded side panel displaying the top locations sorted by weather quality.
- **Clean Interface**: A user-friendly GUI built with Tkinter, featuring responsive layouts and scrollable panels for easy navigation.
- **Data Export**: Ability to view and analyze weather parameters in an organized format.

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
- Unit tests for core business logic (scoring, models)
- GUI logic tests
- Integration tests for data processing

## Building Executables

The application can be built into standalone executables using PyInstaller:

```bash
pyinstaller --onefile --windowed weather_helper.py
```

The executable will be created in the `dist` directory.

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
- **`src/core/scoring.py`**: Centralized weather scoring logic and range definitions
- **`src/core/evaluation.py`**: Weather evaluation and analysis logic
- **`src/core/weather_api.py`**: API integration for weather data
- **`src/core/locations.py`**: Location definitions and management
- **`src/gui/app.py`**: Main application window and logic
- **`src/gui/themes.py`**: UI theming and visual styling
- **`src/gui/formatting.py`**: Data formatting for display

## Weather Scoring System

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions for outdoor activities. Each hour receives a total score based on five key factors.

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

#### 4. Precipitation Score (-12 to +5 points)

Assesses precipitation impact on outdoor activities:

| Precipitation (mm) | Score | Description           |
| ------------------ | ----- | --------------------- |
| 0 mm               | +5    | No precipitation      |
| 0-0.1 mm           | +4    | Trace amounts         |
| 0.1-0.5 mm         | +2    | Very light            |
| 0.5-1.0 mm         | 0     | Light drizzle         |
| 1.0-2.5 mm         | -2    | Light rain            |
| 2.5-5.0 mm         | -4    | Moderate rain         |
| 5.0-10.0 mm        | -6    | Heavy rain            |
| 10.0-20.0 mm       | -8    | Very heavy rain       |
| >20.0 mm           | -12   | Extreme precipitation |

#### 5. Humidity Score (-4 to +3 points)

Evaluates relative humidity comfort:

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

The application identifies the best continuous time periods for outdoor activities by:

1. **Filtering**: Only considering hours with non-negative scores.
2. **Duration Bonuses**: Rewarding longer consistent periods of good weather.
3. **Consistency Checks**: Prioritizing blocks with stable scores.
4. **Combined Scoring**: Balancing quality, duration, and consistency.

This ensures users find sustained periods of favorable weather rather than just isolated good hours.
