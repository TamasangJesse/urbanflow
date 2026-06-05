"""
Additional tests covering:
  - get_user_route_points() in NotificationRepository
  - Route-based geofencing in NotificationService
  - incident_resolved handling in stream_consumer
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.models import IncidentEvent
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _make_mock_redis() -> MagicMock:
    r = MagicMock()
    r.rpush = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    r.lrange = AsyncMock(return_value=[])
    r.delete = AsyncMock(return_value=1)
    r.get = AsyncMock(return_value=None)
    r.scan_iter = MagicMock()
    return r


def _make_mock_repo() -> MagicMock:
    repo = MagicMock(spec=NotificationRepository)
    repo.get_all_active_user_ids = AsyncMock(return_value=[])
    repo.get_user_location = AsyncMock(return_value=None)
    repo.get_user_route_points = AsyncMock(return_value=None)
    repo.push_notification = AsyncMock(return_value=None)
    repo.get_notifications = AsyncMock(return_value=[])
    repo.clear_notifications = AsyncMock(return_value=None)
    return repo


def _make_event(**kwargs) -> IncidentEvent:
    defaults = dict(
        incident_id="inc-001",
        type="accident",
        latitude=3.8886,
        longitude=11.5449,
        severity="high",
        created_at=datetime(2026, 4, 1, 10, 0, 0),
        reported_by=None,
    )
    defaults.update(kwargs)
    return IncidentEvent(**defaults)


# ------------------------------------------------------------------ #
# get_user_route_points()
# ------------------------------------------------------------------ #

class TestGetUserRoutePoints:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_session(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(return_value=None)
        repo = NotificationRepository(redis)
        result = await repo.get_user_route_points("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_route_points_in_session(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(
            return_value=json.dumps({"latitude": 3.87, "longitude": 11.52})
        )
        repo = NotificationRepository(redis)
        result = await repo.get_user_route_points("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_route_points_when_present(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(
            return_value=json.dumps({
                "latitude": 3.87,
                "longitude": 11.52,
                "route_points": [[3.87, 11.52], [3.88, 11.53], [3.89, 11.54]]
            })
        )
        repo = NotificationRepository(redis)
        result = await repo.get_user_route_points("user-1")
        assert result == [(3.87, 11.52), (3.88, 11.53), (3.89, 11.54)]

    @pytest.mark.asyncio
    async def test_reads_correct_key(self):
        redis = _make_mock_redis()
        repo = NotificationRepository(redis)
        await repo.get_user_route_points("user-42")
        redis.get.assert_called_once_with("user_session:user-42")

    @pytest.mark.asyncio
    async def test_returns_none_on_malformed_json(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(return_value="not-valid-json{{{")
        repo = NotificationRepository(redis)
        result = await repo.get_user_route_points("user-1")
        assert result is None


# ------------------------------------------------------------------ #
# Route-based geofencing in NotificationService
# ------------------------------------------------------------------ #

class TestRouteBased:
    @pytest.mark.asyncio
    async def test_user_with_route_notified_when_incident_on_route(self):
        """Incident at (3.8886, 11.5449) — place a route point 200m away."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        repo.get_user_location = AsyncMock(return_value=(3.8750, 11.5156))
        # Route point very close to the incident
        repo.get_user_route_points = AsyncMock(
            return_value=[(3.8884, 11.5447)]
        )

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8886, 11.5449)

        assert "user-1" in result

    @pytest.mark.asyncio
    async def test_user_with_route_not_notified_when_incident_far_from_route(self):
        """Incident far from every route point — user should not be notified."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        repo.get_user_location = AsyncMock(return_value=(3.8750, 11.5156))
        # Route points all far from incident at (3.8886, 11.5449)
        repo.get_user_route_points = AsyncMock(
            return_value=[(3.8000, 11.4000), (3.8100, 11.4100)]
        )

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8886, 11.5449)

        assert "user-1" not in result

    @pytest.mark.asyncio
    async def test_user_without_route_falls_back_to_proximity(self):
        """User has no route — falls back to 5km proximity check."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        repo.get_user_location = AsyncMock(return_value=(3.8750, 11.5156))
        repo.get_user_route_points = AsyncMock(return_value=None)

        service = NotificationService(repo)
        # Incident close to user location
        result = await service.find_nearby_users(3.8760, 11.5160)

        assert "user-1" in result

    @pytest.mark.asyncio
    async def test_route_check_takes_priority_over_proximity(self):
        """User has a route but incident is NOT on it — not notified even if nearby."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        # User is physically close to incident
        repo.get_user_location = AsyncMock(return_value=(3.8887, 11.5450))
        # But their route goes in a completely different direction
        repo.get_user_route_points = AsyncMock(
            return_value=[(3.8000, 11.4000), (3.8100, 11.4100)]
        )

        service = NotificationService(repo)
        result = await service.find_nearby_users(3.8886, 11.5449)

        assert "user-1" not in result

    @pytest.mark.asyncio
    async def test_incident_on_route_calls_push_notification(self):
        """When incident is on route, push_notification must be called."""
        repo = _make_mock_repo()
        repo.get_all_active_user_ids = AsyncMock(return_value=["user-1"])
        repo.get_user_location = AsyncMock(return_value=(3.8750, 11.5156))
        repo.get_user_route_points = AsyncMock(
            return_value=[(3.8884, 11.5447)]
        )

        service = NotificationService(repo)
        event = _make_event()
        count = await service.notify_nearby_users(event)

        assert count == 1
        assert repo.push_notification.call_count == 1


# ------------------------------------------------------------------ #
# incident_resolved in stream_consumer
# ------------------------------------------------------------------ #

class TestIncidentResolved:
    @pytest.mark.asyncio
    async def test_resolved_event_triggers_broadcast(self):
        from app.workers.stream_consumer import _process_message
        from unittest.mock import patch, AsyncMock

        redis = MagicMock()
        redis.xack = AsyncMock(return_value=1)

        service = MagicMock()
        service.notify_nearby_users = AsyncMock(return_value=0)

        fields = {
            "event": "incident_resolved",
            "incident_id": "inc-resolved-001",
        }

        with patch("app.workers.stream_consumer.manager") as mock_manager:
            mock_manager.broadcast = AsyncMock()
            await _process_message(redis, service, "msg-resolved-001", fields)
            call_args = mock_manager.broadcast.call_args[0][0]
                assert call_args["type"] == "incident_resolved"
                assert call_args["incident_id"] == "inc-resolved-001"
                assert mock_manager.broadcast.call_count == 1

                
    @pytest.mark.asyncio
    async def test_resolved_event_acks_and_does_not_notify_users(self):
        from app.workers.stream_consumer import _process_message

        redis = MagicMock()
        redis.xack = AsyncMock(return_value=1)

        service = MagicMock()
        service.notify_nearby_users = AsyncMock(return_value=0)

        fields = {
            "event": "incident_resolved",
            "incident_id": "inc-resolved-002",
        }

        with patch("app.workers.stream_consumer.manager") as mock_manager:
            mock_manager.broadcast = AsyncMock()
            await _process_message(redis, service, "msg-002", fields)

            # Must ACK
            redis.xack.assert_called_once()
            # Must NOT call notify_nearby_users
            service.notify_nearby_users.assert_not_called()