# Installation

## Prerequisites

- **Python 3.10 or later** (tested up to 3.14)
- **pip** package manager

## Install from Source

```bash
# Clone the repository
git clone https://github.com/shivsdev2/aero-prox.git
cd aero-prox

# Install dependencies
pip install -r requirements.txt
```

## Install with pip (editable)

For development, install the package in editable mode:

```bash
pip install -e .
```

This makes the `aero-prox` console entry point available and links the source code so changes take effect immediately.

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `FlightRadarAPI` | ≥1.0 | Real-time flight data from FlightRadar24 |
| `airportsdata` | ≥1.0 | ICAO airport code lookup and coordinates |

All dependencies are listed in `requirements.txt` and `pyproject.toml`.

## Verify Installation

```bash
python -c "from FlightRadarAPI import FlightRadar24API; print('OK')"
python -c "import airportsdata; print('OK')"
```

## Development Dependencies

For contributors:

```bash
pip install -e ".[dev]"
```

This installs:

- `pytest` — test runner
- `pytest-anyio` — async test support
- `ruff` — linter and formatter
- `pre-commit` — git hook framework

Then set up pre-commit hooks:

```bash
pre-commit install
```
