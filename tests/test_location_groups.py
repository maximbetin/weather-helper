import pytest
from src.core.locations import (
    LOCATION_GROUPS,
    LOCATIONS,
    ASTURIAS_LOCATIONS,
    SPAIN_LOCATIONS,
    WORLDWIDE_LOCATIONS
)

def test_location_groups_structure():
    """Verify the structure and content of LOCATION_GROUPS."""
    expected_keys = {"Asturias", "Spain", "Worldwide"}
    assert set(LOCATION_GROUPS.keys()) == expected_keys

    # Check that mappings are correct
    assert LOCATION_GROUPS["Asturias"] == ASTURIAS_LOCATIONS
    assert LOCATION_GROUPS["Spain"] == SPAIN_LOCATIONS
    assert LOCATION_GROUPS["Worldwide"] == WORLDWIDE_LOCATIONS

def test_default_locations():
    """Verify that the default LOCATIONS export matches Asturias."""
    assert LOCATIONS == ASTURIAS_LOCATIONS

def test_location_containment():
    """Verify that groups are non-overlapping as per user request."""
    # Spain should NOT contain any Asturias locations
    for key in ASTURIAS_LOCATIONS:
        assert key not in SPAIN_LOCATIONS

    # Worldwide should only contain Madrid from Spain
    spain_keys_in_worldwide = [key for key in SPAIN_LOCATIONS if key in WORLDWIDE_LOCATIONS]
    assert spain_keys_in_worldwide == ["madrid"]

    # Check that we have the expected number of locations
    # Spain has 16 locations in OTHER list
    assert len(SPAIN_LOCATIONS) == 16
    # Worldwide has 12 OTHER locations + Madrid = 13
    assert len(WORLDWIDE_LOCATIONS) == 13

    # Asturias has 12 locations (previously 10)
    assert len(ASTURIAS_LOCATIONS) == 12
