"""
Unit tests for src.sky_compass.

Tests cover:
- _bearing_degrees(): known bearing calculations
- _haversine_distance_m(): known distance calculations
- _compass_label(): direction labels for bearings
- _distance_description(): human-readable distance formatting
- _altitude_description(): human-readable altitude formatting
- _incline_description(): incline label to phrase conversion
- describe_flight(): complete sentence generation
- generate_compass_report(): full report with/without flights
"""

from unittest.mock import MagicMock

from src.sky_compass import (
    _altitude_description,
    _bearing_degrees,
    _compass_label,
    _distance_description,
    _haversine_distance_m,
    _incline_description,
    describe_flight,
    generate_compass_report,
)


class TestBearingDegrees:
    """Tests for the _bearing_degrees helper."""

    def test_north(self):
        """Point directly north should give bearing ~0/360."""
        angle = _bearing_degrees(0, 0, 1, 0)
        assert 0 <= angle <= 1 or 359 <= angle <= 360

    def test_east(self):
        """Point directly east should give bearing ~90."""
        angle = _bearing_degrees(0, 0, 0, 1)
        assert 89 <= angle <= 91

    def test_south(self):
        """Point directly south should give bearing ~180."""
        angle = _bearing_degrees(0, 0, -1, 0)
        assert 179 <= angle <= 181

    def test_west(self):
        """Point directly west should give bearing ~270."""
        angle = _bearing_degrees(0, 0, 0, -1)
        assert 269 <= angle <= 271

    def test_same_point(self):
        """Same point should give bearing 0."""
        angle = _bearing_degrees(23.3, 85.3, 23.3, 85.3)
        assert angle == 0


class TestHaversineDistance:
    """Tests for the _haversine_distance_m helper."""

    def test_zero_distance(self):
        """Same point should give 0 distance."""
        d = _haversine_distance_m(23.3, 85.3, 23.3, 85.3)
        assert d == 0

    def test_known_distance(self):
        """Distance from equator to 1 degree north should be ~111km."""
        d = _haversine_distance_m(0, 0, 1, 0)
        assert 110_000 < d < 112_000  # ~111km per degree


class TestCompassLabel:
    """Tests for the _compass_label helper."""

    def test_north(self):
        assert _compass_label(0) == "N"
        assert _compass_label(360) == "N"

    def test_east(self):
        assert _compass_label(90) == "E"

    def test_south(self):
        assert _compass_label(180) == "S"

    def test_west(self):
        assert _compass_label(270) == "W"

    def test_boundaries(self):
        """Check boundary values between direction sectors."""
        assert _compass_label(11.24) == "N"
        assert _compass_label(11.25) == "NNE"
        assert _compass_label(33.74) == "NNE"
        assert _compass_label(33.75) == "NE"


class TestDistanceDescription:
    """Tests for the _distance_description helper."""

    def test_meters(self):
        assert _distance_description(500) == "500m"
        assert _distance_description(999) == "999m"

    def test_small_km(self):
        assert _distance_description(1500) == "1.5km"
        assert _distance_description(9999) == "10.0km"

    def test_large_km(self):
        assert _distance_description(10000) == "10km"
        assert _distance_description(42195) == "42km"


class TestAltitudeDescription:
    """Tests for the _altitude_description helper."""

    def test_cruising(self):
        assert _altitude_description(35000) == "at FL350"

    def test_low_altitude(self):
        assert _altitude_description(500) == "at FL5"

    def test_ground(self):
        assert _altitude_description(0) == "on the ground"

    def test_none(self):
        assert _altitude_description(None) == "on the ground"


class TestInclineDescription:
    """Tests for the _incline_description helper."""

    def test_climbing(self):
        assert _incline_description("Climbing at 2.5 deg") == "climbing"

    def test_descending(self):
        assert _incline_description("Descending at 3.1 deg") == "descending"

    def test_calculating(self):
        assert _incline_description("Calculating...") == "just appeared"

    def test_level(self):
        assert _incline_description("Level flight") == "cruising level"


class TestDescribeFlight:
    """Tests for the describe_flight function."""

    def test_basic_description(self):
        """A flight to the east with typical data."""
        sentence = describe_flight(
            airport_lat=23.3,
            airport_lon=85.3,
            flight_lat=23.3,
            flight_lon=85.8,  # ~55km east
            callsign="AI123",
            aircraft_type="B738",
            altitude=35000,
            incline_label="Level flight",
            heading=270.0,
        )
        assert "AI123" in sentence
        assert "B738" in sentence
        assert "look E" in sentence or "look" in sentence
        assert "FL350" in sentence
        assert "cruising level" in sentence
        assert "heading" in sentence

    def test_descending_flight_west(self):
        """A descending flight to the west."""
        sentence = describe_flight(
            airport_lat=23.3,
            airport_lon=85.3,
            flight_lat=23.3,
            flight_lon=84.8,  # ~55km west
            callsign="6E204",
            aircraft_type="A320",
            altitude=10000,
            incline_label="Descending at 3.0 deg",
            heading=90.0,
        )
        assert "6E204" in sentence
        assert "A320" in sentence
        assert "descending" in sentence
        assert "FL100" in sentence

    def test_no_heading(self):
        """A flight without heading should not include heading in the sentence."""
        sentence = describe_flight(
            airport_lat=23.3,
            airport_lon=85.3,
            flight_lat=23.3,
            flight_lon=85.8,
            callsign="AI123",
            aircraft_type="B738",
            altitude=35000,
            incline_label="Level flight",
            heading=None,
        )
        assert "heading" not in sentence


class TestGenerateCompassReport:
    """Tests for the generate_compass_report function."""

    def test_no_flights(self):
        """With an empty flight list, the report should say 'No flights'."""
        report = generate_compass_report(23.3, 85.3, "Test Airport", [])
        assert "No flights" in report
        assert "Test Airport" in report

    def test_with_flights(self):
        """With flights, the report should include their details."""
        flight = MagicMock(
            id="abc123",
            callsign="AI123",
            number="AI123",
            aircraft_model="B738",
            altitude=35000,
            heading=270.0,
            latitude=23.3,
            longitude=85.8,
            _incline_label="Level flight",
        )
        report = generate_compass_report(23.3, 85.3, "Test Airport", [flight])
        assert "AI123" in report
        assert "B738" in report
        assert "Test Airport" in report
        assert "Look up and enjoy" in report

    def test_flight_skipped_no_position(self):
        """A flight without lat/lon should be skipped."""
        flight_no_pos = MagicMock(id="no_pos", latitude=None, longitude=None)
        report = generate_compass_report(23.3, 85.3, "Test Airport", [flight_no_pos])
        assert "No flights" in report  # no valid flights

    def test_multiple_flights(self):
        """With multiple flights, the count should be correct."""
        f1 = MagicMock(
            id="f1", callsign="AI1", latitude=23.3, longitude=85.8, altitude=35000
        )
        f2 = MagicMock(
            id="f2", callsign="AI2", latitude=23.3, longitude=84.8, altitude=10000
        )
        report = generate_compass_report(23.3, 85.3, "Test Airport", [f1, f2])
        assert "2 flights" in report
        assert "AI1" in report
        assert "AI2" in report
