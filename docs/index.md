# aero-prox Documentation

**aero-prox** is a Python-based flight tracking tool that monitors active flights within a specified radius of any airport using the [FlightRadar24 API](https://pypi.org/project/FlightRadarAPI/). It provides real-time terminal updates, incline/decline angle calculations, audio alerts for new arrivals, and CSV flight history logging.

---

## Contents

| Section | Description |
|---|---|
| [Installation](installation.md) | Setup instructions, dependencies, and environment configuration |
| [Usage](usage.md) | Interactive and CLI usage, examples, and tips |
| [Architecture](architecture.md) | Module layout, data flow, and design decisions |
| [Testing](testing.md) | Running tests, test structure, and writing new tests |
| [API Reference](api.md) | Public module interfaces, classes, and functions |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/shivsdev2/aero-prox.git
cd aero-prox

# Install dependencies
pip install -r requirements.txt

# Run the tracker
python main.py
```

Then follow the interactive prompts to enter an airport ICAO code and radius.

---

## Project Status

**Version:** 1.2.0 | **Tests:** 55 passing | **Python:** 3.10–3.14

[![CI](https://github.com/shivsdev2/aero-prox/actions/workflows/ci.yml/badge.svg)](https://github.com/shivsdev2/aero-prox/actions/workflows/ci.yml)
