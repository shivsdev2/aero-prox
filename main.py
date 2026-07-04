import sys
import time
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
    exit(1)

AIRPORT_LAT = airport['lat']
AIRPORT_LON = airport['lon']
AIRPORT_NAME = airport['name']

RADIUS_METERS = int(input("Enter radius in meters: ").strip())

print(f"\nStarting live tracking for {AIRPORT_NAME} ({icao_code})...")
print(f"Lat: {AIRPORT_LAT}, Lon: {AIRPORT_LON}")
print(f"Checking for flights within {RADIUS_METERS} meters radius every 3 seconds...\n")
print('---------------------------------------')

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

                for flight in flights:
                    try:
                        details = fr_api.get_flight_details(flight)
                        flight.set_flight_details(details)
                        flight_name = flight.callsign if flight.callsign else "N/A"
                        departure_airport = flight.origin_airport_name if flight.origin_airport_name else "Unknown"
                        flight_type = flight.aircraft_model if flight.aircraft_model else "Unknown"
                        print(f"Flight Name: {flight_name}")
                        print(f"Departure Airport: {departure_airport}")
                        print(f"Flight Type (Aircraft): {flight_type}")
                        print("-" * 40)
                    except Exception:
                        print(f"Flight Name: {flight.number}")
                        print(f"Departure Airport: {flight.origin_airport_iata}")
                        print(f"Flight Type (Aircraft): {flight.aircraft_code}")
                        print("-" * 40)

        except Exception as inner_e:
            print(f"Error fetching active flight list: {inner_e}")

        time.sleep(3)


except KeyboardInterrupt:
    print("stopped by user.")
except Exception as e:
    print(f"{e}")