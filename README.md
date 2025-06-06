# Weather Helper

Weather Helper is a Python app with a modern Tkinter GUI for viewing and comparing weather forecasts across multiple locations. It helps you find the best times and places for outdoor activities, using activity-based weather scoring and clear visualizations.

## Features
A quick overview of what the app offers.
- Forecasts for multiple locations
- Activity-based weather ratings
- Hourly and daily weather details
- Top recommendations for each day
- Simple, interactive GUI (no command line)

## Unified Scoring Mechanism

The application employs a unified scoring mechanism to provide consistent weather assessments across all its features. This ensures that recommendations and rankings are based on a single, reliable source of truth for how "good" the weather is at any given time.

### Core Hourly Score

The foundation of the scoring system is the `HourlyWeather.total_score`. This score is calculated for each hour of the weather forecast and represents an overall assessment of weather conditions for that specific hour.

The `total_score` is a sum of several component scores, each evaluating a different aspect of the weather:

*   **`weather_score`**: Derived from the weather symbol (e.g., "clearsky", "rain", "cloudy"). Clearer conditions generally receive higher scores.
*   **`temp_score`**: Assesses the comfort level of the air temperature.
*   **`wind_score`**: Evaluates the pleasantness of the wind speed (e.g., light breezes are preferred over strong winds).
*   **`cloud_score`**: Considers the impact of cloud coverage.
*   **`precip_prob_score`**: Factors in the probability of precipitation; lower probabilities score higher.

These individual component scores are determined by dedicated functions (primarily in `src/utils.py`) that interpret the raw forecast data.

### How Features Utilize the Unified Score

Different features of the Weather Helper leverage this core `HourlyWeather.total_score` in ways appropriate to their purpose:

*   **Hourly Forecast Display**: When viewing the detailed hourly forecast for a location (either by default or with the `-a` flag), the displayed rating for each hour directly reflects its `total_score`.
*   **Daily Rankings (`-r` flag)**: The daily ranking feature calculates an `avg_score` for each day. This is achieved by averaging the `total_score` of all daylight hours (as defined in `src/config.py`) for that day. Locations are then ranked based on these daily average scores.
*   **Best Times Recommendation**: This feature (default behavior or when using `-r` for detailed recommendations within ranked days) identifies continuous blocks of hours with favorable weather conditions. The "goodness" of these blocks is also determined by averaging the `total_score` of the constituent hours.

This centralized approach means that any adjustments to the scoring logic (e.g., changing how temperature affects the score) are made in one place and consistently propagate throughout all parts of the application, ensuring maintainability and reliability.

## Project Structure
How the code is organized for clarity and easy maintenance.
```
weather-helper/
├── run_gui.py         # Launches the GUI
├── src/
│   ├── gui/           # Tkinter GUI code
│   ├── core/          # Weather logic, API, evaluation
│   └── utils/         # Helpers/utilities
├── requirements.txt   # Dependencies
├── README.md
├── LICENSE
└── .gitignore
```
*Optional: Add an `assets/` folder for icons/screenshots if you want.*

## Usage
How to set up the project on your computer.

```bash
# Clone the repository
git clone https://github.com/maximbetin/weather-helper.git
cd weather-helper

# Create a virtual environment
python -m venv venv # or python3 -m venv venv

# Activate the virtual environment
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python run_gui.py
```

## API
The external weather data source used by the app.
- MET Norway Weather API: https://api.met.no/weatherapi/locationforecast/2.0

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.