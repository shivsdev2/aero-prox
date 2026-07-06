# Testing

## Running Tests

```bash
# Run the full test suite
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_calculator.py

# Run a specific test class
python -m pytest tests/test_calculator.py::TestComputeInclineAngle

# Run a specific test method
python -m pytest tests/test_calculator.py::TestComputeInclineAngle::test_climbing_detected

# Run with coverage report (if pytest-cov is installed)
python -m pytest --cov=src
```

## Test Suite Overview

The test suite contains **55 tests** across 4 modules:

| Module | Tests | What it covers |
|---|---|---|
| `test_calculator.py` | 9 | `compute_incline_angle()` — first call, level flight, climbing, descending, edge cases, formula correctness |
| `test_flight_logger.py` | 12 | `FlightLogger` — file creation, appending, None values, idempotent close, default directory |
| `test_main.py` | 13 | `parse_args()`, `prompt_airport()`, `prompt_radius()`, `main()` — valid input, invalid input, CLI args, exceptions |
| `test_tracker.py` | 21 | `play_alert()`, `_get_flight_details()`, `_poll_once()`, `run_tracking()` — alerts, API calls, new flight detection, error resilience |

## Test Structure

Tests use `pytest` with `unittest.mock` for isolating external dependencies:

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures
├── test_calculator.py       # Calculator tests
├── test_flight_logger.py    # FlightLogger tests
├── test_main.py             # Main module tests
└── test_tracker.py          # Tracker tests
```

## Fixtures (conftest.py)

Shared fixtures are defined in `tests/conftest.py`:

| Fixture | Scope | Purpose |
|---|---|---|
| `mock_airportsdata` | function | Mocks `airportsdata.load()` with a sample airport |
| `mock_fr_api` | function | Mocks `FlightRadar24API` with configurable return values |
| `mock_flight` | function | Creates a mock flight object with attributes like `id`, `callsign`, `altitude` |
| `reset_calculator_state` (autouse) | function | Clears `previous_altitudes` before each test |
| `reset_tracker_state` (autouse) | function | Clears `seen_flight_ids` and resets `first_loop` before each test |

## Writing New Tests

### Pattern 1: Testing a pure function

```python
from src.calculator import compute_incline_angle

class TestMyFeature:
    def test_expected_behaviour(self):
        angle, label = compute_incline_angle("TEST001", 35000, 450)
        assert label == "Level flight"
```

### Pattern 2: Testing with mocked API

Use the existing fixtures from `conftest.py`:

```python
def test_custom_scenario(self, mock_fr_api, mock_flight):
    mock_fr_api.get_flights.return_value = [mock_flight]
    mock_fr_api.get_flight_details.return_value = {...}
    # your test logic here
```

### Pattern 3: Testing file I/O (FlightLogger)

Use `tmp_path` fixture from pytest:

```python
def test_custom_logging(self, tmp_path):
    logger = FlightLogger("Test Airport", log_dir=tmp_path)
    logger.log("2026-01-01 12:00:00", "FL123", ...)
    content = (tmp_path / logger.filepath.name).read_text()
    assert "FL123" in content
```

## Mocking Guidelines

- **API calls**: Mock `FlightRadar24API.get_flights()` and `get_flight_details()` using `mock_fr_api`
- **Airport data**: Mock `airportsdata.load()` using `mock_airportsdata`
- **User input**: Patch `builtins.input` with `side_effect` for multiple prompts
- **Platform specifics**: Mock `winsound` via `patch.object(src.tracker, "winsound", create=True)` on Linux
- **File system**: Use `tmp_path` for temp directories, or patch `FlightLogger` directly

## Pre-submission Checklist

Before submitting changes:

1. Run the full test suite: `python -m pytest`
2. Run the linter: `ruff check src/ tests/`
3. Run the formatter: `ruff format src/ tests/`
4. Run pre-commit hooks: `pre-commit run --all-files`
