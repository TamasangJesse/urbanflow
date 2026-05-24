import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.connection_manager import manager
from app.core.models import NotificationListResponse
from app.core.redis_client import get_redis
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

router = APIRouter()
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Dependency injection helpers
# ------------------------------------------------------------------ #

async def get_notification_service(
    redis: aioredis.Redis = Depends(get_redis),
) -> NotificationService:
    repo = NotificationRepository(redis)
    return NotificationService(repo)


# ------------------------------------------------------------------ #
# WebSocket endpoint — real-time push
# ------------------------------------------------------------------ #

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket /ws/{user_id}

    The frontend opens this connection once after login and keeps it open.
    The moment an incident is detected near the user, the notification is
    pushed instantly over this connection without the frontend needing to poll.

    The connection also stays resilient — if the client disconnects and
    reconnects, it picks up from where it left off (history is in Redis).

    Flow:
        1. Client connects → manager registers the connection
        2. Worker detects nearby incident → push_notification() fires
        3. manager.send_to_user() pushes JSON instantly to this socket
        4. Client disconnects → manager cleans up
    """
    await manager.connect(user_id, websocket)
    logger.info("WebSocket opened for user %s", user_id)

    try:
        # Keep the connection alive by waiting for any client message.
        # The frontend can send a ping ("heartbeat") to prevent timeouts.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        logger.info("WebSocket closed for user %s", user_id)


# ------------------------------------------------------------------ #
# HTTP endpoints — polling fallback
# ------------------------------------------------------------------ #

@router.get(
    "/notifications/{user_id}",
    response_model=NotificationListResponse,
    summary="Get all notifications for a user",
)
async def get_notifications(
    user_id: str,
    redis: aioredis.Redis = Depends(get_redis),
) -> NotificationListResponse:
    """
    GET /notifications/{user_id}

    Returns all notifications stored in the user's Redis key.
    Used as a fallback for clients that can't maintain a WebSocket,
    or to load notification history on page load.
    """
    repo = NotificationRepository(redis)
    notifications = await repo.get_notifications(user_id)

    return NotificationListResponse(
        user_id=user_id,
        notifications=notifications,
        total=len(notifications),
    )


@router.put(
    "/notifications/{user_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark all notifications as read",
)
async def mark_as_read(
    user_id: str,
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    """
    PUT /notifications/{user_id}/read

    Deletes all notifications for the user from Redis.
    """
    repo = NotificationRepository(redis)
    await repo.clear_notifications(user_id)
    logger.info("Notifications cleared for user %s", user_id)


@router.get(
    "/health",
    summary="Kubernetes liveness probe",
)
async def health_check(redis: aioredis.Redis = Depends(get_redis)) -> dict:
    """
    GET /health

    Confirms the service is running and Redis is reachable.
    """
    try:
        await redis.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection unavailable",
        )