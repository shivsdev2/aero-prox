import time
import platform
import logging

from FlightRadarAPI import FlightRadar24API

from src.calculator import compute_incline_angle

# harmless "failed to decode Content-Encoding=gzip" warning.
# this used to happen because curl_cffi already auto-decompresses the response,
# so FlightRadarAPI own gzip.decompress() call fails on already-decoded
# bytes and logs a warning
# the data is fine so we only silence it

# Check the operating system once at startup.
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    import winsound
    
logging.getLogger("FlightRadarAPI.request").setLevel(logging.ERROR)

fr_api = FlightRadar24API()

# tracks every flight id ever seen, to detect brand-new arrivals
seen_flight_ids = set()
first_loop = True


def run_tracking(airport_lat, airport_lon, airport_name, radius_meters):
    """
    1) Create a box around the given airport
    2) Get flights within those bounds
    3) Get info for each flight (callsign, departure airport, aircraft type)
    4) Loop every few seconds
    """
    global first_loop

    bounds = fr_api.get_bounds_by_point(airport_lat, airport_lon, radius_meters)

    while True:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Refreshing radar data...")
            flights = fr_api.get_flights(bounds=bounds)
            
            if not flights:
                print(f"No flights currently found within {radius_meters}m radius of {airport_name}.")
                print("-" * 40)
            else:
                print(f"Found {len(flights)} flight(s). Fetching details...\n")
                current_ids = set()
                new_flight_detected = False
                
                for flight in flights:
                    current_ids.add(flight.id)
                    
                    if not first_loop and flight.id not in seen_flight_ids:
                        new_flight_detected = True
                        print(f"[INFO] New flight entered radius: {flight.id}")
                        print("-" * 40)
                        
                    try:
                        details = fr_api.get_flight_details(flight)
                        flight.set_flight_details(details)
                        flight_name = flight.callsign if flight.callsign else "N/A"
                        departure_airport = flight.origin_airport_name if flight.origin_airport_name else "Unknown"
                        flight_type = flight.aircraft_model if flight.aircraft_model else "Unknown"
                        altitude = flight.altitude
                        ground_speed = flight.ground_speed

                        _, incline_label = compute_incline_angle(flight.id, altitude, ground_speed)

                        print(f"Flight Name: {flight_name}")
                        print(f"Departure Airport: {departure_airport}")
                        print(f"Flight Type (Aircraft): {flight_type}")
                        print(f"Altitude: {altitude} ft")
                        print(f"Incline/Descent: {incline_label}")
                        print("-" * 40)
                    except Exception:
                        altitude = getattr(flight, "altitude", 0)
                        ground_speed = getattr(flight, "ground_speed", 0)
                        _, incline_label = compute_incline_angle(flight.id, altitude, ground_speed)

                        print(f"Flight Name: {flight.number}")
                        print(f"Departure Airport: {flight.origin_airport_iata}")
                        print(f"Flight Type (Aircraft): {flight.aircraft_code}")
                        print(f"Altitude: {altitude} ft")
                        print(f"Incline/Descent: {incline_label}")
                        print("-" * 40)
                
                if new_flight_detected:
                    play_alert()

                seen_flight_ids.update(current_ids)
                first_loop = False

        except Exception as inner_e:
            print(f"Error fetching active flight list: {inner_e}")

        time.sleep(3)
    
def play_alert():
    if IS_WINDOWS:
        winsound.MessageBeep()
    else:
        print("\a", end="", flush=True)