# Weather Helper

A Python-based weather application that provides weather information through a graphical user interface.

## Project Structure

```
weather-helper/
├── src/
│   ├── core/       # Core weather functionality
│   ├── gui/        # GUI implementation
│   └── utils/      # Utility functions
├── .github/
│   └── workflows/  # CI/CD workflows
├── weather_helper.py    # Main entry point
├── requirements.txt     # Python dependencies
└── setup.py             # Package setup
```

## Prerequisites

- Python 3.13.4 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/maximbetin/weather-helper.git
   cd weather-helper
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Running the Application

To run the application in development mode:
```sh
python weather_helper.py
```

## Building an Executable

To create a standalone executable for this application:

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Build the executable:
   ```sh
   pyinstaller --onefile --windowed weather_helper.py
   ```
   The executable will be located in the `dist` folder as `WeatherHelper.exe`.

## Development

### Running Tests

Run the test suite using pytest:
```sh
pytest
```

### GitHub Actions Workflows

This project uses GitHub Actions for continuous integration and deployment:

- **Build Workflow**: Tests the code and builds the executable on every merge to the `main` branch.

The workflows are defined in the `.github/workflows` directory.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.