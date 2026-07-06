# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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



## [1.1.0] - 2026-07-06

### Added
- **Automated Test Suite:** Introduced a comprehensive unit testing framework using `pytest` located in the new `tests/` directory.
- **Calculator Tests:** Added `test_calculator.py` to handle test assertions for level flight, climbing, descending, and boundary mathematical edge cases (like zero or negative ground speeds).
- **Tracker Mocking:** Added `test_tracker.py` using `unittest.mock` to simulate real-time FlightRadar24 API data streams, platform-specific audio alerts, and error propagation boundaries without triggering live network calls.
- **Shared Test Configuration:** Implemented a unified `conftest.py` with auto-triggering execution fixtures to isolate test environments and thoroughly scrub cache metrics between test runs.
- **Test Optimization:** Added a global `pytest.ini` structure to configure baseline regression testing defaults.


## [1.1.1] - 2026-07-06

### Added
- **`pyproject.toml`:** Replaced `requirements.txt` with a standard `pyproject.toml` defining project metadata, dependencies, and build configuration.
- **Pre-commit Hooks:** Added `.pre-commit-config.yaml` with hooks for trailing whitespace, end-of-file newlines, YAML/TOML validation, large file checks, merge conflict detection, and Ruff linting/formatting.
- **GitHub Actions CI:** Created `.github/workflows/ci.yml` to automatically run the full pytest suite on every push and pull request to `main` across Python 3.10–3.14.
- **Ruff Configuration:** Integrated Ruff linter and formatter settings into `pyproject.toml` with rules for pycodestyle, pyflakes, isort, naming, and pyupgrade.

### Changed
- Migrated from `pytest.ini` to `[tool.pytest.ini_options]` in `pyproject.toml`.
- Updated `.gitignore` to exclude `.ruff_cache/` and pre-commit backup files.
