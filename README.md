# Weather Helper

Weather Helper is a Python app with a modern Tkinter GUI for viewing and comparing weather forecasts across multiple locations. It helps you find the best times and places for outdoor activities, using activity-based weather scoring and clear visualizations.

## Features
A quick overview of what the app offers.
- Forecasts for multiple locations
- Activity-based weather ratings
- Hourly and daily weather details
- Top recommendations for each day
- Simple, interactive GUI (no command line)

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