"""
aero-prox - Flight proximity notifier with desktop alerts.
"""

import time
import logging
from datetime import datetime
from typing import List, Dict, Any

from FlightRadarAPI import FlightRadarAPI
from notifications import NotificationManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightTracker:
    """Track flights and send notifications for new ones within range."""

    def __init__(self, latitude: float, longitude: float, radius_km: float = 50.0):
        """
        Initialize flight tracker.

        Args:
            latitude: Center latitude for detection
            longitude: Center longitude for detection
            radius_km: Detection radius in kilometers
        """
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.client = FlightRadarAPI()
        self.notifier = NotificationManager()
        self.seen_flights: set = set()

    def get_nearby_flights(self) -> List[Dict[str, Any]]:
        """Fetch flights within the detection radius."""
        try:
            # Get flights in the area
            flights = self.client.get_flights(
                bounds={
                    "lat1": self.latitude - 0.5,
                    "lat2": self.latitude + 0.5,
                    "lon1": self.longitude - 0.5,
                    "lon2": self.longitude + 0.5,
                }
            )
            return flights
        except Exception as e:
            logger.error(f"Error fetching flights: {e}")
            return []

    def is_within_radius(self, flight_lat: float, flight_lon: float) -> bool:
        """Check if flight coordinates are within detection radius."""
        # Simple distance calculation (approximate)
        lat_diff = abs(flight_lat - self.latitude)
        lon_diff = abs(flight_lon - self.longitude)
        distance = (lat_diff ** 2 + lon_diff ** 2) ** 0.5 * 111  # Approx km per degree
        return distance <= self.radius_km

    def process_flights(self):
        """Process flights and send notifications for new ones."""
        flights = self.get_nearby_flights()
        new_flights = []

        for flight in flights:
            flight_id = flight.get('id', flight.get('flight', ''))
            if not flight_id:
                continue

            if flight_id not in self.seen_flights:
                self.seen_flights.add(flight_id)
                new_flights.append(flight)

        if new_flights:
            for flight in new_flights:
                self._send_notification(flight)
            logger.info(f"Detected {len(new_flights)} new flight(s)")

        return new_flights

    def _send_notification(self, flight: Dict[str, Any]):
        """Send desktop notification for a flight."""
        flight_id = flight.get('id', flight.get('flight', 'Unknown'))
        altitude = flight.get('altitude', flight.get('alt', 'N/A'))
        speed = flight.get('speed', flight.get('spd', 'N/A'))
        heading = flight.get('heading', flight.get('track', 'N/A'))

        title = f"✈️ New Flight Detected!"
        message = (
            f"Flight: {flight_id}\n"
            f"Altitude: {altitude} ft\n"
            f"Speed: {speed} kts\n"
            f"Heading: {heading}°"
        )

        if self.notifier.is_supported():
            self.notifier.send(title, message)
        else:
            print(f"\n{title}\n{'-' * 30}\n{message}\n")

    def run(self, interval: int = 60):
        """Run the tracker continuously."""
        logger.info(
            f"Starting flight tracker at ({self.latitude}, {self.longitude}) "
            f"radius: {self.radius_km}km"
        )

        try:
            while True:
                self.process_flights()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Stopped by user")


if __name__ == "__main__":
    # Default location (example: Lima, Peru)
    # You can change these coordinates to your location
    tracker = FlightTracker(
        latitude=-12.0464,
        longitude=-77.0428,
        radius_km=50.0
    )
    tracker.run(interval=30)  # Check every 30 seconds