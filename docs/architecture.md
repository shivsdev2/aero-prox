# Architecture

## Module Overview

```
aero-prox/
├── main.py                 # Entry point: CLI parsing + interactive prompts
├── src/
│   ├── __init__.py         # Package marker
│   ├── calculator.py       # Incline/decline angle computation
│   ├── flight_logger.py    # CSV flight history logging
│   └── tracker.py          # Core tracking loop, API interaction, alerting
├── tests/
│   ├── conftest.py         # Shared pytest fixtures and mocks
│   ├── test_calculator.py  # Calculator unit tests
│   ├── test_flight_logger.py  # FlightLogger unit tests
│   ├── test_main.py        # CLI + prompt + main() tests
│   └── test_tracker.py     # Tracker unit tests (mocked API)
├── docs/                   # Project documentation
└── flight_logs/            # Output directory for CSV logs
```

## Data Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Input  │────▶│   main.py        │────▶│  run_tracking() │
│ (ICAO,radius)│     │ (parse_args /    │     │  in tracker.py  │
└─────────────┘     │  prompt_*)        │     └────────┬────────┘
                    └──────────────────┘              │
                                                      ▼
                                            ┌─────────────────┐
                                            │  _poll_once()    │
                                            │  in tracker.py   │
                                            └────────┬─────────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────┐
                          │                           │                       │
                          ▼                           ▼                       ▼
                 ┌─────────────────┐       ┌──────────────────┐    ┌─────────────────┐
                 │ FlightRadar24API │       │ compute_incline_ │    │  FlightLogger   │
                 │ (external pkg)   │       │ angle()          │    │  (CSV writer)   │
                 └─────────────────┘       │ in calculator.py │    └─────────────────┘
                                           └──────────────────┘
```

## Module Responsibilities

### `main.py`

- Parses CLI arguments with `argparse`
- Loads airport data via `airportsdata`
- Validates user input (ICAO existence, radius > 0)
- Calls `run_tracking()` with resolved coordinates
- Handles `KeyboardInterrupt` and unexpected exceptions at the top level

### `src/calculator.py`

- Maintains a module-level `previous_altitudes` dictionary mapping flight IDs to `(timestamp, altitude)` tuples
- `compute_incline_angle()` calculates the vertical angle using `atan2(altitude_change, horizontal_distance)`
- Horizontal distance is derived from ground speed and elapsed time
- Returns `(angle_degrees, label_string)` — label is one of: "Calculating...", "Level flight", "Climbing at X deg", "Descending at X deg"

### `src/flight_logger.py`

- `FlightLogger` class writes flight observations to timestamped CSV files
- Creates `flight_logs/` directory on instantiation
- Appends rows with `flush()` after each write for crash safety
- Handles `None` altitude/ground speed gracefully (writes empty string)

### `src/tracker.py`

- `FlightRadar24API` client (singleton `fr_api`)
- `seen_flight_ids` set tracks all observed flight IDs to detect new arrivals
- `_get_flight_details()` performs detailed API lookup with fallback to basic fields
- `_poll_once()` runs a single fetch-and-report cycle
- `run_tracking()` creates bounds, instantiates `FlightLogger`, and runs the infinite loop

## State Management

Module-level mutable state is used in two modules:

| Module | Variable | Purpose |
|---|---|---|
| `tracker.py` | `seen_flight_ids` | Set of all flight IDs ever seen (new flight detection) |
| `tracker.py` | `first_loop` | Boolean flag to suppress new-flight alerts on the first poll |
| `calculator.py` | `previous_altitudes` | Dict of `{flight_id: (timestamp, altitude)}` for angle calculation |

This state is reset between tests via autouse fixtures in `conftest.py`.

## Error Handling Strategy

- **API failures** in `_poll_once()` are caught and logged, the loop continues
- **Detailed lookup failures** in `_get_flight_details()` fall back to basic flight fields
- **Missing attributes** on flight objects use `getattr()` with defaults
- **Top-level exceptions** in `main()` print a message and exit with code 1
- **KeyboardInterrupt** stops the loop gracefully with a message

## Audio Alerts

- **Windows**: Uses `winsound.MessageBeep()`
- **Linux/macOS**: Prints `\a` (ASCII bell) to the terminal with flush
- Triggered only when a flight ID not in `seen_flight_ids` is detected on a non-first loop
