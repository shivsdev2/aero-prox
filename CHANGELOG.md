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
