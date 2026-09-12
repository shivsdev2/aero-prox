"""Unit tests for src.live_map."""

import json
import re
from unittest.mock import MagicMock

import pytest

from src.live_map import LiveMap, render_live_map_html


def _extract_config(html: str) -> dict:
    match = re.search(r"const config = (\{.*?\});", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


@pytest.fixture
def map_flight():
    flight = MagicMock(
        id="abc123",
        callsign="AI123",
        latitude=23.35,
        longitude=85.40,
        altitude=35000,
        origin_airport_name="Delhi",
        destination_airport_name="Ranchi",
    )
    flight._incline_label = "Climbing at 2.5 deg "
    return flight


class TestRenderLiveMapHtml:
    def test_includes_airport_and_radius(self):
        html = render_live_map_html(
            airport_lat=23.3,
            airport_lon=85.3,
            airport_name="Test Airport",
            radius_meters=5000,
            flights=[],
            timestamp="2026-01-01 12:00:00",
        )
        assert "Test Airport" in html
        assert '"radiusMeters": 5000' in html
        assert "leaflet" in html.lower()

    def test_includes_flight_marker_data(self, map_flight):
        html = render_live_map_html(
            airport_lat=23.3,
            airport_lon=85.3,
            airport_name="Test Airport",
            radius_meters=5000,
            flights=[map_flight],
            timestamp="2026-01-01 12:00:00",
        )
        assert "AI123" in html
        assert "abc123" in html
        assert "Climbing at 2.5 deg" in html
        assert "Delhi" in html
        assert "Ranchi" in html

    def test_skips_flights_without_position(self, map_flight):
        no_pos = MagicMock(id="missing", callsign="XX000", latitude=None, longitude=None)
        html = render_live_map_html(
            airport_lat=23.3,
            airport_lon=85.3,
            airport_name="Test Airport",
            radius_meters=5000,
            flights=[no_pos, map_flight],
            timestamp="2026-01-01 12:00:00",
        )
        config = _extract_config(html)
        assert len(config["flights"]) == 1
        assert config["flights"][0]["id"] == "abc123"


class TestLiveMap:
    def test_writes_html_file(self, map_flight, tmp_path):
        output = tmp_path / "map.html"
        live_map = LiveMap(23.3, 85.3, "Test Airport", 5000, output_path=output)
        live_map.update([map_flight], "2026-01-01 12:00:00")

        assert output.exists()
        content = output.read_text(encoding="utf-8")
        assert "Test Airport" in content
        assert "AI123" in content

    def test_updates_on_empty_flights(self, tmp_path):
        output = tmp_path / "map.html"
        live_map = LiveMap(23.3, 85.3, "Test Airport", 5000, output_path=output)
        live_map.update([], "2026-01-01 12:00:00")

        content = output.read_text(encoding="utf-8")
        config = _extract_config(content)
        assert config["flights"] == []
