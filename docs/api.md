# API Reference

## Module: `main.py`

### `parse_args(argv: list[str] | None = None) -> argparse.Namespace`

Parses CLI arguments. Returns a namespace with `icao` (str or None) and `radius` (int or None).

```python
args = parse_args(["--icao", "VERC", "--radius", "5000"])
# args.icao == "VERC", args.radius == 5000
```

### `prompt_airport(airports: dict) -> dict`

Prompts the user for an ICAO code until a valid one is entered. Returns the airport dict with `name`, `lat`, `lon` keys.

### `prompt_radius() -> int`

Prompts the user for a positive integer radius in meters. Returns the integer.

### `main() -> None`

Entry point. Loads airport data, resolves inputs (CLI args or interactive prompts), and starts `run_tracking()`.

---

## Module: `src.calculator.py`

### `compute_incline_angle(flight_id: str, current_altitude_ft: float, ground_speed_kt: float) -> tuple[float | None, str]`

Calculates the climb/descent angle based on altitude change since the last call for the given flight.

**Parameters:**
- `flight_id` — Unique flight identifier (used as dictionary key)
- `current_altitude_ft` — Current altitude in feet
- `ground_speed_kt` — Current ground speed in knots

**Returns:** `(angle_degrees | None, label_string)`
- First call for a flight ID returns `(None, "Calculating...")`
- `None` angle also returned for zero/negative ground speed or zero time delta
- Label is one of: `"Calculating..."`, `"Level flight"`, `"Climbing at X.X deg"`, `"Descending at X.X deg"`

**Constants:**
- `NM_TO_FT = 6076.12` — Nautical miles to feet conversion
- `ANGLE_THRESHOLD_DEG = 0.3` — Angle below this is considered level flight

**Module-level state:**
- `previous_altitudes: dict[str, tuple[float, float]]` — Maps flight ID to `(timestamp, altitude)`

---

## Module: `src.flight_logger.py`

### `class FlightLogger`

Appends flight observations to a timestamped CSV file.

#### `__init__(self, airport_name: str, log_dir: Path | str | None = None)`

Creates the log directory if needed and opens the CSV file for appending. Writes headers if the file is new.

- `airport_name` — Used in the filename (spaces/slashes replaced with underscores)
- `log_dir` — Output directory (defaults to `flight_logs/`)

#### `filepath -> Path`

Read-only property returning the path to the current CSV file.

#### `log(self, timestamp: str, flight_id: str, callsign: str, departure_airport: str, aircraft_type: str, altitude: int | float | None, ground_speed: int | float | None, incline_label: str) -> None`

Writes a single observation row and flushes the file buffer.

#### `close(self) -> None`

Closes the underlying file handle. Idempotent (safe to call multiple times).

#### `__del__(self) -> None`

Calls `close()` on garbage collection.

### Helper Functions

#### `_build_filename(airport_name: str) -> str`

Returns `flight_log_<sanitized_name>_<date>.csv`.

#### `_headers() -> list[str]`

Returns CSV column headers: `timestamp, flight_id, callsign, departure_airport, aircraft_type, altitude_ft, ground_speed_kt, incline_label`.

#### `_ensure_log_dir(log_dir: Path) -> None`

Creates `log_dir` with `parents=True, exist_ok=True`.

---

## Module: `src.tracker.py`

### `play_alert() -> None`

Plays an audio alert: `winsound.MessageBeep()` on Windows, terminal bell (`\a`) on other platforms.

### `_get_flight_details(flight) -> tuple[str, str, str, int | None, str]`

Performs a detailed FlightRadar24 API lookup for the given flight. Falls back to basic attributes on failure.

**Returns:** `(name, departure_airport, aircraft_type, altitude, incline_label)`

### `_poll_once(bounds, airport_name: str, radius_meters: int, logger: FlightLogger | None = None) -> None`

Runs a single fetch-and-report cycle:
1. Fetches flights within `bounds`
2. For each flight, calls `_get_flight_details()` and prints flight info
3. Logs to CSV if a `logger` is provided
4. Plays alert if a new flight (not in `seen_flight_ids`) is detected on a non-first loop

### `run_tracking(airport_lat: float, airport_lon: float, airport_name: str, radius_meters: int) -> None`

Main tracking loop:
1. Creates a `FlightLogger` instance for CSV output
2. Creates geographic bounds via `fr_api.get_bounds_by_point()`
3. Loops indefinitely, calling `_poll_once()` every 3 seconds
4. Catches and reports nested exceptions without crashing

### Module-level State

| Variable | Type | Purpose |
|---|---|---|
| `fr_api` | `FlightRadar24API` | Singleton API client |
| `seen_flight_ids` | `set[str]` | Tracks all observed flight IDs |
| `first_loop` | `bool` | Suppresses new-flight alerts on initial poll |

### Constants

- `POLL_INTERVAL_SECONDS = 3` — Delay between API polls
- `SEPARATOR = "-" * 40` — Visual separator for terminal output
