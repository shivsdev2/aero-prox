import argparse
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


def prompt_coordinates(label: str) -> float:
    """Prompt for a latitude or longitude value. Returns the float."""
    while True:
        raw = input(f"Enter your {label}: ").strip()
        try:
            value = float(raw)
            return value
        except ValueError:
            print("Please enter a valid decimal number.\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments, falling back to interactive prompts when omitted."""
    parser = argparse.ArgumentParser(
        description="Track active flights within a specified radius of any airport.",
    )
    parser.add_argument(
        "--icao",
        type=str,
        default=None,
        metavar="CODE",
        help="ICAO code of the airport (e.g. VERC for Ranchi). Prompts interactively if omitted.",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=None,
        metavar="METERS",
        help="Radius in meters around the airport. Prompts interactively if omitted.",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=None,
        metavar="DEGREES",
        help="Your current latitude (e.g. 23.34). Used for Sky Compass bearings. Prompts if omitted.",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=None,
        metavar="DEGREES",
        help="Your current longitude (e.g. 85.31). Used for Sky Compass bearings. Prompts if omitted.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    airports = airportsdata.load("ICAO")

    if args.icao:
        icao_code = args.icao.strip().upper()
        airport = airports.get(icao_code)
        if not airport:
            print(f"Error: ICAO code '{icao_code}' not found.")
            sys.exit(1)
    else:
        airport = prompt_airport(airports)

    if args.radius is not None:
        radius_meters = args.radius
        if radius_meters <= 0:
            print("Error: radius must be a positive integer.")
            sys.exit(1)
    else:
        radius_meters = prompt_radius()

    # Resolve user coordinates for Sky Compass.
    if args.lat is not None and args.lon is not None:
        user_lat = args.lat
        user_lon = args.lon
    else:
        print("\nSky Compass uses your location to tell you where to look.")
        print("You can skip this by passing --lat and --lon.\n")
        user_lat = prompt_coordinates("latitude")
        user_lon = prompt_coordinates("longitude")

    airport_name = airport["name"]
    airport_lat = airport["lat"]
    airport_lon = airport["lon"]

    print(f"\nStarting live tracking for {airport_name}...")
    print(f"Airport coordinates: {airport_lat}, {airport_lon}")
    print(f"Your coordinates:     {user_lat}, {user_lon}")
    print(
        f"Checking for flights within {radius_meters} meters radius every 3 seconds...\n"
    )
    print(SEPARATOR)

    try:
        run_tracking(
            airport_lat,
            airport_lon,
            airport_name,
            radius_meters,
            user_lat=user_lat,
            user_lon=user_lon,
        )
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
