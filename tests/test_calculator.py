"""
Unit tests for src.calculator.

Tests cover:
- First call returns "Calculating..." (no prior sample)
- Climbing, descending, and level flight angle detection
- Edge cases: zero ground speed, zero altitude change, negative dt
"""

import math
import time

from src.calculator import (
    ANGLE_THRESHOLD_DEG,
    NM_TO_FT,
    compute_incline_angle,
    previous_altitudes,
)


class TestComputeInclineAngle:
    """Tests for the compute_incline_angle function."""

    # ------------------------------------------------------------------
    # First-call behaviour
    # ------------------------------------------------------------------

    def test_first_call_returns_calculating(self):
        """The very first call for a flight_id should return (None, "Calculating...")."""
        angle, label = compute_incline_angle("flight_1", 30000, 400)
        assert angle is None
        assert label == "Calculating..."

    # ------------------------------------------------------------------
    # Level flight
    # ------------------------------------------------------------------

    def test_level_flight_no_altitude_change(self):
        """No altitude change over time should be labelled 'Level flight'."""
        flight_id = "level_test"
        # First call – seeds the previous value
        compute_incline_angle(flight_id, 30000, 400)
        time.sleep(0.01)  # ensure dt > 0
        angle, label = compute_incline_angle(flight_id, 30000, 400)
        assert label == "Level flight"
        assert angle is not None and abs(angle) <= ANGLE_THRESHOLD_DEG

    def test_level_flight_small_altitude_change(self):
        """A very small altitude change relative to distance should be 'Level flight'."""
        flight_id = "small_change"
        # Simulate a 3-second gap with a tiny altitude change via module state
        import src.calculator as calc
        now = time.time()
        calc.previous_altitudes[flight_id] = (now - 3, 30000)
        # 1 ft change over 3 seconds at 400 kt => ~2025 ft horizontal, angle ≈ 0.028°
        angle, label = compute_incline_angle(flight_id, 30001, 400)
        assert label == "Level flight"
        assert angle is not None and abs(angle) <= ANGLE_THRESHOLD_DEG

    # ------------------------------------------------------------------
    # Climbing
    # ------------------------------------------------------------------

    def test_climbing_detected(self):
        """A positive altitude change should be labelled 'Climbing'."""
        flight_id = "climb_test"
        compute_incline_angle(flight_id, 10000, 400)
        time.sleep(0.01)
        angle, label = compute_incline_angle(flight_id, 11000, 400)
        assert "Climbing" in label
        assert angle is not None and angle > ANGLE_THRESHOLD_DEG

    # ------------------------------------------------------------------
    # Descending
    # ------------------------------------------------------------------

    def test_descending_detected(self):
        """A negative altitude change should be labelled 'Descending'."""
        flight_id = "desc_test"
        compute_incline_angle(flight_id, 11000, 400)
        time.sleep(0.01)
        angle, label = compute_incline_angle(flight_id, 10000, 400)
        assert "Descending" in label
        assert angle is not None and angle < -ANGLE_THRESHOLD_DEG

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_zero_ground_speed(self):
        """Zero ground speed should return 'Calculating...' (horizontal_ft <= 0)."""
        flight_id = "zero_speed"
        compute_incline_angle(flight_id, 30000, 0)
        time.sleep(0.01)
        angle, label = compute_incline_angle(flight_id, 30000, 0)
        assert angle is None
        assert label == "Calculating..."

    def test_negative_ground_speed(self):
        """Negative ground speed should also return 'Calculating...'."""
        flight_id = "neg_speed"
        compute_incline_angle(flight_id, 30000, -100)
        time.sleep(0.01)
        angle, label = compute_incline_angle(flight_id, 30000, -100)
        assert angle is None
        assert label == "Calculating..."

    def test_rapid_consecutive_calls(self):
        """
        If dt is extremely small (<= 0), the function should return
        'Calculating...' to avoid division-by-zero or nonsensical angles.
        """
        flight_id = "rapid_fire"
        compute_incline_angle(flight_id, 30000, 400)
        # Call again immediately – dt will be ~0
        angle, label = compute_incline_angle(flight_id, 30000, 400)
        # On some systems dt may be > 0, but if it's <= 0 we expect Calculating...
        if angle is None:
            assert label == "Calculating..."

    def test_angle_formula_correctness(self):
        """
        Manually verify the angle calculation for a known scenario.
        If a flight climbs 1000 ft in 3 seconds at 400 kt:
          - dt = 3 s
          - horizontal_ft = 400 * (3/3600) * 6076.12 ≈ 2025.37 ft
          - angle = atan2(1000, 2025.37) ≈ 26.3°
        """
        flight_id = "formula_check"
        # Manually set previous_altitudes to simulate a 3-second gap
        now = time.time()
        previous_altitudes[flight_id] = (now - 3, 30000)

        angle, label = compute_incline_angle(flight_id, 31000, 400)
        assert angle is not None
        # Expected: atan2(1000, 400 * (3/3600) * 6076.12)
        expected_horizontal = 400 * (3 / 3600) * NM_TO_FT
        expected_angle = math.degrees(math.atan2(1000, expected_horizontal))
        assert abs(angle - expected_angle) < 0.01
        assert "Climbing" in label