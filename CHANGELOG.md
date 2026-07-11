# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [2.1.0] - 2026-07-11

### Added
- **Desktop Notifications:** Added cross-platform desktop notifications via `plyer` when a new flight enters the tracking radius. Shows flight count and callsigns on Windows, macOS, and Linux.

### Changed
- **Module Structure:** Moved `main.py` from project root to `src/main.py` for proper package organization. All internal imports updated to use `src.` module paths.
- `pyproject.toml`: Updated console script entry point from `main:main` to `src.main:main`.
- `src/main.py`: Updated import to use `from src.tracker import run_tracking`.
- `src/tracker.py`: Updated imports to use `src.calculator`, `src.flight_logger`, and `src.sky_compass` module paths.
- `tests/test_main.py`: Updated all mock patch paths from `main.*` to `src.main.*`.
- `docs/api.md`: Updated module reference from `main.py` to `src.main`.
- `docs/usage.md`: Updated usage examples to use `aero-prox` command and `python -m src.main`.
- `docs/index.md`: Updated quick start to use `aero-prox` command.

## [2.0.0] - 2026-07-06

### Added
- **Sky Compass:** New `src/sky_compass.py` module that generates natural-language sentences telling you where to look for each flight. Calculates bearing, distance, compass direction, flight level, and incline state relative to your current location.
- **User Coordinates:** `main.py` now prompts for your latitude and longitude (or accepts `--lat`/`--lon` CLI arguments). The Sky Compass uses these coordinates to give accurate bearing and distance directions from *your* location. Falls back to airport coordinates if not provided.
- **30 Sky Compass Tests:** Added `tests/test_sky_compass.py` with 29 tests covering bearing calculations, haversine distance, compass labels, distance/altitude/incline formatting, sentence generation, and full report generation.

### Changed
- `src/tracker.py`: `_poll_once()` and `run_tracking()` accept optional `user_lat`/`user_lon` parameters passed through to Sky Compass. Compass bearings are relative to the user's location when provided.
- `main.py`: Added `--lat` and `--lon` CLI arguments and interactive prompts. `main()` passes user coordinates to `run_tracking()`.
- Updated tests in `tests/test_main.py` and `tests/test_tracker.py` for the new parameters and prompts.

## [1.2.0] - 2026-07-06

### Added
- **CLI Arguments:** `main.py` now accepts `--icao CODE` and `--radius METERS` flags for non-interactive usage. Falls back to interactive prompts when omitted.
- **CSV Flight History Logging:** Every flight seen during tracking is automatically logged to a timestamped CSV file in the `flight_logs/` directory. Each row records timestamp, flight ID, callsign, departure airport, aircraft type, altitude, ground speed, and incline/descent label.
- **`src/flight_logger.py`:** New module providing the `FlightLogger` class for appending flight observations to CSV files with automatic header creation and directory management.
- **Logger Tests:** Added `tests/test_flight_logger.py` with 12 tests covering filename generation, header correctness, row appending, None-value handling, existing file appending, and cleanup.

### Changed
- `src/tracker.py`: `_poll_once()` now accepts an optional `logger` parameter; `run_tracking()` creates a `FlightLogger` instance and passes it to each poll cycle.
- `tests/test_tracker.py`: Updated `run_tracking` tests to mock `FlightLogger` and avoid real file I/O.

## [1.1.1] - 2026-07-06

### Added
- **`pyproject.toml`:** Replaced `requirements.txt` with a standard `pyproject.toml` defining project metadata, dependencies, and build configuration.
- **Pre-commit Hooks:** Added `.pre-commit-config.yaml` with hooks for trailing whitespace, end-of-file newlines, YAML/TOML validation, large file checks, merge conflict detection, and Ruff linting/formatting.
- **GitHub Actions CI:** Created `.github/workflows/ci.yml` to automatically run the full pytest suite on every push and pull request to `main` across Python 3.10–3.14.
- **Ruff Configuration:** Integrated Ruff linter and formatter settings into `pyproject.toml` with rules for pycodestyle, pyflakes, isort, naming, and pyupgrade.

### Changed
- Migrated from `pytest.ini` to `[tool.pytest.ini_options]` in `pyproject.toml`.
- Updated `.gitignore` to exclude `.ruff_cache/` and pre-commit backup files.

## [1.1.0] - 2026-07-06

### Added
- **Automated Test Suite:** Introduced a comprehensive unit testing framework using `pytest` located in the new `tests/` directory.
- **Calculator Tests:** Added `test_calculator.py` to handle test assertions for level flight, climbing, descending, and boundary mathematical edge cases (like zero or negative ground speeds).
- **Tracker Mocking:** Added `test_tracker.py` using `unittest.mock` to simulate real-time FlightRadar24 API data streams, platform-specific audio alerts, and error propagation boundaries without triggering live network calls.
- **Shared Test Configuration:** Implemented a unified `conftest.py` with auto-triggering execution fixtures to isolate test environments and thoroughly scrub cache metrics between test runs.
- **Test Optimization:** Added a global `pytest.ini` structure to configure baseline regression testing defaults.

## [1.0.0] - 2026-07-06

### Added
- flight tracking inside radius using the `FlightRadar24API` https://pypi.org/project/FlightRadarAPI/.
- Automatic cordinates filling using ICAO code via `airports` module.
- Live polling every 3 seconds.
- dependency error handling for missing packages at startup.
- Incline/Decline angle check using previous altitudes.
- Audio alerts (windwos/unix) when new flight enters the radius.
- Added `CONTRIBUTING.md` guidelines and initial codebase structure.

### Changed
- improved code base for robustness