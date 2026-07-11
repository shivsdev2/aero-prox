import logging
import platform
import sys
import time

from FlightRadarAPI import FlightRadar24API
from plyer import notification

# Support both direct execution and module execution
if __name__ == "__main__" and __package__ is None:
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from calculator import compute_incline_angle
    from flight_logger import FlightLogger
    from sky_compass import generate_compass_report
else:
    from src.calculator import compute_incline_angle
    from src.flight_logger import FlightLogger
    from src.sky_compass import generate_compass_report

# Silence a harmless "failed to decode Content-Encoding=gzip" warning.
# curl_cffi already auto-decompresses responses, so FlightRadarAPI's own
# gzip.decompress() call fails on already-decoded bytes and logs a warning.
# The data itself is unaffected.
logging.getLogger("FlightRadarAPI.request").setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Check the operating system once at startup.
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winsound

POLL_INTERVAL_SECONDS = 3
SEPARATOR = "-" * 40

fr_api = FlightRadar24API()

# Tracks every flight id ever seen, to detect brand-new arrivals.
seen_flight_ids = set()
first_loop = True


def send_notification(title, message):
    notification.notify(title=title, message=message)


def play_alert():
    """Play a simple audio alert (system beep on Windows, terminal bell elsewhere)."""
    if IS_WINDOWS:
        winsound.MessageBeep()
    else:
        print("\a", end="", flush=True)


def _get_flight_details(flight):
    """
    Return (name, departure_airport, aircraft_type, altitude, incline_label)
    for a flight, using the detailed API lookup with a fallback to the
    basic fields already present on the flight object if that lookup fails.
    """
    try:
        details = fr_api.get_flight_details(flight)
        flight.set_flight_details(details)

        name = flight.callsign or "N/A"
        departure_airport = flight.origin_airport_name or "Unknown"
        aircraft_type = flight.aircraft_model or "Unknown"
        altitude = flight.altitude
        ground_speed = flight.ground_speed
    except Exception as e:
        log.warning("Falling back to basic flight fields for %s: %s", flight.id, e)
        name = getattr(flight, "number", "N/A")
        departure_airport = getattr(flight, "origin_airport_iata", "Unknown")
        aircraft_type = getattr(flight, "aircraft_code", "Unknown")
        altitude = getattr(flight, "altitude", 0)
        ground_speed = getattr(flight, "ground_speed", 0)

    _, incline_label = compute_incline_angle(flight.id, altitude, ground_speed)
    return name, departure_airport, aircraft_type, altitude, incline_label


def _print_flight(name, departure_airport, aircraft_type, altitude, incline_label):
    print(f"Flight Name: {name}")
    print(f"Departure Airport: {departure_airport}")
    print(f"Flight Type (Aircraft): {aircraft_type}")
    print(f"Altitude: {altitude} ft")
    print(f"Incline/Descent: {incline_label}")
    print(SEPARATOR)


def _poll_once(
    bounds,
    airport_lat,
    airport_lon,
    airport_name,
    radius_meters,
    logger: FlightLogger | None = None,
    user_lat=None,
    user_lon=None,
):
    """Run a single fetch-and-report cycle. Returns nothing; mutates module state."""
    global first_loop

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Refreshing radar data...")
    flights = fr_api.get_flights(bounds=bounds)

    if not flights:
        print(
            f"No flights currently found within {radius_meters}m radius of {airport_name}."
        )
        print(SEPARATOR)
        return

    print(f"Found {len(flights)} flight(s). Fetching details...\n")

    current_ids = set()
    new_flight_detected = False
    new_flights = list()

    for flight in flights:
        current_ids.add(flight.id)
        new_flight_detected = False

        if not first_loop and flight.id not in seen_flight_ids:
            new_flight_detected = True
            print(f"[INFO] New flight entered radius: {flight.id}")
            print(SEPARATOR)

        name, departure_airport, aircraft_type, altitude, incline_label = (
            _get_flight_details(flight)
        )

        if new_flight_detected:
            new_flights.append(name)

        # Attach incline label to the flight object for Sky Compass.
        flight._incline_label = incline_label

        _print_flight(name, departure_airport, aircraft_type, altitude, incline_label)

        # Log to CSV if a logger is available
        if logger is not None:
            ground_speed = getattr(flight, "ground_speed", None)
            logger.log(
                timestamp=timestamp,
                flight_id=flight.id,
                callsign=name,
                departure_airport=departure_airport,
                aircraft_type=aircraft_type,
                altitude=altitude,
                ground_speed=ground_speed,
                incline_label=incline_label,
            )

    if new_flights:
        play_alert()
        sample_flights = ", ".join(new_flights[:3])
        others = f" and {len(new_flights) - 3} others" if len(new_flights) > 3 else ""
        send_notification(f"{len(new_flights)} new flight(s) entered radius", f"{sample_flights}{others}")

    # Print the Sky Compass report (relative to user location if provided).
    compass_lat = user_lat if user_lat is not None else airport_lat
    compass_lon = user_lon if user_lon is not None else airport_lon
    report = generate_compass_report(compass_lat, compass_lon, airport_name, flights)
    print(report)
    print(SEPARATOR)

    seen_flight_ids.update(current_ids)
    first_loop = False


def run_tracking(
    airport_lat,
    airport_lon,
    airport_name,
    radius_meters,
    user_lat=None,
    user_lon=None,
):
    """
    1) Create a box around the given airport
    2) Get flights within those bounds
    3) Get info for each flight (callsign, departure airport, aircraft type)
    4) Log every flight to a CSV file
    5) Print Sky Compass report (relative to user location if provided)
    6) Loop every few seconds
    """
    logger = FlightLogger(airport_name)
    log.info("Flight history CSV: %s", logger.filepath)

    bounds = fr_api.get_bounds_by_point(airport_lat, airport_lon, radius_meters)

    while True:
        try:
            _poll_once(
                bounds,
                airport_lat,
                airport_lon,
                airport_name,
                radius_meters,
                logger=logger,
                user_lat=user_lat,
                user_lon=user_lon,
            )
        except Exception as inner_e:
            print(f"Error fetching active flight list: {inner_e}")

        time.sleep(POLL_INTERVAL_SECONDS)