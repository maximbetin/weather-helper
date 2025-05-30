from setuptools import find_packages, setup

setup(
    name="weather-helper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "idna==3.10",
        "pytz>=2022.7",
        "pytest>=7.3.1",
        "urllib3==2.4.0",
        "colorama>=0.4.6",
        "argparse>=1.4.0",
        "requests>=2.28.1",
        "certifi == 2025.4.26",
        "setuptools >= 65.6.3",
        "typing-extensions >= 4.4.0",
        "charset-normalizer == 3.4.2",
    ],
    python_requires=">=3.8",
)
