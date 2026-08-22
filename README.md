# Weather Helper

Weather Helper compares hourly forecasts and identifies useful outdoor weather windows, then nags you with a daily notification naming today's best activity, location, and time block. It ships as a single Android app built with Capacitor.

## Architecture

```text
Vanilla HTML/CSS/JavaScript (js/, css/, index.html)
          ↓
       dist/ web assets
          ↓
Capacitor Android WebView wrapper (CapacitorHttp enabled)
          ↓
Native Android Gradle project (android/)
          ↓
artifacts/weather-helper.apk
```

Capacitor is used only as the native Android container and bridge. The interface and scoring logic remain plain HTML, CSS, and modern vanilla JavaScript (`js/core/`), shared between the foreground UI (`js/app.js`) and the headless daily background task (`js/background-task.js`). `CapacitorHttp` is enabled so `fetch()` is routed through the native HTTP layer, which lets a custom `User-Agent` header reach MET Norway (required by their API terms) from both the app and the background task.

### Weather data and attribution

Forecasts come from the [MET Norway Locationforecast API](https://api.met.no/weatherapi/locationforecast/2.0/). Weather Helper processes the source data into hourly displays, activity scores, rankings, and recommended windows; MET Norway does not endorse those changes. The data is available under MET Norway's [licensing and data policy](https://api.met.no/doc/License), including CC BY 4.0.

## Features

- **Detailed Hourly Forecasts**: Comprehensive weather data including temperature, wind speed, cloud coverage, precipitation, rain risk, and relative humidity.
- **Multi-Region Support**: Compare locations across different regions (e.g., Asturias, Spain, Worldwide) to plan trips effectively.
- **Activity Profiles**: Rank the same forecast for either Hiking (any general outdoor time: strolling, sightseeing, exploring, walking) or Beach (warm, sunny outdoor leisure: beach, pool, swimming, sunbathing).
- **Optimal Weather Finder**: Automatically identifies the best time blocks for the selected activity based on a weighted scoring system.
- **Daily Nag Notification**: A background task reports today's best Hiking option and today's best Beach option independently, each naming the best location across all configured Asturias locations and its time window. When any candidate window scores at least 50/100 the best of those is recommended, even if the ranking's duration/consistency bonuses put a weaker but longer window on top. Only if every option scores below 50/100 is the best of them presented as "no good option" rather than as a recommendation, and a total forecast outage is reported as an outage rather than as bad weather.
- **Honest Missing-Data Display**: Missing precipitation is shown as `N/A`, not as a dry `0.0 mm` forecast.

## Prerequisites

- Node.js 24 and npm 11 or newer
- Java 21 for Android builds
- Android SDK/API and build tools for local Gradle builds
- Optional: `adb` for installation and an Android emulator or phone

The Android project uses the committed Gradle wrapper. Do not install a separate global Gradle version.

## Clean setup and web tests

```bash
npm ci
npm test
npm run build
```

`npm run build` copies the local HTML/CSS/JavaScript, manifest, and icons into `dist/`, then `scripts/verify-web-build.mjs` checks that required files are present and that no `<script>`/`<link>`/`<img>` tag in `index.html` loads a remote or localhost runtime resource.

## Build the Android APK locally

```bash
npm run android:sync
```

then, on Windows PowerShell:

```powershell
cd android
.\gradlew.bat assembleDebug
cd ..
node scripts\locate-apk.mjs --variant debug --output artifacts\weather-helper.apk
```

or on macOS/Linux:

```bash
cd android
./gradlew assembleDebug
cd ..
node scripts/locate-apk.mjs --variant debug --output artifacts/weather-helper.apk
```

Or run the complete cross-platform helper:

```bash
npm run android:debug
```

The final installable file is `artifacts/weather-helper.apk` (rename via `--output`). Inspect it once Android SDK tools are available:

```bash
node scripts/verify-apk.mjs artifacts/weather-helper.apk
```

This checks that the APK is non-empty and contains `assets/public/index.html`. If `apkanalyzer` is installed, it also verifies application ID `com.maximbk.weatherhelper`.

## Install with ADB

```bash
adb install -r artifacts/weather-helper.apk
```

The `-r` flag replaces an existing installation while preserving its data when signatures match.

## GitHub Actions

`.github/workflows/android.yml` runs on every push to `main`, and on manual `workflow_dispatch`. It runs `npm ci`, `npm test`, the web build, `npx cap sync android`, and `gradlew assembleRelease`, then publishes the signed APK twice:

- a **permanent versioned GitHub Release**, tagged and named from the current `version.json` version (e.g. `Weather Helper v1.4.0`, with auto-generated notes) and marked as latest. Pushing to `main` again without bumping `version.json` overwrites that same release rather than creating a new one.
- a **temporary per-run build artifact**, named `weather-helper-v<version>-build-<run number>` and kept for 7 days, so an individual run's APK can be downloaded without disturbing the release.

Gradle reads the authoritative version from `version.json` (`versionName`, `versionCode`); increase both deliberately before a release, since Android's `versionCode` must always increase.

## Native behavior and permissions

The Android manifest declares `android.permission.INTERNET` (for forecast fetches) and `android.permission.POST_NOTIFICATIONS` (Android 13+, requested at runtime by the app). `@capacitor/background-runner`'s own manifest fragment pulls in location permissions for its optional geolocation API; the app's manifest explicitly strips them (`tools:node="remove"`) since Weather Helper never does geolocation.

The manifest also declares `android.permission.SCHEDULE_EXACT_ALARM`. Weather Helper is not an alarm-clock app, so it is not eligible for `USE_EXACT_ALARM` and cannot assume exact delivery: when the user has not granted "Alarms & reminders", `@capacitor/background-runner` falls back to an inexact alarm and Android may deliver the reminder late. The app therefore promises the notification *around* the chosen time, never at exactly that minute.

The background runner wakes roughly hourly rather than once a day, but almost every wake-up does nothing: forecasts are only fetched inside a window around the chosen reminder time, the notification is armed for today only, and the processed date is recorded so at most one notification is produced per day. A late OS wake-up still delivers today's recommendation (within a few hours of the reminder time) instead of shifting it to tomorrow.

On some OEMs (Xiaomi, Samsung, Huawei), the daily background refresh needs the app excluded from battery optimization to survive Doze; the Settings screen explains this on first enabling notifications.

## Project Structure

```bash
weather-helper/
├── index.html          # App shell
├── css/styles.css       # Styling
├── native-bridge.js     # Capacitor plugin wrapper (App, LocalNotifications, Preferences)
├── js/
│   ├── core/            # Weather API, models, evaluation, scoring, locations, timezone, daily summary
│   ├── app.js            # UI orchestrator
│   ├── notifications.js  # Settings screen + notification scheduling
│   └── background-task.js # @capacitor/background-runner worker entry
├── android/              # Capacitor-generated Gradle project
├── scripts/               # Build, sync, and packaging helpers
├── tests/                 # node --test suite
├── capacitor.config.ts
└── version.json
```

### Core Components

- **`js/core/scoring.js`**: Centralized weather scoring logic and range definitions
- **`js/core/evaluation.js`**: Weather evaluation and analysis logic
- **`js/core/weather_api.js`**: MET Norway API integration (complete → compact fallback)
- **`js/core/locations.js`**: Location definitions and management
- **`js/core/timezone.js`**: Europe/Madrid local-time helpers
- **`js/core/daily_summary.js`**: Builds the daily nag notification's recommendation text
- **`js/app.js`**: Main UI screen and logic
- **`js/notifications.js`**: Settings screen and daily notification scheduling
- **`js/background-task.js`**: Headless daily fetch + score + notify

## Weather Scoring System

The Weather Helper uses a comprehensive scoring system to evaluate weather conditions. Each hour receives a base Hiking score (general outdoor comfort) from five key factors, and the app can also re-score the same hour for Beach conditions (warm, sunny outdoor leisure). Forecast times are converted to the app timezone before grouping, filtering, and display.

### Individual Component Scores

#### 1. Temperature Score (-15 to +7 points)

Evaluates temperature comfort for outdoor activities:

| Temperature (°C) | Score | Description         |
| ---------------- | ----- | -------------------- |
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

| Wind Speed (km/h) | Score | Description             |
| ------------------- | ----- | ------------------------ |
| 3.6-10.8 km/h       | +2    | Light breeze (ideal)    |
| 0-3.6 km/h          | +1    | Calm (good)             |
| 10.8-18 km/h        | 0     | Gentle breeze (neutral) |
| 18-28.8 km/h        | -2    | Moderate breeze         |
| 28.8-43.2 km/h      | -4    | Fresh breeze            |
| 43.2-57.6 km/h      | -6    | Strong breeze           |
| 57.6-72 km/h        | -7    | Near gale               |
| >72 km/h            | -8    | Gale and above          |

#### 3. Cloud Coverage Score (-3 to +4 points)

Evaluates sky conditions for outdoor activities:

| Cloud Coverage | Score | Description                     |
| --------------- | ----- | -------------------------------- |
| 10-30%         | +4    | Few to scattered clouds (ideal) |
| 0-10%          | +3    | Clear skies                     |
| 30-60%         | +2    | Partly cloudy                   |
| 60-80%         | 0     | Mostly cloudy                   |
| 80-95%         | -1    | Very cloudy                     |
| 95-100%        | -3    | Overcast                        |

#### 4. Precipitation Score (-12 to +5 points)

Assesses precipitation impact on outdoor activities:

| Precipitation (mm) | Score | Description           |
| -------------------- | ----- | ---------------------- |
| 0 mm               | +5    | No precipitation      |
| 0-0.1 mm           | +4    | Trace amounts         |
| 0.1-0.5 mm         | +2    | Very light            |
| 0.5-1.0 mm         | 0     | Light drizzle         |
| 1.0-2.5 mm         | -2    | Light rain            |
| 2.5-5.0 mm         | -4    | Moderate rain         |
| 5.0-10.0 mm        | -6    | Heavy rain             |
| 10.0-20.0 mm       | -8    | Very heavy rain        |
| >20.0 mm           | -12   | Extreme precipitation |

#### 5. Humidity Score (-4 to +3 points)

Evaluates relative humidity comfort:

| Relative Humidity | Score | Description                    |
| ------------------- | ----- | -------------------------------- |
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

| Profile | Intended use | Scoring emphasis |
| --------- | ------------------------------------- | ----------------- |
| Hiking | Any general outdoor time: strolling, sightseeing, exploring, walking | Balanced comfort across temperature, wind, cloud, rain, and humidity |
| Beach | Warm, sunny outdoor leisure: beach, pool, swimming, sunbathing | Warm air, low wind, dry weather, and clear to partly cloudy skies |

Beach scoring uses the same forecast data, but it treats wind and rain more strictly because they matter more when you are sitting still in a swimsuit. It scores air conditions only — there is no sea-state or water-temperature input. Wind values are converted from the source forecast data and always shown in kilometres per hour (km/h).

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

All successfully loaded locations that contain hourly data for the selected date remain selectable, even when conditions do not meet the minimum for a ranked recommendation. In that case the app shows an unranked summary and keeps the hourly details available for the user's own judgment.

Locations are ranked by the quality of their best usable continuous window — the same combined quality/duration/consistency score that picks the window itself — so the ranking answers "where is the best opportunity today?". The score shown beside a recommended window is that window's own quality, not a whole-day aggregate. The broader remaining-day score (average with a volatility penalty for abrupt hour-to-hour changes) is kept as context and only breaks ties between locations whose best opportunities are effectively equal. For today, both are computed from the remaining useful daylight only, so hours that have already passed cannot influence today's ranking; future dates use the full daylight period.
