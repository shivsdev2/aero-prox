"""
Sky Compass — a natural-language guide that tells you where to look in the sky.

For each flight detected within the tracking radius, the Sky Compass calculates
the bearing and distance from the airport, then generates a human-readable
sentence describing where to look and what you'd see.
"""

import math

# Compass direction labels for bearing angles.
COMPASS_DIRECTIONS = [
    ("N", 0, 11.25),
    ("NNE", 11.25, 33.75),
    ("NE", 33.75, 56.25),
    ("ENE", 56.25, 78.75),
    ("E", 78.75, 101.25),
    ("ESE", 101.25, 123.75),
    ("SE", 123.75, 146.25),
    ("SSE", 146.25, 168.75),
    ("S", 168.75, 191.25),
    ("SSW", 191.25, 213.75),
    ("SW", 213.75, 236.25),
    ("WSW", 236.25, 258.75),
    ("W", 258.75, 281.25),
    ("WNW", 281.25, 303.75),
    ("NW", 303.75, 326.25),
    ("NNW", 326.25, 348.75),
    ("N", 348.75, 360.0),
]

# Earth radius in meters (WGS-84).
EARTH_RADIUS_M = 6_371_000


def _bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing from point 1 to point 2, in degrees
    (0 = north, 90 = east, etc.).
    """
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)

    x = math.sin(dlon_r) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(
        lat2_r
    ) * math.cos(dlon_r)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance in meters between two lat/lon points."""
    dlat_r = math.radians(lat2 - lat1)
    dlon_r = math.radians(lon2 - lon1)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)

    a = (
        math.sin(dlat_r / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon_r / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def _compass_label(bearing: float) -> str:
    """Convert a bearing in degrees to a compass direction label (e.g. 0 → 'N', 90 → 'E')."""
    for label, start, end in COMPASS_DIRECTIONS:
        if start <= bearing < end:
            return label
    return "N"  # fallback (shouldn't happen)


def _distance_description(distance_m: float) -> str:
    """Format a distance in meters to a human-readable string."""
    if distance_m < 1000:
        return f"{int(round(distance_m))}m"
    km = distance_m / 1000
    if km < 10:
        return f"{km:.1f}km"
    return f"{int(round(km))}km"


def _altitude_description(altitude_ft: int | float | None) -> str:
    """Format altitude in feet to a human-readable flight level string."""
    if altitude_ft is None or altitude_ft == 0:
        return "on the ground"
    fl = round(altitude_ft / 100)
    return f"at FL{fl}"


def _incline_description(incline_label: str) -> str:
    """Convert an incline label to a short, natural phrase."""
    if "Climbing" in incline_label:
        return "climbing"
    if "Descending" in incline_label:
        return "descending"
    if "Calculating" in incline_label:
        return "just appeared"
    return "cruising level"


def _heading_description(heading: float | None) -> str:
    """Convert a heading in degrees to a compass direction."""
    if heading is None:
        return ""
    if not isinstance(heading, int | float):
        return ""
    return _compass_label(heading)


def describe_flight(
    airport_lat: float,
    airport_lon: float,
    flight_lat: float,
    flight_lon: float,
    callsign: str,
    aircraft_type: str,
    altitude: int | float | None,
    incline_label: str,
    heading: float | None = None,
) -> str:
    """
    Generate a single natural-language sentence describing where to look
    for a given flight relative to the airport.
    """
    bearing = _bearing_degrees(airport_lat, airport_lon, flight_lat, flight_lon)
    distance_m = _haversine_distance_m(airport_lat, airport_lon, flight_lat, flight_lon)
    direction = _compass_label(bearing)
    dist_str = _distance_description(distance_m)
    alt_str = _altitude_description(altitude)
    incline_str = _incline_description(incline_label)

    # Build the sentence.
    parts = [f"• {callsign}"]
    parts.append(f"({aircraft_type})")
    parts.append(f"— look {direction}")
    parts.append(f"({bearing:.0f}°)")
    parts.append(f"about {dist_str} away,")
    parts.append(f"{alt_str},")
    parts.append(incline_str)

    if heading is not None:
        hdg = _heading_description(heading)
        if hdg:
            parts.append(f"heading {hdg}")

    return " ".join(parts) + "."


def generate_compass_report(
    airport_lat: float,
    airport_lon: float,
    airport_name: str,
    flights: list,
) -> str:
    """
    Generate the full Sky Compass report for a list of flights.

    Each flight in the list must have at minimum:
        .id, .latitude, .longitude, .altitude, .ground_speed
    and optionally .heading, .callsign, .aircraft_model / .aircraft_code.

    Returns a multi-line string ready to print.
    """
    lines = []
    lines.append(f"🔭 Sky Compass — {airport_name}")
    lines.append("")

    valid_flights = []
    for flight in flights:
        flight_lat = getattr(flight, "latitude", None)
        flight_lon = getattr(flight, "longitude", None)
        if flight_lat is not None and flight_lon is not None:
            valid_flights.append(flight)

    if not valid_flights:
        lines.append("No flights in your sky right now.")
        return "\n".join(lines)

    n = len(valid_flights)
    lines.append(f"{n} flight{'s' if n != 1 else ''} in your sky right now:")
    lines.append("")

    for flight in valid_flights:
        callsign = getattr(flight, "callsign", None) or getattr(flight, "number", "N/A")
        aircraft_type = (
            getattr(flight, "aircraft_model", None)
            or getattr(flight, "aircraft_code", None)
            or "Unknown"
        )
        altitude = getattr(flight, "altitude", None)
        heading = getattr(flight, "heading", None)
        incline_label = getattr(flight, "_incline_label", "Calculating...")

        sentence = describe_flight(
            airport_lat=airport_lat,
            airport_lon=airport_lon,
            flight_lat=flight_lat,
            flight_lon=flight_lon,
            callsign=callsign,
            aircraft_type=aircraft_type,
            altitude=altitude,
            incline_label=incline_label,
            heading=heading,
        )
        lines.append(sentence)

    lines.append("")
    lines.append("📡 Look up and enjoy the sky!")
    return "\n".join(lines)
