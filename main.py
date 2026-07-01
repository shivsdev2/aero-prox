import time
from FlightRadarAPI import FlightRadar24API

fr_api = FlightRadar24API()

# # change these value to your airports
# i have used the cordinates of Ranchi IXR.
# to get airport cordinates ->
#                             1)https://www.google.com/maps
#                             2)search for your aiport
#                             3)right click on the airport on the map
#                             4)at the top you will see the latitude and longitude of the airport.

AIRPORT_LAT = 23.3142
AIRPROT_LON = 85.3218 

RADIUS_METERS = 10000

print("Starting live tracking...")
print(f"Checking for flights within {RADIUS_METERS} meters radius of Ranchi Airport every 2 seconds...\n")
print('---------------------------------------')

# 1) Create a box around the given Airport 
# 2) Get flights within those bounds.
# 3) Get information for each flight (callsign, departure airport, aircraft type)
# 4) Loops every two seconds.
try:
    bounds = fr_api.get_bounds_by_point(AIRPORT_LAT, AIRPROT_LON, RADIUS_METERS)
    
    while True:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Refreshing radar data...")
# 2)
            flights = fr_api.get_flights(bounds=bounds)
            
            if not flights:
                print("No flights currently found under,", RADIUS_METERS, "radius of  Airport.")
                print("-" * 40)
            else:
                print(f"Found {len(flights)} flight(s). Fetching details...\n")
                
# 3)  
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
                        
                    except Exception as detail_err:
                        print(f"Flight Name: {flight.number}")
                        print(f"Departure Airport: {flight.origin_airport_iata}")
                        print(f"Flight Type (Aircraft): {flight.aircraft_code}")
                        print("-" * 40)
                        
        except Exception as inner_e:
            print(f"Error fetching active flight list: {inner_e}")
        time.sleep(3)
# IGNORE THE 
# *APIRequest.get_content: failed to decode Content-Encoding='gzip' for https://data-cloud.flightradar24.com/zones/fcgi/feed.js (Not a gzipped file (b'{"')). Assuming the transport already decompressed and returning raw bytes.*
except KeyboardInterrupt:
    print("stopped by user.")
except Exception as e:
    print(f"{e}")
