import time
import math

NM_TO_FT = 6076.12
ANGLE_THRESHOLD_DEG = 0.3  # below this, treat as level flight

previous_altitudes = {}  # used to track previous atltitude for getting angle climb/descent


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
        label = "Level flight"  # less than 0.5 degrees

    return angle_deg, label
