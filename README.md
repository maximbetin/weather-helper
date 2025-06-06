# Weather Helper

A desktop application that helps users find the best weather conditions across multiple locations.

## Features

- View weather forecasts for multiple locations
- Compare weather conditions across different locations
- Get recommendations for the best locations based on weather conditions
- Simple and intuitive GUI interface

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/maximbetin/weather-helper.git
   cd weather-helper
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
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
├── .github/            # GitHub Actions workflows
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.