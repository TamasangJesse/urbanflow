"""
Tests for the HTTP API routes (get_notifications, mark_as_read, health_check).
Uses FastAPI's TestClient with dependency overrides to mock Redis.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.models import Notification
from app.main import app
from app.core.redis_client import get_redis


def _make_mock_redis() -> MagicMock:
    r = MagicMock()
    r.ping = AsyncMock(return_value=True)
    r.rpush = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    r.lrange = AsyncMock(return_value=[])
    r.delete = AsyncMock(return_value=1)
    r.get = AsyncMock(return_value=None)
    r.scan_iter = MagicMock()
    return r


def _make_notification() -> Notification:
    return Notification(
        incident_id="inc-001",
        type="accident",
        severity="high",
        latitude=3.87,
        longitude=11.52,
        message="Alert near you",
        created_at=datetime(2026, 4, 1, 10, 0, 0),
        is_read=False,
    )


class TestHealthCheck:
    def test_health_returns_200_when_redis_ok(self):
        mock_redis = _make_mock_redis()

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["redis"] == "connected"

        app.dependency_overrides.clear()

    def test_health_returns_503_when_redis_down(self):
        mock_redis = _make_mock_redis()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 503
        app.dependency_overrides.clear()


class TestGetNotifications:
    def test_returns_empty_list_when_no_notifications(self):
        mock_redis = _make_mock_redis()
        mock_redis.lrange = AsyncMock(return_value=[])

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.get("/notifications/user-1")

        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == "user-1"
        assert body["notifications"] == []
        assert body["total"] == 0

        app.dependency_overrides.clear()

    def test_returns_notifications_when_present(self):
        notif = _make_notification()
        mock_redis = _make_mock_redis()
        mock_redis.lrange = AsyncMock(return_value=[notif.model_dump_json()])

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.get("/notifications/user-1")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["notifications"][0]["incident_id"] == "inc-001"

        app.dependency_overrides.clear()

    def test_user_id_reflected_in_response(self):
        mock_redis = _make_mock_redis()

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.get("/notifications/user-abc-123")

        assert response.json()["user_id"] == "user-abc-123"
        app.dependency_overrides.clear()


class TestMarkAsRead:
    def test_mark_as_read_returns_204(self):
        mock_redis = _make_mock_redis()

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        response = client.put("/notifications/user-1/read")

        assert response.status_code == 204
        app.dependency_overrides.clear()

    def test_mark_as_read_calls_delete_on_correct_key(self):
        mock_redis = _make_mock_redis()

        app.dependency_overrides[get_redis] = lambda: mock_redis
        client = TestClient(app)

        client.put("/notifications/user-42/read")

        mock_redis.delete.assert_called_once_with("notification:user-42")
        app.dependency_overrides.clear()