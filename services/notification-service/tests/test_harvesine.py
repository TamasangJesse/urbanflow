"""
Tests for the Haversine distance formula.

No mocking needed — haversine() is a pure function with no I/O.
"""
import pytest
from app.core.haversine import haversine


class TestHaversine:
    def test_same_point_returns_zero(self):
        """Distance from a point to itself must be 0."""
        assert haversine(3.848, 11.502, 3.848, 11.502) == 0.0

    def test_known_distance_bastos_to_mokolo(self):
        """
        Bastos (~3.8730, 11.5156) to Mokolo (~3.8820, 11.5080).
        Known approximate distance: ~1.1 km.
        """
        distance = haversine(3.8730, 11.5156, 3.8820, 11.5080)
        assert 900 < distance < 1500, f"Expected ~1300m, got {distance:.0f}m"

    def test_within_5km_radius(self):
        """Two points ~2.5 km apart should both be within the 5 km geofence."""
        # Yaoundé city centre to a point ~2.5 km north
        lat1, lng1 = 3.8667, 11.5167
        lat2, lng2 = 3.8892, 11.5167  # ~2.5 km north
        distance = haversine(lat1, lng1, lat2, lng2)
        assert distance <= 5000

    def test_outside_5km_radius(self):
        """Two points ~10 km apart should exceed the 5 km geofence."""
        lat1, lng1 = 3.8667, 11.5167
        lat2, lng2 = 3.9565, 11.5167  # ~10 km north
        distance = haversine(lat1, lng1, lat2, lng2)
        assert distance > 5000

    def test_symmetry(self):
        """haversine(A, B) must equal haversine(B, A)."""
        d1 = haversine(3.8730, 11.5156, 3.8820, 11.5080)
        d2 = haversine(3.8820, 11.5080, 3.8730, 11.5156)
        assert abs(d1 - d2) < 0.001  # floating point tolerance

    def test_returns_metres(self):
        """Result should be in metres, not kilometres."""
        # ~1 km apart → result should be ~1000, not ~1
        distance = haversine(3.8730, 11.5156, 3.8820, 11.5080)
        assert distance > 100, "Result looks like it might be in km, not metres"

    def test_large_distance_is_positive(self):
        """Distances must always be non-negative."""
        distance = haversine(0.0, 0.0, 90.0, 180.0)
        assert distance > 0

    def test_equator_crossing(self):
        """Should handle coordinates that cross the equator without error."""
        distance = haversine(-1.0, 11.5, 1.0, 11.5)
        assert distance > 0