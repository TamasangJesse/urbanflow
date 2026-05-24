import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.connection_manager import manager
from app.core.models import IncidentEvent
from app.core.redis_client import get_redis
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# How long (seconds) to block waiting for new stream messages before looping.
# Keeps the worker responsive to cancellation without busy-waiting.
_BLOCK_MS = 5_000

# How long a message can sit pending before we auto-claim it (60 seconds).
# If a consumer dies mid-processing, another consumer will pick it up after
# this threshold instead of leaving it stuck forever.
_PENDING_TIMEOUT_MS = 60_000


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


async def _claim_abandoned_messages(
    redis: aioredis.Redis,
    service: NotificationService,
) -> None:
    """
    Claim and reprocess any messages that have been pending for longer than
    _PENDING_TIMEOUT_MS without being acknowledged.

    This handles the case where a consumer pod crashes or is restarted mid-
    processing, leaving messages stuck in the pending state forever. Without
    this, those messages block the queue and new incidents are delayed.
    """
    try:
        result = await redis.xautoclaim(
            settings.incident_stream_name,
            settings.stream_consumer_group,
            settings.stream_consumer_name,
            min_idle_time=_PENDING_TIMEOUT_MS,
            start_id="0-0",
            count=10,
        )

        # xautoclaim returns (next_start_id, messages, deleted_ids)
        messages = result[1] if result and len(result) > 1 else []

        if messages:
            logger.warning(
                "Claimed %d abandoned message(s) — reprocessing now", len(messages)
            )
            for message_id, fields in messages:
                await _process_message(redis, service, message_id, fields)

    except Exception as e:
        # XAUTOCLAIM requires Redis 6.2+. If not available, log and continue.
        logger.warning("XAUTOCLAIM not available or failed: %s — skipping", e)


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
            # Claim any abandoned pending messages first before reading new ones.
            await _claim_abandoned_messages(redis, service)

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

        event_type = fields.get("event", "incident_reported")

        # ── Incident resolved — broadcast to all connected clients ────────
        if event_type == "incident_resolved":
            await manager.broadcast({
             "type":          "incident_resolved",
             "incident_id":   fields.get("incident_id"),
             "incident_type": fields.get("incident_type", "Incident"),
             "address":       fields.get("address", ""),
           })
            logger.info(
                "Incident %s resolved — broadcast sent to all connected clients",
                fields.get("incident_id"),
            )
            await redis.xack(
                settings.incident_stream_name,
                settings.stream_consumer_group,
                message_id,
            )
            return

        # ── Normal incident reported — notify nearby users ─────────────────
        event = IncidentEvent(
            incident_id=fields["incident_id"],
            type=fields["type"],
            latitude=float(fields["latitude"]),
            longitude=float(fields["longitude"]),
            severity=fields["severity"].lower(),
            created_at=fields["created_at"],
            reported_by=fields.get("reported_by"),
            description=fields.get("description", ""),
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