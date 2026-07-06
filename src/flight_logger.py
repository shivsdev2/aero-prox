"""
CSV flight history logger for aero-prox.

Writes every flight seen during tracking to a timestamped CSV file
for post-hoc analysis.
"""

import csv
import time
from pathlib import Path

# Default output directory for log files.
DEFAULT_LOG_DIR = Path("flight_logs")


def _ensure_log_dir(log_dir: Path) -> None:
    """Create the log directory if it doesn't exist."""
    log_dir.mkdir(parents=True, exist_ok=True)


def _build_filename(airport_name: str) -> str:
    """Generate a filename like 'flight_log_VERC_2026-07-06.csv'."""
    safe_name = airport_name.replace(" ", "_").replace("/", "_")
    date_str = time.strftime("%Y-%m-%d")
    return f"flight_log_{safe_name}_{date_str}.csv"


def _headers() -> list[str]:
    return [
        "timestamp",
        "flight_id",
        "callsign",
        "departure_airport",
        "aircraft_type",
        "altitude_ft",
        "ground_speed_kt",
        "incline_label",
    ]


class FlightLogger:
    """
    Appends flight observations to a CSV file.

    Usage:
        logger = FlightLogger("Birsa Munda Airport")
        logger.log(timestamp, flight_id, callsign, ...)
        logger.close()
    """

    def __init__(self, airport_name: str, log_dir: Path | str | None = None) -> None:
        self._log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        _ensure_log_dir(self._log_dir)

        filename = _build_filename(airport_name)
        self._filepath = self._log_dir / filename

        file_exists = self._filepath.exists()
        self._file = open(self._filepath, "a", newline="")  # noqa: SIM115
        self._writer = csv.writer(self._file)

        if not file_exists:
            self._writer.writerow(_headers())

    @property
    def filepath(self) -> Path:
        """Return the path to the current CSV log file."""
        return self._filepath

    def log(
        self,
        timestamp: str,
        flight_id: str,
        callsign: str,
        departure_airport: str,
        aircraft_type: str,
        altitude: int | float | None,
        ground_speed: int | float | None,
        incline_label: str,
    ) -> None:
        """Write a single flight observation row to the CSV."""
        self._writer.writerow(
            [
                timestamp,
                flight_id,
                callsign,
                departure_airport,
                aircraft_type,
                altitude if altitude is not None else "",
                ground_speed if ground_speed is not None else "",
                incline_label,
            ]
        )
        self._file.flush()

    def close(self) -> None:
        """Close the underlying CSV file."""
        if not self._file.closed:
            self._file.close()

    def __del__(self) -> None:
        self.close()
