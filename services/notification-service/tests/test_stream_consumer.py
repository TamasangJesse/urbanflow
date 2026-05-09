"""
Tests for the Redis Streams background worker.
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.stream_consumer import _process_message, _ensure_consumer_group


class TestEnsureConsumerGroup:
    @pytest.mark.asyncio
    async def test_creates_group_successfully(self):
        redis = MagicMock()
        redis.xgroup_create = AsyncMock(return_value=True)

        await _ensure_consumer_group(redis)

        redis.xgroup_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_ignores_busygroup_error(self):
        redis = MagicMock()
        redis.xgroup_create = AsyncMock(side_effect=Exception("BUSYGROUP already exists"))

        # Should not raise
        await _ensure_consumer_group(redis)

    @pytest.mark.asyncio
    async def test_raises_on_unexpected_error(self):
        redis = MagicMock()
        redis.xgroup_create = AsyncMock(side_effect=Exception("WRONGTYPE operation"))

        with pytest.raises(Exception, match="WRONGTYPE"):
            await _ensure_consumer_group(redis)


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_processes_valid_message_and_acks(self):
        redis = MagicMock()
        redis.xack = AsyncMock(return_value=1)

        service = MagicMock()
        service.notify_nearby_users = AsyncMock(return_value=3)

        fields = {
            "incident_id": "inc-001",
            "type": "accident",
            "latitude": "3.8730",
            "longitude": "11.5156",
            "severity": "high",
            "created_at": "2026-04-01T10:00:00",
        }

        await _process_message(redis, service, "msg-001", fields)

        service.notify_nearby_users.assert_called_once()
        redis.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_ack_on_processing_failure(self):
        redis = MagicMock()
        redis.xack = AsyncMock(return_value=1)

        service = MagicMock()
        service.notify_nearby_users = AsyncMock(side_effect=Exception("DB error"))

        fields = {
            "incident_id": "inc-002",
            "type": "flooding",
            "latitude": "3.87",
            "longitude": "11.52",
            "severity": "medium",
            "created_at": "2026-04-01T10:00:00",
        }

        # Should not raise — errors are caught and logged
        await _process_message(redis, service, "msg-002", fields)

        # Must NOT ack — message will be redelivered
        redis.xack.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_field_does_not_ack(self):
        redis = MagicMock()
        redis.xack = AsyncMock(return_value=1)

        service = MagicMock()
        service.notify_nearby_users = AsyncMock(return_value=0)

        # Missing 'severity' field — should fail gracefully
        fields = {
            "incident_id": "inc-003",
            "type": "accident",
            "latitude": "3.87",
            "longitude": "11.52",
            # severity is missing
            "created_at": "2026-04-01T10:00:00",
        }

        await _process_message(redis, service, "msg-003", fields)

        redis.xack.assert_not_called()