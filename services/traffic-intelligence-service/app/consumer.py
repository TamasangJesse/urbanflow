"""
consumer.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Redis Streams consumer for the incident_stream.

Responsibilities:
  - Listen on incident_stream published by the Incident Report Service
  - Map incoming incident severity to a congestion level
  - Populate active_incident_boosts with a 30-minute expiry
  - Run as a background asyncio task for the lifetime of the service

Does NOT touch PostgreSQL.
Does NOT retrain the model.
Does NOT expose any HTTP endpoints.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from app.redis_client import redis_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity → congestion level mapping
# ---------------------------------------------------------------------------
SEVERITY_TO_CONGESTION = {
    "low":      "Medium",
    "medium":   "High",
    "high":     "Very High",
    "critical": "Very High",
}

BOOST_DURATION_MINUTES = 30
STREAM_KEY             = "incident_stream"


# ---------------------------------------------------------------------------
# CONSUMER
# ---------------------------------------------------------------------------

async def consume_incident_stream(active_incident_boosts: dict) -> None:
    """
    Background worker — runs for the entire lifetime of the service.
    Started as an asyncio task in the FastAPI lifespan handler in main.py.

    Reads from incident_stream using XREAD with a 5-second block.
    On each event:
      1. Extracts location_name and severity from the message fields
      2. Maps severity to a congestion level via SEVERITY_TO_CONGESTION
      3. Writes an entry into active_incident_boosts with a 30-minute expiry

    The /predict endpoint checks active_incident_boosts before calling
    the ML model — if a live boost exists for the requested location,
    it returns the boosted level immediately with confidence=1.0.

    Expected message fields published by the Incident Report Service:
        location_name  — e.g. "Bastos"
        severity       — one of: low, medium, high, critical

    Parameters:
        active_incident_boosts — the module-level dict defined in main.py.
                                  Passed in so consumer.py never imports main.py
                                  (avoids circular imports).
    """
    last_id = "$"   # only consume new messages from this point forward

    logger.info("Incident stream consumer started. Listening on '%s' ...", STREAM_KEY)

    while True:
        try:
            # Run blocking xread in a thread executor so it doesn't block
            # the asyncio event loop. block=5000 waits up to 5s for messages.
            messages = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: redis_client.xread(
                    {STREAM_KEY: last_id},
                    block=5000,
                    count=10,
                ),
            )

            if not messages:
                continue

            for stream, events in messages:
                for event_id, fields in events:

                    location_name = fields.get("location_name", "").strip()
                    severity      = fields.get("severity", "").lower().strip()

                    # Validate — skip malformed events
                    if not location_name or severity not in SEVERITY_TO_CONGESTION:
                        logger.warning(
                            "Skipping malformed incident event id=%s fields=%s",
                            event_id, fields,
                        )
                        last_id = event_id
                        continue

                    congestion_level = SEVERITY_TO_CONGESTION[severity]
                    expires_at       = datetime.utcnow() + timedelta(minutes=BOOST_DURATION_MINUTES)

                    active_incident_boosts[location_name] = {
                        "congestion_level": congestion_level,
                        "expires_at":       expires_at,
                    }

                    logger.info(
                        "Incident boost applied | location='%s' severity='%s' "
                        "congestion='%s' expires_at='%s'",
                        location_name,
                        severity,
                        congestion_level,
                        expires_at.strftime("%H:%M:%S"),
                    )

                    # Advance cursor — never reprocess this event
                    last_id = event_id

        except asyncio.CancelledError:
            # Service is shutting down — exit cleanly
            logger.info("Incident stream consumer cancelled — shutting down cleanly.")
            break

        except Exception as e:
            # Any Redis error — log and retry after 5 seconds
            logger.error(
                "Incident stream consumer error: %s — retrying in 5s.", str(e)
            )
            await asyncio.sleep(5)