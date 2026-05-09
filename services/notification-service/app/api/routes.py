import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status

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
# Endpoints
# ------------------------------------------------------------------ #

@router.get(
    "/notifications/{user_id}",
    response_model=NotificationListResponse,
    summary="Get all unread notifications for a user",
)
async def get_notifications(
    user_id: str,
    service: NotificationService = Depends(get_notification_service),
    redis: aioredis.Redis = Depends(get_redis),
) -> NotificationListResponse:
    """
    GET /notifications/{user_id}

    Returns all notifications stored in the user's Redis key.
    The frontend polls this endpoint to display unread alerts.
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
    This implements the "mark as read" behaviour specified in the document.
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

    Confirms the service is running and the Redis connection is alive.
    Used by Kubernetes liveness probes.
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