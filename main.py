import sys

try:
    import airportsdata
except ImportError:
    print("Missing dependency: 'airportsdata' is not installed.")
    print("Install it with:  pip install airportsdata")
    sys.exit(1)

from src.tracker import run_tracking


def main():
    airports = airportsdata.load('ICAO')

    icao_code = input("Enter airport ICAO code (e.g. VERC for Ranchi): ").strip().upper()
    airport = airports.get(icao_code)
    if not airport:
        print(f"ICAO code '{icao_code}' not found. Exiting.")
        sys.exit(1)

    airport_lat = airport['lat']
    airport_lon = airport['lon']
    airport_name = airport['name']

    radius_meters = int(input("Enter radius in meters: ").strip())

    print(f"\nStarting live tracking for {airport_name} ({icao_code})...")
    print(f"Lat: {airport_lat}, Lon: {airport_lon}")
    print(f"Checking for flights within {radius_meters} meters radius every 3 seconds...\n")
    print('---------------------------------------')

    try:
        run_tracking(airport_lat, airport_lon, airport_name, radius_meters)
    except KeyboardInterrupt:
        print("stopped by user.")
    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    main()
