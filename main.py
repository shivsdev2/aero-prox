import sys

try:
    import airportsdata
except ImportError:
    print("Missing dependency: 'airportsdata' is not installed.")
    print("Install it with:  pip install airportsdata")
    sys.exit(1)

from src.tracker import run_tracking

SEPARATOR = "-" * 40


def prompt_airport(airports: dict) -> dict:
    while True:
        icao_code = (
            input("Enter airport ICAO code (e.g. VERC for Ranchi): ").strip().upper()
        )
        airport = airports.get(icao_code)
        if airport:
            return airport
        print(f"ICAO code '{icao_code}' not found. Please try again.\n")


def prompt_radius() -> int:
    while True:
        raw = input("Enter radius in meters: ").strip()
        try:
            radius = int(raw)
            if radius <= 0:
                raise ValueError
            return radius
        except ValueError:
            print("Please enter a positive whole number.\n")


def main() -> None:
    airports = airportsdata.load("ICAO")

    airport = prompt_airport(airports)
    radius_meters = prompt_radius()

    airport_name = airport["name"]
    airport_lat = airport["lat"]
    airport_lon = airport["lon"]

    print(f"\nStarting live tracking for {airport_name}...")
    print(f"Lat: {airport_lat}, Lon: {airport_lon}")
    print(
        f"Checking for flights within {radius_meters} meters radius every 3 seconds...\n"
    )
    print(SEPARATOR)

    try:
        run_tracking(airport_lat, airport_lon, airport_name, radius_meters)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
