"""
Shared fixtures and configuration for the aero-prox test suite.

These fixtures provide mock objects and reusable test data so that
unit tests can run without hitting the real FlightRadar24 API or
requiring the airportsdata package.
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

SAMPLE_AIRPORT_ICAO = "VERC"
SAMPLE_AIRPORT = {
    "name": "Birsa Munda Airport",
    "city": "Ranchi",
    "country": "India",
    "iata": "IXR",
    "lat": 23.3147,
    "lon": 85.3217,
}

SAMPLE_FLIGHT_ID = "abc123"
SAMPLE_FLIGHT = MagicMock(
    id=SAMPLE_FLIGHT_ID,
    callsign="AI123",
    number="AI123",
    origin_airport_name="Indira Gandhi International Airport",
    origin_airport_iata="DEL",
    aircraft_model="Boeing 737-800",
    aircraft_code="B738",
    altitude=35000,
    ground_speed=450,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_airportsdata():
    """Mock the airportsdata.load() call so tests don't need the real package."""
    with patch("airportsdata.load") as mock_load:
        mock_load.return_value = {SAMPLE_AIRPORT_ICAO: SAMPLE_AIRPORT}
        yield mock_load


@pytest.fixture
def mock_fr_api():
    """Mock the FlightRadar24API instance used in tracker.py."""
    with patch("src.tracker.fr_api") as mock_api:
        yield mock_api


@pytest.fixture
def mock_flight():
    """Return a fresh MagicMock configured like a real flight object."""
    flight = MagicMock(
        id=SAMPLE_FLIGHT_ID,
        callsign="AI123",
        number="AI123",
        origin_airport_name="Indira Gandhi International Airport",
        origin_airport_iata="DEL",
        aircraft_model="Boeing 737-800",
        aircraft_code="B738",
        altitude=35000,
        ground_speed=450,
    )
    return flight


@pytest.fixture(autouse=True)
def reset_calculator_state():
    """
    Reset the module-level `previous_altitudes` dict before every test
    so that tests don't leak state into each other.
    """
    import src.calculator as calc

    calc.previous_altitudes.clear()
    yield


@pytest.fixture(autouse=True)
def reset_tracker_state():
    """
    Reset tracker module-level state (seen_flight_ids, first_loop) before
    every test so that tests don't leak state into each other.
    """
    import src.tracker as tracker

    tracker.seen_flight_ids.clear()
    tracker.first_loop = True
    yield