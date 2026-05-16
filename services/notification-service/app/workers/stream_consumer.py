import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.models import IncidentEvent
from app.core.redis_client import get_redis
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# How long (seconds) to block waiting for new stream messages before looping.
# Keeps the worker responsive to cancellation without busy-waiting.
_BLOCK_MS = 5_000


async def _ensure_consumer_group(redis: aioredis.Redis) -> None:
    """
    Create the Redis Streams consumer group if it doesn't already exist.
    MKSTREAM creates the stream itself if it doesn't exist yet.
    """
    try:
        await redis.xgroup_create(
            settings.incident_stream_name,
            settings.stream_consumer_group,
            id="0",         # start from the beginning of the stream
            mkstream=True,
        )
        logger.info(
            "Consumer group '%s' created on stream '%s'",
            settings.stream_consumer_group,
            settings.incident_stream_name,
        )
    except Exception as e:
        # BUSYGROUP means the group already exists — safe to ignore.
        if "BUSYGROUP" in str(e):
            logger.debug("Consumer group already exists — skipping creation")
        else:
            raise


async def consume_incident_stream() -> None:
    """
    Background worker (Publisher-Subscriber pattern).

    Continuously reads new messages from `incident_stream` in Redis Streams
    using a consumer group so that, if multiple instances of this service
    run in Kubernetes, each event is processed by exactly one instance.

    Flow per message:
        1. Parse the raw Redis hash into an IncidentEvent.
        2. Call NotificationService.notify_nearby_users().
        3. ACK the message so it is not redelivered.

    This function runs for the lifetime of the application.  It is started
    as an asyncio background task in main.py startup_event().
    """
    logger.info("Notification worker starting — listening on '%s'", settings.incident_stream_name)

    redis = await get_redis()
    await _ensure_consumer_group(redis)

    repo = NotificationRepository(redis)
    service = NotificationService(repo)

    while True:
        try:
            # XREADGROUP blocks for up to _BLOCK_MS ms waiting for new messages.
            # ">" means "give me only messages not yet delivered to any consumer".
            results = await redis.xreadgroup(
                groupname=settings.stream_consumer_group,
                consumername=settings.stream_consumer_name,
                streams={settings.incident_stream_name: ">"},
                count=10,
                block=_BLOCK_MS,
            )

            if not results:
                # Timeout with no messages — loop and wait again.
                continue

            for _stream_name, messages in results:
                for message_id, fields in messages:
                    await _process_message(redis, service, message_id, fields)

        except asyncio.CancelledError:
            logger.info("Notification worker cancelled — shutting down cleanly")
            break
        except Exception as e:
            logger.error("Worker error: %s — retrying in 3 seconds", e, exc_info=True)
            await asyncio.sleep(3)


async def _process_message(
    redis: aioredis.Redis,
    service: NotificationService,
    message_id: str,
    fields: dict,
) -> None:
    """Parse one Redis Streams message and trigger geofencing + push."""
    try:
        logger.debug("Processing message %s: %s", message_id, fields)

        event = IncidentEvent(
            incident_id=fields["incident_id"],
            type=fields["type"],
            latitude=float(fields["latitude"]),
            longitude=float(fields["longitude"]),
            severity=fields["severity"].lower(),
            created_at=fields["created_at"],
            reported_by=fields.get("reported_by"),
        )

        notified_count = await service.notify_nearby_users(event)
        logger.info(
            "Incident %s — notified %d nearby users",
            event.incident_id,
            notified_count,
        )

        # ACK: tells Redis this message has been successfully processed.
        await redis.xack(
            settings.incident_stream_name,
            settings.stream_consumer_group,
            message_id,
        )

    except Exception as e:
        logger.error(
            "Failed to process message %s: %s — message will be redelivered",
            message_id,
            e,
            exc_info=True,
        )
        # Do NOT ACK on failure — Redis will redeliver to another consumer.