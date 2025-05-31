import pytest

from src.core.locations import LOCATIONS, Location


def test_location_creation():
  """Test creating a Location instance with valid data."""
  location = Location("test", "Test City", 40.7128, -74.0060)
  assert location.key == "test"
  assert location.name == "Test City"
  assert location.lat == 40.7128
  assert location.lon == -74.0060


def test_location_immutability():
  """Test that Location instances are immutable."""
  location = Location("test", "Test City", 40.7128, -74.0060)
  with pytest.raises(AttributeError):
    setattr(location, "name", "New Name")


def test_locations_dictionary():
  """Test that the LOCATIONS dictionary contains valid Location objects."""
  assert isinstance(LOCATIONS, dict)
  assert len(LOCATIONS) > 0

  # Test a few known locations
  assert "gijon" in LOCATIONS
  assert "oviedo" in LOCATIONS

  # Test location data
  gijon = LOCATIONS["gijon"]
  assert isinstance(gijon, Location)
  assert gijon.name == "Gijón"
  assert gijon.lat == 43.5322
  assert gijon.lon == -5.6610


def test_location_coordinates_range():
  """Test that all locations have valid coordinate ranges."""
  for location in LOCATIONS.values():
    assert -90 <= location.lat <= 90  # Valid latitude range
    assert -180 <= location.lon <= 180  # Valid longitude range
