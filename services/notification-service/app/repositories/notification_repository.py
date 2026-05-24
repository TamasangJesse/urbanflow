import json
import logging
from datetime import datetime

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.models import Notification

logger = logging.getLogger(__name__)


class NotificationRepository:
    """
    Repository Pattern implementation for the Notification Service.

    All Redis key construction and serialisation lives here.
    Service logic never touches raw Redis keys directly — it calls
    methods on this repository instead.

    Keys managed:
        notification:{user_id}   — List of notification JSON objects (TTL 24h)
        user_session:{user_id}   — User location + route written by the User Service
    """

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    # ------------------------------------------------------------------ #
    # Notification storage
    # ------------------------------------------------------------------ #

    async def push_notification(self, user_id: str, notification: Notification) -> None:
        """
        Append a notification to the user's notification list in Redis.
        Resets the TTL to 24 hours on every write (document spec).
        """
        key = f"notification:{user_id}"
        payload = notification.model_dump_json()

        await self._redis.rpush(key, payload)
        await self._redis.expire(key, settings.notification_ttl_seconds)

        logger.info("Pushed notification to %s (incident %s)", key, notification.incident_id)

    async def get_notifications(self, user_id: str) -> list[Notification]:
        """
        Return all stored notifications for a user.
        Returns an empty list if the key does not exist.
        """
        key = f"notification:{user_id}"
        raw_items = await self._redis.lrange(key, 0, -1)

        notifications: list[Notification] = []
        for raw in raw_items:
            try:
                notifications.append(Notification.model_validate_json(raw))
            except Exception:
                logger.warning("Failed to deserialise notification for %s — skipping", user_id)

        return notifications

    async def clear_notifications(self, user_id: str) -> None:
        """
        Delete all notifications for a user (mark-as-read behaviour).
        """
        key = f"notification:{user_id}"
        await self._redis.delete(key)
        logger.info("Cleared notifications for user %s", user_id)

    # ------------------------------------------------------------------ #
    # User session / location (written by User Service, read here)
    # ------------------------------------------------------------------ #

    async def get_user_location(self, user_id: str) -> tuple[float, float] | None:
        """
        Read the user's last known GPS coordinates from the shared
        user_session:{user_id} Redis key.

        Returns:
            (latitude, longitude) tuple, or None if the key is missing.
        """
        key = f"user_session:{user_id}"
        raw = await self._redis.get(key)

        if raw is None:
            return None

        try:
            data = json.loads(raw)
            return float(data["latitude"]), float(data["longitude"])
        except (KeyError, ValueError, json.JSONDecodeError):
            logger.warning("Malformed user_session for user %s", user_id)
            return None

    async def get_user_route_points(self, user_id: str) -> list[tuple[float, float]] | None:
        """
        Read the user's active route points from the shared
        user_session:{user_id} Redis key.

        Route points are written by the User Service when the user
        plans a route on the frontend. Each point is a [lat, lng] pair.

        Returns:
            List of (latitude, longitude) tuples, or None if no route is stored.
        """
        key = f"user_session:{user_id}"
        raw = await self._redis.get(key)

        if raw is None:
            return None

        try:
            data = json.loads(raw)
            route_points = data.get("route_points")
            if not route_points:
                return None
            return [(float(p[0]), float(p[1])) for p in route_points]
        except (KeyError, ValueError, json.JSONDecodeError, IndexError):
            logger.warning("Malformed route_points for user %s", user_id)
            return None

    async def get_all_active_user_ids(self) -> list[str]:
        """
        Scan Redis for all user_session:* keys to get IDs of users whose
        location is currently cached.

        Uses SCAN (non-blocking) instead of KEYS (blocks the server).
        """
        user_ids: list[str] = []
        async for key in self._redis.scan_iter("user_session:*"):
            user_id = key.split(":", 1)[1]
            user_ids.append(user_id)
        return user_ids