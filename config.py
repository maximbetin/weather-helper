import os

# Define locations in Asturias
LOCATIONS = {
  "Oviedo": "33044"
}

# API settings
API_URL = "https://opendata.aemet.es/opendata"
HEADERS = {
    "Accept": "application/json",
    "api_key": os.getenv("API_KEY")
}