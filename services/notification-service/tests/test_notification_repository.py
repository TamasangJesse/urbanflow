"""
Tests for NotificationRepository.

All Redis calls are mocked so these tests run without a live Redis instance.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.models import Notification
from app.repositories.notification_repository import NotificationRepository


def _make_mock_redis() -> MagicMock:
    r = MagicMock()
    r.rpush = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    r.lrange = AsyncMock(return_value=[])
    r.delete = AsyncMock(return_value=1)
    r.get = AsyncMock(return_value=None)
    r.scan_iter = MagicMock()
    return r


def _make_notification(**kwargs) -> Notification:
    defaults = dict(
        incident_id="inc-001",
        type="accident",
        severity="high",
        latitude=3.87,
        longitude=11.52,
        message="Alert near you",
        created_at=datetime(2026, 4, 1, 10, 0, 0),
        is_read=False,
    )
    defaults.update(kwargs)
    return Notification(**defaults)


class TestPushNotificationRepository:
    @pytest.mark.asyncio
    async def test_push_calls_rpush_with_correct_key(self):
        redis = _make_mock_redis()
        repo = NotificationRepository(redis)
        notif = _make_notification()

        await repo.push_notification("user-1", notif)

        redis.rpush.assert_called_once()
        key_used = redis.rpush.call_args[0][0]
        assert key_used == "notification:user-1"

    @pytest.mark.asyncio
    async def test_push_sets_ttl(self):
        redis = _make_mock_redis()
        repo = NotificationRepository(redis)
        notif = _make_notification()

        await repo.push_notification("user-1", notif)

        redis.expire.assert_called_once()
        key_used = redis.expire.call_args[0][0]
        assert key_used == "notification:user-1"

    @pytest.mark.asyncio
    async def test_get_notifications_returns_empty_list_when_no_key(self):
        redis = _make_mock_redis()
        redis.lrange = AsyncMock(return_value=[])
        repo = NotificationRepository(redis)

        result = await repo.get_notifications("user-999")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_notifications_deserialises_correctly(self):
        notif = _make_notification()
        redis = _make_mock_redis()
        redis.lrange = AsyncMock(return_value=[notif.model_dump_json()])
        repo = NotificationRepository(redis)

        result = await repo.get_notifications("user-1")

        assert len(result) == 1
        assert result[0].incident_id == "inc-001"
        assert result[0].severity == "high"

    @pytest.mark.asyncio
    async def test_clear_notifications_calls_delete(self):
        redis = _make_mock_redis()
        repo = NotificationRepository(redis)

        await repo.clear_notifications("user-1")

        redis.delete.assert_called_once_with("notification:user-1")


class TestGetUserLocation:
    @pytest.mark.asyncio
    async def test_returns_none_when_key_missing(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(return_value=None)
        repo = NotificationRepository(redis)

        result = await repo.get_user_location("user-1")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_tuple_when_valid_session_exists(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(
            return_value=json.dumps({"latitude": 3.8730, "longitude": 11.5156})
        )
        repo = NotificationRepository(redis)

        result = await repo.get_user_location("user-1")

        assert result == (3.8730, 11.5156)

    @pytest.mark.asyncio
    async def test_reads_correct_key(self):
        redis = _make_mock_redis()
        repo = NotificationRepository(redis)

        await repo.get_user_location("user-42")

        redis.get.assert_called_once_with("user_session:user-42")

    @pytest.mark.asyncio
    async def test_returns_none_on_malformed_json(self):
        redis = _make_mock_redis()
        redis.get = AsyncMock(return_value="not-valid-json{{{")
        repo = NotificationRepository(redis)

        result = await repo.get_user_location("user-1")

        assert result is None