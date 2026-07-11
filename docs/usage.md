# Usage

## Interactive Mode

Run the tracker with no arguments to use interactive prompts:

```bash
aero-prox
```

Or using Python module syntax:

```bash
python -m src.main
```

You will be prompted for:

1. **ICAO code** — The 4-letter airport identifier (e.g. `VERC` for Ranchi, `KJFK` for New York JFK)
2. **Radius (meters)** — The detection radius around the airport
3. 
Example session:

```
Enter airport ICAO code (e.g. VERC for Ranchi): VERC
Enter radius in meters: 5000

Starting live tracking for Birsa Munda Airport...
Lat: 23.3167, Lon: 85.3217
Checking for flights within 5000 meters radius every 3 seconds...

----------------------------------------
[2026-07-06 14:30:00] Refreshing radar data...
Found 3 flight(s). Fetching details...

Flight Name: ABC123
Departure Airport: Delhi Airport
Flight Type (Aircraft): B738
Altitude: 35000 ft
Incline/Descent: Level flight
----------------------------------------
```

## CLI Arguments

You can supply `--icao` and `--radius` directly to skip interactive prompts:

```bash
# Specify both
aero-prox --icao VERC --radius 5000

# Specify ICAO only (radius will prompt interactively)
aero-prox --icao KJFK

# Specify radius only (ICAO will prompt interactively)
aero-prox --radius 10000
```

### Argument Reference

| Argument | Type | Default | Description |
|---|---|---|---|
| `--icao CODE` | `str` | — | ICAO airport code (e.g. VERC). Prompts if omitted. |
| `--radius METERS` | `int` | — | Radius in meters. Must be positive. Prompts if omitted. |

Error handling:

```bash
# Invalid ICAO
$ aero-prox --icao XXXX
Error: ICAO code 'XXXX' not found.

# Invalid radius
$ aero-prox --radius -100
Error: radius must be a positive integer.
```

## Runtime Behaviour

Once running, the tracker polls the FlightRadar24 API every **3 seconds** and:

1. Fetches all flights within the defined geographic bounds
2. Retrieves detailed information for each flight (callsign, departure airport, aircraft type, altitude)
3. Calculates the incline/decline angle based on altitude changes between polls
4. Logs every flight observation to a CSV file in `flight_logs/`
5. Plays an audio alert when a previously unseen flight enters the radius

### Output Fields

Each flight cycle prints:

| Field | Description |
|---|---|
| Flight Name | Aircraft callsign (e.g. ABC123) |
| Departure Airport | Origin airport name |
| Flight Type (Aircraft) | Aircraft model code (e.g. B738, A320) |
| Altitude | Current altitude in feet |
| Incline/Descent | Climb/descent angle or "Level flight" |

### Incline/Descent Labels

| Label | Condition |
|---|---|
| `Calculating...` | First poll for this flight (no prior data) |
| `Level flight` | Angle within ±0.3° of horizontal |
| `Climbing at X.X deg` | Ascending at more than 0.3° |
| `Descending at X.X deg` | Descending at more than 0.3° |

## Stopping

Press **Ctrl+C** to stop tracking gracefully:

```
^C
Stopped by user.
```

## CSV Logging

Every flight observation is automatically appended to a CSV file:

```
flight_logs/flight_log_<airport_name>_<date>.csv
```

The CSV contains: timestamp, flight_id, callsign, departure_airport, aircraft_type, altitude_ft, ground_speed_kt, and incline_label.