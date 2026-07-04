import sys
import time
import math
import logging

try:
    import airportsdata
except ImportError:
    print("Missing dependency: 'airportsdata' is not installed.")
    print("Install it with:  pip install airportsdata")
    sys.exit(1)

from FlightRadarAPI import FlightRadar24API

# harmless "failed to decode Content-Encoding=gzip" warning.
# this used to happen because curl_cffi already auto-decompresses the response,
# so FlightRadarAPI own gzip.decompress() call fails on already-decoded
# bytes and logs a warning
# the data is fine so we only silence it
logging.getLogger("FlightRadarAPI.request").setLevel(logging.ERROR)

fr_api = FlightRadar24API()
airports = airportsdata.load('ICAO')

icao_code = input("Enter airport ICAO code (e.g. VERC for Ranchi): ").strip().upper()
airport = airports.get(icao_code)
if not airport:
    print(f"ICAO code '{icao_code}' not found. Exiting.")
    sys.exit(1)

AIRPORT_LAT = airport['lat']
AIRPORT_LON = airport['lon']
AIRPORT_NAME = airport['name']

RADIUS_METERS = int(input("Enter radius in meters: ").strip())

NM_TO_FT = 6076.12
ANGLE_THRESHOLD_DEG = 0.5  # below this, treat as level flight

print(f"\nStarting live tracking for {AIRPORT_NAME} ({icao_code})...")
print(f"Lat: {AIRPORT_LAT}, Lon: {AIRPORT_LON}")
print(f"Checking for flights within {RADIUS_METERS} meters radius every 3 seconds...\n")
print('---------------------------------------')

previous_altitudes = {} # used to track previous atltitude for getting angle climb/descent

# tracks every flight id ever seen, to detect brand-new arrivals
seen_flight_ids = set()
first_loop = True

def compute_incline_angle(flight_id, current_altitude_ft, ground_speed_kt):
    """
    Compares altitude now vs altitude ~3 seconds ago for this flight,
    and the horizontal distance covered in that time (from ground speed),
    to get the climb/descent angle in degrees.
    Returns (angle_deg, label) or (None, "Calculating...") if no prior sample yet.
    """
    now = time.time()
    prev = previous_altitudes.get(flight_id)
    previous_altitudes[flight_id] = (now, current_altitude_ft)

    if prev is None:
        return None, "Calculating..."

    prev_time, prev_altitude = prev
    dt = now - prev_time
    if dt <= 0:
        return None, "Calculating..."

    altitude_change_ft = current_altitude_ft - prev_altitude
    horizontal_ft = ground_speed_kt * (dt / 3600) * NM_TO_FT

    if horizontal_ft <= 0:
        return None, "Calculating..."

    angle_deg = math.degrees(math.atan2(altitude_change_ft, horizontal_ft))

    if angle_deg > ANGLE_THRESHOLD_DEG:
        label = f"Climbing at {angle_deg:.1f} deg "
    elif angle_deg < -ANGLE_THRESHOLD_DEG:
        label = f"Descending at {abs(angle_deg):.1f} deg"
    else:
        label = "Level flight" # less than 0.5 degrees

    return angle_deg, label


# 1) Create a box around the given airport
# 2) Get flights within those bounds
# 3) Get info for each flight (callsign, departure airport, aircraft type)
# 4) Loop every few seconds
try:
    bounds = fr_api.get_bounds_by_point(AIRPORT_LAT, AIRPORT_LON, RADIUS_METERS)

    while True:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Refreshing radar data...")
            flights = fr_api.get_flights(bounds=bounds)

            if not flights:
                print(f"No flights currently found within {RADIUS_METERS}m radius of {AIRPORT_NAME}.")
                print("-" * 40)
            else:
                print(f"Found {len(flights)} flight(s). Fetching details...\n")
                current_ids = set()

                for flight in flights:
                    current_ids.add(flight.id)
                    

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

                seen_flight_ids.update(current_ids)
                first_loop = False

        except Exception as inner_e:
            print(f"Error fetching active flight list: {inner_e}")

        time.sleep(3)

except KeyboardInterrupt:
    print("stopped by user.")
except Exception as e:
    print(f"{e}")