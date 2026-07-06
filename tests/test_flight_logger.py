"""
Unit tests for src.flight_logger.

Tests cover:
- _build_filename: safe filename generation
- _headers: correct column names
- FlightLogger: file creation, header writing, row logging, close
"""

import csv
import time

from src.flight_logger import (
    DEFAULT_LOG_DIR,
    FlightLogger,
    _build_filename,
    _ensure_log_dir,
    _headers,
)


class TestBuildFilename:
    """Tests for the _build_filename helper."""

    def test_basic_filename(self):
        """A simple airport name should produce a clean filename."""
        name = _build_filename("Test Airport")
        date_str = time.strftime("%Y-%m-%d")
        assert name == f"flight_log_Test_Airport_{date_str}.csv"

    def test_special_characters_replaced(self):
        """Slashes and spaces should be replaced with underscores."""
        name = _build_filename("LAX/Intl")
        date_str = time.strftime("%Y-%m-%d")
        assert name == f"flight_log_LAX_Intl_{date_str}.csv"


class TestHeaders:
    """Tests for the _headers helper."""

    def test_headers_are_correct(self):
        """The header list should contain the expected columns."""
        headers = _headers()
        assert headers == [
            "timestamp",
            "flight_id",
            "callsign",
            "departure_airport",
            "aircraft_type",
            "altitude_ft",
            "ground_speed_kt",
            "incline_label",
        ]


class TestEnsureLogDir:
    """Tests for the _ensure_log_dir helper."""

    def test_creates_directory(self, tmp_path):
        """The directory should be created if it doesn't exist."""
        test_dir = tmp_path / "new_logs"
        assert not test_dir.exists()
        _ensure_log_dir(test_dir)
        assert test_dir.exists()

    def test_existing_directory(self, tmp_path):
        """An existing directory should not raise an error."""
        test_dir = tmp_path / "existing_logs"
        test_dir.mkdir()
        _ensure_log_dir(test_dir)  # should not raise


class TestFlightLogger:
    """Tests for the FlightLogger class."""

    def test_creates_file_with_headers(self, tmp_path):
        """A new CSV file should be created with headers."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.close()

        assert logger.filepath.exists()
        with open(logger.filepath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) >= 1
        assert rows[0] == [
            "timestamp",
            "flight_id",
            "callsign",
            "departure_airport",
            "aircraft_type",
            "altitude_ft",
            "ground_speed_kt",
            "incline_label",
        ]

    def test_appends_row(self, tmp_path):
        """Logging a flight should append a data row."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.log(
            timestamp="2026-07-06 12:00:00",
            flight_id="abc123",
            callsign="AI123",
            departure_airport="DEL",
            aircraft_type="B738",
            altitude=35000,
            ground_speed=450,
            incline_label="Level flight",
        )
        logger.close()

        with open(logger.filepath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2  # header + 1 data row
        assert rows[1] == [
            "2026-07-06 12:00:00",
            "abc123",
            "AI123",
            "DEL",
            "B738",
            "35000",
            "450",
            "Level flight",
        ]

    def test_appends_multiple_rows(self, tmp_path):
        """Multiple log calls should append multiple rows."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.log("t1", "f1", "CS1", "DEP1", "A1", 10000, 200, "Climbing")
        logger.log("t2", "f2", "CS2", "DEP2", "A2", 20000, 300, "Descending")
        logger.close()

        with open(logger.filepath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3  # header + 2 data rows

    def test_handles_none_altitude_and_speed(self, tmp_path):
        """None altitude/ground_speed should be written as empty strings."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.log(
            timestamp="t1",
            flight_id="f1",
            callsign="CS1",
            departure_airport="DEP1",
            aircraft_type="A1",
            altitude=None,
            ground_speed=None,
            incline_label="Calculating...",
        )
        logger.close()

        with open(logger.filepath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert rows[1][5] == ""  # altitude_ft
        assert rows[1][6] == ""  # ground_speed_kt

    def test_appends_to_existing_file(self, tmp_path):
        """If the file already exists, new rows should be appended without re-writing headers."""
        filepath = tmp_path / _build_filename("Test Airport")
        # Write headers manually first
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(_headers())
            writer.writerow(["old", "f0", "CS0", "DEP0", "A0", "0", "0", "Level"])

        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.log("new", "f1", "CS1", "DEP1", "A1", 100, 10, "Climbing")
        logger.close()

        with open(filepath, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3  # header + old row + new row
        assert rows[2][1] == "f1"

    def test_filepath_property(self, tmp_path):
        """The filepath property should return the correct path."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        expected = tmp_path / _build_filename("Test Airport")
        assert logger.filepath == expected
        logger.close()

    def test_close_idempotent(self, tmp_path):
        """Calling close() multiple times should not raise."""
        logger = FlightLogger("Test Airport", log_dir=tmp_path)
        logger.close()
        logger.close()  # second call should be safe

    def test_default_log_dir(self):
        """When no log_dir is provided, DEFAULT_LOG_DIR should be used."""
        logger = FlightLogger("Test Airport")
        assert DEFAULT_LOG_DIR in logger.filepath.parents
        logger.close()
        # Clean up
        import shutil

        if DEFAULT_LOG_DIR.exists():
            shutil.rmtree(DEFAULT_LOG_DIR)
