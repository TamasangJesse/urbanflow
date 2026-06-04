from math import atan2, cos, radians, sin, sqrt


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates.

    Uses the Haversine formula exactly as specified in the UrbanFlow
    architecture document (SEN3244).

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lng1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lng2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in metres between the two points.
    """
    R = 6_371_000  # Earth radius in metres

    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )

    return R * 2 * atan2(sqrt(a), sqrt(1 - a))