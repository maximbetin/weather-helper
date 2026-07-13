# Weather Helper

[![Test and Build Releases](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/maximbetin/weather-helper/actions/workflows/release.yml)

## Overview

Weather Helper compares hourly forecasts and identifies useful outdoor weather
windows. It has a Tkinter Windows interface and a responsive Flet interface for
Android, both backed by the same weather, evaluation, and activity-scoring code.

Prebuilt Windows ZIP and Android APK files are available from the repository's
[GitHub Releases](https://github.com/maximbetin/weather-helper/releases) page.

## Features

- **Detailed Hourly Forecasts**: Comprehensive weather data including temperature, wind speed, cloud coverage, precipitation, rain risk, and relative humidity.
- **Multi-Region Support**: Compare locations across different regions (e.g., Asturias, Spain, Worldwide) to plan trips effectively.
- **Activity Profiles**: Rank the same forecast for either hiking/general outdoors or beach plans focused on swimming and sunbathing.
- **Optimal Weather Finder**: Automatically identifies the best time blocks for the selected activity based on a weighted scoring system.
- **Visual Scoring Analysis**: Color-coded side panel displaying the top locations sorted by weather quality.
- **Windows and Android Interfaces**: Native-feeling Tkinter desktop and responsive Flet mobile layouts.

## Installation and Usage

1. **Clone the repository**:

```bash
git clone https://github.com/maximbetin/weather-helper.git
cd weather-helper
```

2. **Create and activate a virtual environment**:

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: .\.venv\Scripts\Activate.ps1
```

Using a virtual environment is required for development. Installing into a
shared/global Python can conflict with unrelated tools that pin different
versions of `requests` or Flet's `httpx` dependency.

3. **Install development and application dependencies**:

```bash
python -m pip install -e ".[dev]"
```

4. **Run the application**:

```bash
python weather_helper.py
```

### Android and Flet development

For a clean mobile environment on Windows, run from the repository root:

```powershell
py -3.13 -m venv .venv-mobile
.\.venv-mobile\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[mobile,dev]"
flet run weather_helper_mobile.py
```

The complete beginner-oriented setup, APK build, signing, installation,
versioning, CI release, and troubleshooting instructions are in
[Android Development and APK Builds](docs/android-development.md).

## Testing

The project uses pytest for testing. To run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The test suite includes:
- Unit tests for core business logic (scoring, models)
- GUI logic tests
- Integration tests for data processing

## Building Executables

The application can be built into standalone executables using PyInstaller:

```bash
python -m pip install -e ".[windows-build]"
pyinstaller --onefile --windowed weather_helper.py
```

The executable will be created in the `dist` directory.

## Building an Android APK

With the mobile environment active:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
flet build apk --yes --no-rich-output
```

The APK is created under `build\apk`. See the
[Android development guide](docs/android-development.md) before distributing
builds, because Android version numbers and signing keys determine whether an
APK can update an existing installation.

## Automated GitHub Releases

Relevant pushes to `main` run the tests, build both platforms, and create a
GitHub Release containing:

- `weather-helper-windows-<version>.zip`
- `weather-helper-android-<version>.apk`

The Android build works without repository secrets using a temporary debug key.
Configure the four signing secrets described in the Android guide so APKs from
different workflow runs can update one another.

## Project Structure

```bash
weather-helper/
├── src/
│   ├── application/    # UI-independent forecast orchestration
│   ├── core/           # Core business logic and data models
│   ├── gui/            # Tkinter GUI components and theming
│   └── mobile/         # Flet mobile UI and presentation state
├── docs/               # Development and build guides
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
- **`src/application/forecast_service.py`**: Shared forecast loading orchestration
- **`src/gui/app.py`**: Main application window and logic
- **`src/mobile/app.py`**: Flet mobile screen
- **`src/mobile/view_model.py`**: UI-independent mobile presentation state
- **`src/gui/themes.py`**: UI theming and visual styling
- **`src/gui/formatting.py`**: Data formatting for display

## Weather Scoring System

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions. Each hour receives a base hiking/general outdoors score from five key factors, and the app can also re-score the same hour for beach plans focused on open-water swimming and sunbathing. Forecast times are converted to the app timezone before grouping, filtering, and display.

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

### Activity Profiles

The app can rank locations and hourly blocks using different activity profiles:

| Profile   | Intended use                         | Scoring emphasis |
| --------- | ------------------------------------ | ---------------- |
| Hiking    | General outdoors, walking, day trips | Balanced comfort across temperature, wind, cloud, rain, and humidity |
| Beach     | Swimming and sunbathing              | Warm air, low wind, dry weather, and clear to partly cloudy skies |

Beach scoring uses the same forecast data, but it treats wind and rain more strictly because they matter more for open-water swimming and beach comfort. Wind values are shown in meters per second (m/s), matching the source forecast data.

Both profiles also consider precipitation probability and forecast symbols such as rain, showers, fog, snow, and thunder. These risk signals can lower the profile score even when the expected precipitation amount is low.

### Overall Rating System

The total scores are converted to descriptive ratings. Each activity profile has its own thresholds, so Beach scores are interpreted against beach-specific expectations rather than the generic outdoors scale.

| Score Range | Rating    |
| ----------- | --------- |
| 18+         | Excellent |
| 13-18       | Very Good |
| 7-13        | Good      |
| 2-7         | Fair      |
| <2          | Poor      |

### Optimal Weather Block Detection

The application identifies the best continuous time periods for the selected activity by:

1. **Filtering**: Avoiding multi-hour recommendations that contain bad hours.
2. **Continuity Checks**: Only joining forecast rows that are truly adjacent hours.
3. **Quality First**: Letting the average profile score dominate the recommendation.
4. **Duration Bonuses**: Rewarding longer useful periods without letting length overwhelm quality.
5. **Consistency Checks**: Prioritizing blocks with stable scores.

This ensures users find sustained periods of favorable weather rather than just isolated good hours.

The recommended time remains the best continuous block, but location ranking
uses the selected activity's average across the whole usable day. Small
hour-to-hour changes are tolerated, while abrupt changes add an increasingly
strong volatility penalty. This keeps the Top 10 score grounded in the broader
day even when one short period has excellent conditions. For today, the score
uses the remaining useful daylight; future dates use the full daylight period.
