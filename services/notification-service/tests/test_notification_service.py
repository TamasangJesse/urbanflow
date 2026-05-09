"""
Tests for NotificationService — the two most critical functions per the spec:
    1. find_nearby_users()  — geofencing logic
    2. push_notification()  — writing notifications to Redis

Redis is mocked so tests run without a live Redis instance.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.models import IncidentEvent, Notification
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

def _make_event(**kwargs) -> IncidentEvent:
    defaults = dict(
        incident_id="inc-001",
        type="accident",
        latitude=3.8730,
        longitude=11.5156,
        severity="high",
        created_at=datetime(2026, 4, 1, 10, 0, 0),
    )
    defaults.update(kwargs)
    return IncidentEvent(**defaults)


def _make_mock_repo() -> MagicMock:
    """Return a MagicMock whose async methods return sensible defaults."""
    repo = MagicMock(spec=NotificationRepository)
    repo.get_all_active_user_ids = AsyncMock(return_value=[])
    repo.get_user_location = AsyncMock(return_value=None)
    repo.push_notification = AsyncMock(return_value=None)
    repo.get_notifications = AsyncMock(return_value=[])
    repo.clear_notifications = AsyncMock(return_value=None)
    return repo


# ------------------------------------------------------------------ #
# find_nearby_users()
# ------------------------------------------------------------------ #

class TestFindNearbyUsers:
    @pytest.mark.asyncio
    async def test_no_active_users_returns_empty(self):
        repo = _make_mock_repo()
        service = NotificationService(repo)

        result = await service.find_nearby_users(3.8730, 11.5156)

        assert result == []
        repo.get_all_active_user_ids.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_within_radius_is_included(self):
        """User ~800m from incident — should be included."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        # ~800m away from incident at (3.8730, 11.5156)
        repo.get_user_location = AsyncMock(return_value=(3.8800, 11.5156))

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8730, 11.5156, radius_metres=5000)

        assert "user-1" in result

    @pytest.mark.asyncio
    async def test_user_outside_radius_is_excluded(self):
        """User ~12km from incident — should be excluded from 5km geofence."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-far"])
        # ~12 km away
        repo.get_user_location = AsyncMock(return_value=(3.9800, 11.5156))

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8730, 11.5156, radius_metres=5000)

        assert "user-far" not in result

    @pytest.mark.asyncio
    async def test_mixed_users_only_nearby_returned(self):
        """One user inside radius, one outside — only the nearby one returned."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["near", "far"])

        async def mock_location(user_id):
            return (3.8750, 11.5156) if user_id == "near" else (3.9900, 11.5156)

        repo.get_user_location = AsyncMock(side_effect=mock_location)

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8730, 11.5156, radius_metres=5000)

        assert "near" in result
        assert "far" not in result

    @pytest.mark.asyncio
    async def test_user_with_no_cached_location_is_skipped(self):
        """Users without a cached location (session expired) are skipped."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-no-loc"])
        repo.get_user_location = AsyncMock(return_value=None)

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8730, 11.5156)

        assert result == []

    @pytest.mark.asyncio
    async def test_user_exactly_at_boundary_is_included(self):
        """User exactly at the radius boundary should be included (<= check)."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["boundary-user"])

        # Place user exactly 5000m north of the incident.
        # 1 degree latitude ≈ 111,195 m → 5000m ≈ 0.04497 degrees
        incident_lat, incident_lng = 3.8730, 11.5156
        user_lat = incident_lat + (5000 / 111_195)
        repo.get_user_location = AsyncMock(return_value=(user_lat, incident_lng))

        service = NotificationService(repo)
        result = await service.find_nearby_users(incident_lat, incident_lng, radius_metres=5000)

        assert "boundary-user" in result

    @pytest.mark.asyncio
    async def test_multiple_nearby_users_all_returned(self):
        """All three users within radius should be in the result."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["u1", "u2", "u3"])
        # All within ~500m of incident
        repo.get_user_location = AsyncMock(return_value=(3.8740, 11.5160))

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8730, 11.5156, radius_metres=5000)

        assert set(result) == {"u1", "u2", "u3"}


# ------------------------------------------------------------------ #
# push_notification()
# ------------------------------------------------------------------ #

class TestPushNotification:
    @pytest.mark.asyncio
    async def test_push_notification_calls_repository(self):
        """push_notification() must call repo.push_notification() exactly once."""
        repo = _make_mock_repo()
        service = NotificationService(repo)

        event = _make_event()
        await service.push_notification("user-1", event)

        repo.push_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_notification_correct_user_id(self):
        """Notification must be pushed to the correct user ID."""
        repo = _make_mock_repo()
        service = NotificationService(repo)

        event = _make_event()
        await service.push_notification("user-42", event)

        call_args = repo.push_notification.call_args
        assert call_args[0][0] == "user-42"

    @pytest.mark.asyncio
    async def test_push_notification_builds_correct_model(self):
        """The Notification object built from the event must carry the right fields."""
        repo = _make_mock_repo()
        service = NotificationService(repo)

        event = _make_event(incident_id="inc-999", type="flooding", severity="critical")
        await service.push_notification("user-1", event)

        call_args = repo.push_notification.call_args
        notification: Notification = call_args[0][1]

        assert notification.incident_id == "inc-999"
        assert notification.type == "flooding"
        assert notification.severity == "critical"
        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_push_notification_message_contains_type(self):
        """Human-readable message should reference the incident type."""
        repo = _make_mock_repo()
        service = NotificationService(repo)

        event = _make_event(type="roadblock")
        await service.push_notification("user-1", event)

        notification: Notification = repo.push_notification.call_args[0][1]
        assert "Roadblock" in notification.message

    @pytest.mark.asyncio
    async def test_push_notification_message_contains_severity(self):
        """Human-readable message should reference the severity level."""
        repo = _make_mock_repo()
        service = NotificationService(repo)

        event = _make_event(severity="medium")
        await service.push_notification("user-1", event)

        notification: Notification = repo.push_notification.call_args[0][1]
        assert "Medium" in notification.message

    @pytest.mark.asyncio
    async def test_notify_nearby_users_returns_count(self):
        """notify_nearby_users() should return the number of users notified."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["u1", "u2"])
        repo.get_user_location = AsyncMock(return_value=(3.8740, 11.5160))

        service = NotificationService(repo)
        event = _make_event()
        count = await service.notify_nearby_users(event)

        assert count == 2
        assert repo.push_notification.call_count == 2