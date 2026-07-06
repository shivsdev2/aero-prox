"""
Unit tests for src.tracker.

Tests cover:
- play_alert(): Windows vs non-Windows behaviour
- _get_flight_details(): successful detail lookup, fallback on failure
- _poll_once(): no flights, flights detected, new flight detection
- run_tracking(): bounds creation, loop behaviour (limited via side_effect)
- Module-level state management (seen_flight_ids, first_loop)
"""

from unittest.mock import MagicMock, patch

import pytest

from src.tracker import (
    _get_flight_details,
    _poll_once,
    play_alert,
    run_tracking,
)


class TestPlayAlert:
    """Tests for the play_alert function."""

    def test_windows_beep(self):
        """On Windows, play_alert should call winsound.MessageBeep()."""
        import src.tracker

        mock_winsound = MagicMock()
        with (
            patch("src.tracker.IS_WINDOWS", True),
            patch.object(src.tracker, "winsound", mock_winsound, create=True),
        ):
            play_alert()
            mock_winsound.MessageBeep.assert_called_once()

    @patch("src.tracker.IS_WINDOWS", False)
    def test_non_windows_bell(self, capsys):
        """On non-Windows, play_alert should print the terminal bell character."""
        play_alert()
        captured = capsys.readouterr()
        assert captured.out == "\a"


class TestGetFlightDetails:
    """Tests for the _get_flight_details helper."""

    def test_successful_detail_lookup(self, mock_fr_api, mock_flight):
        """When get_flight_details succeeds, details are extracted correctly."""
        mock_fr_api.get_flight_details.return_value = MagicMock()
        name, dep, acft, alt, incline = _get_flight_details(mock_flight)
        assert name == "AI123"
        assert dep == "Indira Gandhi International Airport"
        assert acft == "Boeing 737-800"
        assert alt == 35000

    def test_fallback_on_failure(self, mock_fr_api, mock_flight):
        """When get_flight_details raises, fallback fields are used."""
        mock_fr_api.get_flight_details.side_effect = RuntimeError("API error")
        name, dep, acft, alt, incline = _get_flight_details(mock_flight)
        assert name == "AI123"  # falls back to flight.number
        assert dep == "DEL"  # falls back to origin_airport_iata
        assert acft == "B738"  # falls back to aircraft_code
        assert alt == 35000

    def test_fallback_handles_missing_attributes(self, mock_fr_api):
        """Fallback should handle flights missing basic attributes gracefully."""
        minimal_flight = MagicMock(id="minimal", number="N/A")
        del minimal_flight.origin_airport_iata
        del minimal_flight.aircraft_code
        del minimal_flight.altitude
        del minimal_flight.ground_speed

        mock_fr_api.get_flight_details.side_effect = RuntimeError("API error")
        name, dep, acft, alt, incline = _get_flight_details(minimal_flight)
        # Should not crash; altitude defaults to 0
        assert dep == "Unknown"
        assert acft == "Unknown"


class TestPollOnce:
    """Tests for the _poll_once function."""

    def test_no_flights(self, mock_fr_api, capsys):
        """When no flights are returned, an appropriate message should be printed."""
        mock_fr_api.get_flights.return_value = []
        _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)
        captured = capsys.readouterr()
        assert "No flights" in captured.out
        assert "Test Airport" in captured.out

    def test_flights_detected(self, mock_fr_api, mock_flight, capsys):
        """When flights are returned, their details should be printed."""
        mock_fr_api.get_flights.return_value = [mock_flight]
        mock_fr_api.get_flight_details.return_value = MagicMock()
        _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)
        captured = capsys.readouterr()
        assert "AI123" in captured.out
        assert "Refreshing radar data" in captured.out

    def test_new_flight_detected(self, mock_fr_api, mock_flight, capsys):
        """A flight not in seen_flight_ids after first loop should trigger an alert."""
        # First poll: populate seen_flight_ids
        mock_fr_api.get_flights.return_value = [mock_flight]
        mock_fr_api.get_flight_details.return_value = MagicMock()
        _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)

        # Second poll with a different flight
        new_flight = MagicMock(
            id="new_flight_456",
            callsign="AI456",
            number="AI456",
            origin_airport_name="Mumbai Airport",
            origin_airport_iata="BOM",
            aircraft_model="Airbus A320",
            aircraft_code="A320",
            altitude=30000,
            ground_speed=400,
        )
        mock_fr_api.get_flights.return_value = [new_flight]
        captured = capsys.readouterr()  # discard first poll output
        _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)
        captured = capsys.readouterr()
        assert "New flight entered radius" in captured.out
        assert "new_flight_456" in captured.out

    def test_api_error_propagates(self, mock_fr_api):
        """_poll_once does not catch API errors - they propagate to run_tracking."""
        mock_fr_api.get_flights.side_effect = RuntimeError("Network error")
        with pytest.raises(RuntimeError, match="Network error"):
            _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)

    def test_new_flight_alert_plays_sound(self, mock_fr_api, mock_flight):
        """When a new flight is detected, play_alert should be called."""
        # This is tricky because play_alert is called inline.
        # We can verify it via the module's play_alert reference.
        with patch("src.tracker.play_alert") as mock_alert:
            # First poll: populate seen
            mock_fr_api.get_flights.return_value = [mock_flight]
            mock_fr_api.get_flight_details.return_value = MagicMock()
            _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)

            # Second poll with new flight
            new_flight = MagicMock(id="brand_new", callsign="AI999")
            new_flight.number = "AI999"
            new_flight.origin_airport_iata = "CCU"
            new_flight.aircraft_code = "B738"
            new_flight.altitude = 25000
            new_flight.ground_speed = 300

            mock_fr_api.get_flights.return_value = [new_flight]
            _poll_once(MagicMock(), 23.3, 85.3, "Test Airport", 5000)
            mock_alert.assert_called_once()


class TestRunTracking:
    """Tests for the run_tracking function."""

    def test_creates_bounds_and_loops(self, mock_fr_api):
        """run_tracking should create bounds and enter the polling loop."""
        mock_fr_api.get_bounds_by_point.return_value = "mock_bounds"
        mock_fr_api.get_flights.return_value = []

        call_count = [0]

        def stop_after_one(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise KeyboardInterrupt

        with (
            patch("src.tracker.time.sleep"),
            patch("src.tracker._poll_once", side_effect=stop_after_one),
            patch("src.tracker.FlightLogger"),  # avoid actual file I/O
        ):
            try:
                run_tracking(23.3, 85.3, "Test", 5000)
            except KeyboardInterrupt:
                pass  # expected – used to break the infinite loop

        mock_fr_api.get_bounds_by_point.assert_called_once_with(23.3, 85.3, 5000)

    def test_loop_error_does_not_crash(self, mock_fr_api, capsys):
        """An exception inside the loop should be caught and printed, not crash."""
        mock_fr_api.get_bounds_by_point.return_value = "mock_bounds"
        call_count = [0]

        def raise_then_stop(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Temporary error")
            raise KeyboardInterrupt

        with (
            patch("src.tracker.time.sleep"),
            patch("src.tracker._poll_once", side_effect=raise_then_stop),
            patch("src.tracker.FlightLogger"),  # avoid actual file I/O
        ):
            try:
                run_tracking(23.3, 85.3, "Test", 5000)
            except KeyboardInterrupt:
                pass  # expected – used to break the infinite loop

        captured = capsys.readouterr()
        assert "Error fetching active flight list" in captured.out
