#!/usr/bin/env python3
"""
Build script for Weather Helper executable.
Uses PyInstaller with flags optimized to reduce malware false positives.
"""

import os
import subprocess
import sys


def main():
    """Build the executable using PyInstaller with optimized flags."""

    # Check if PyInstaller is installed
    try:
        # Try to find pyinstaller executable in the virtual environment
        venv_pyinstaller = os.path.join(
            os.path.dirname(sys.executable), "pyinstaller.exe"
        )
        if os.path.exists(venv_pyinstaller):
            subprocess.run(
                [venv_pyinstaller, "--version"], capture_output=True, check=True
            )
            pyinstaller_cmd = venv_pyinstaller
        else:
            # Fallback to module approach
            subprocess.run(
                [sys.executable, "-m", "pyinstaller", "--version"],
                capture_output=True,
                check=True,
            )
            pyinstaller_cmd = [sys.executable, "-m", "pyinstaller"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"], check=True
        )
        # After installation, try to find the executable again
        venv_pyinstaller = os.path.join(
            os.path.dirname(sys.executable), "pyinstaller.exe"
        )
        if os.path.exists(venv_pyinstaller):
            subprocess.run(
                [venv_pyinstaller, "--version"], capture_output=True, check=True
            )
            pyinstaller_cmd = venv_pyinstaller
        else:
            subprocess.run(
                [sys.executable, "-m", "pyinstaller", "--version"],
                capture_output=True,
                check=True,
            )
            pyinstaller_cmd = [sys.executable, "-m", "pyinstaller"]

    # Build command with flags to reduce malware false positives
    if isinstance(pyinstaller_cmd, list):
        cmd = pyinstaller_cmd + [
            "--onedir",  # Create directory instead of single file
            "--windowed",  # No console window on Windows
            "--clean",  # Clean cache before building
            "--noupx",  # Disable UPX compression (often flagged)
            "--name=WeatherHelper",  # Set output name
            "weather_helper.py",
        ]
    else:
        cmd = [
            pyinstaller_cmd,
            "--onedir",  # Create directory instead of single file
            "--windowed",  # No console window on Windows
            "--clean",  # Clean cache before building
            "--noupx",  # Disable UPX compression (often flagged)
            "--name=WeatherHelper",  # Set output name
            "weather_helper.py",
        ]

    print("Building executable with PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    print("\nThis approach creates a directory structure that's less likely")
    print("to trigger malware warnings compared to --onefile builds.")

    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Build completed successfully!")
        print("\nOutput location: dist/weather_helper/")
        print("Run the executable from: dist/weather_helper/WeatherHelper.exe")
        print("\nNote: The --onedir approach creates a folder with the executable")
        print("and all dependencies, which is more transparent and secure.")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
