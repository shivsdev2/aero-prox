"""
Interactive live map for aero-prox.

Writes a self-contained HTML file (Leaflet via CDN) on each poll cycle,
showing the target airport, tracking-radius circle, and live aircraft markers.
"""

import html
import json
from pathlib import Path

DEFAULT_MAP_PATH = Path("live_map.html")
REFRESH_SECONDS = 3


def _flight_marker_data(flight) -> dict | None:
    """Extract map marker fields from a flight object, or None if position is missing."""
    lat = getattr(flight, "latitude", None)
    lon = getattr(flight, "longitude", None)
    if lat is None or lon is None:
        return None

    origin = (
        getattr(flight, "origin_airport_name", None)
        or getattr(flight, "origin_airport_iata", None)
        or "Unknown"
    )
    destination = (
        getattr(flight, "destination_airport_name", None)
        or getattr(flight, "destination_airport_iata", None)
        or "Unknown"
    )

    return {
        "id": flight.id,
        "callsign": getattr(flight, "callsign", None)
        or getattr(flight, "number", "N/A"),
        "lat": lat,
        "lon": lon,
        "altitude": getattr(flight, "altitude", None),
        "incline": getattr(flight, "_incline_label", "Calculating..."),
        "origin": origin,
        "destination": destination,
    }


def render_live_map_html(
    *,
    airport_lat: float,
    airport_lon: float,
    airport_name: str,
    radius_meters: int,
    flights: list,
    timestamp: str,
    refresh_seconds: int = REFRESH_SECONDS,
) -> str:
    """Return the full HTML document for the live map."""
    markers = [data for flight in flights if (data := _flight_marker_data(flight))]

    config = {
        "airport": {
            "name": airport_name,
            "lat": airport_lat,
            "lon": airport_lon,
        },
        "radiusMeters": radius_meters,
        "flights": markers,
        "timestamp": timestamp,
    }
    config_json = (
        json.dumps(config).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )

    safe_airport_name = html.escape(airport_name)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="{refresh_seconds}">
  <title>aero-prox live map — {safe_airport_name}</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    .map-title {{
      position: absolute;
      top: 10px;
      left: 50px;
      z-index: 1000;
      background: rgba(255, 255, 255, 0.9);
      padding: 6px 10px;
      border-radius: 4px;
      font-family: sans-serif;
      font-size: 14px;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    }}
  </style>
</head>
<body>
  <div class="map-title" id="title"></div>
  <div id="map"></div>
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>
  <script>
    const config = {config_json};

    document.getElementById("title").textContent =
      `${{config.airport.name}} — ${{config.flights.length}} flight(s) — ${{config.timestamp}}`;

    const map = L.map("map").setView([config.airport.lat, config.airport.lon], 11);
    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }}).addTo(map);

    L.circle([config.airport.lat, config.airport.lon], {{
      radius: config.radiusMeters,
      color: "#2563eb",
      fillColor: "#3b82f6",
      fillOpacity: 0.08,
      weight: 2,
    }}).addTo(map);

    L.marker([config.airport.lat, config.airport.lon])
      .addTo(map)
      .bindPopup(`<b>${{config.airport.name}}</b><br>Target airport`);

    config.flights.forEach((flight) => {{
      const altitude = flight.altitude != null ? `${{flight.altitude}} ft` : "N/A";
      const popup = [
        `<b>${{flight.callsign}}</b>`,
        `Flight ID: ${{flight.id}}`,
        `Altitude: ${{altitude}}`,
        `Incline/Descent: ${{flight.incline}}`,
        `From: ${{flight.origin}}`,
        `To: ${{flight.destination}}`,
      ].join("<br>");
      L.circleMarker([flight.lat, flight.lon], {{
        radius: 8,
        color: "#dc2626",
        fillColor: "#ef4444",
        fillOpacity: 0.9,
        weight: 2,
      }}).addTo(map).bindPopup(popup);
    }});
  </script>
</body>
</html>
"""


class LiveMap:
    """Writes an interactive HTML map file on each update."""

    def __init__(
        self,
        airport_lat: float,
        airport_lon: float,
        airport_name: str,
        radius_meters: int,
        output_path: Path | str | None = None,
    ) -> None:
        self._airport_lat = airport_lat
        self._airport_lon = airport_lon
        self._airport_name = airport_name
        self._radius_meters = radius_meters
        self._filepath = Path(output_path) if output_path else DEFAULT_MAP_PATH

    @property
    def filepath(self) -> Path:
        """Return the path to the live map HTML file."""
        return self._filepath

    def update(self, flights: list, timestamp: str) -> None:
        """Regenerate the HTML map for the current flight snapshot."""
        html = render_live_map_html(
            airport_lat=self._airport_lat,
            airport_lon=self._airport_lon,
            airport_name=self._airport_name,
            radius_meters=self._radius_meters,
            flights=flights,
            timestamp=timestamp,
        )
        self._filepath.write_text(html, encoding="utf-8")
