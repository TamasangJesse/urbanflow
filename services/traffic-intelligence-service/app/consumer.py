"""
consumer.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Redis Streams consumer for incident_stream.

Keyed by incident_id (not location_name) so we never depend on
the Incident Report Service publishing a location_name field.

New incident  → boost stored by incident_id with lat/lng + congestion level
Resolved      → boost removed by incident_id
No expiry     → boosts stay until explicitly resolved

Proximity check (done in ml_model.py):
  When /predict is called, ml_model.py checks if any active boost
  has a lat/lng within BOOST_RADIUS_KM of the requested location.
"""

import asyncio
import logging

from app.redis_client import redis_client

logger = logging.getLogger(__name__)

SEVERITY_TO_CONGESTION = {
    "low":      "Medium",
    "medium":   "High",
    "high":     "Very High",
    "critical": "Very High",
}

STREAM_KEY = "incident_stream"


async def consume_incident_stream(active_incident_boosts: dict) -> None:
    """
    Background worker — runs for the entire lifetime of the service.
    Started as an asyncio task in the FastAPI lifespan handler in main.py.

    Listens on incident_stream and handles two event types:

    1. New incident (no 'event' field, has 'severity'):
       Fields: incident_id, severity, latitude, longitude
       Action: add entry to active_incident_boosts keyed by incident_id

    2. Resolved incident (event=incident_resolved):
       Fields: event, incident_id
       Action: remove entry from active_incident_boosts by incident_id

    active_incident_boosts structure:
    {
        "64abc123": {
            "congestion_level": "Very High",
            "latitude":          3.8830,
            "longitude":         11.5150,
        },
        ...
    }
    """
    last_id = "$"

    logger.info("Incident stream consumer started. Listening on '%s' ...", STREAM_KEY)

    while True:
        try:
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

                    event_type  = fields.get("event", "")
                    incident_id = fields.get("incident_id", "").strip()

                    # ── Resolved incident ─────────────────────────────────
                    if event_type == "incident_resolved":
                        if incident_id and incident_id in active_incident_boosts:
                            del active_incident_boosts[incident_id]
                            logger.info(
                                "Incident resolved — boost removed | incident_id='%s'",
                                incident_id,
                            )
                        last_id = event_id
                        continue

                    # ── New incident ──────────────────────────────────────
                    severity = fields.get("severity", "").lower().strip()

                    if not incident_id or severity not in SEVERITY_TO_CONGESTION:
                        logger.warning(
                            "Skipping malformed incident event id=%s fields=%s",
                            event_id, fields,
                        )
                        last_id = event_id
                        continue

                    try:
                        latitude  = float(fields.get("latitude",  0))
                        longitude = float(fields.get("longitude", 0))
                    except (TypeError, ValueError):
                        logger.warning(
                            "Invalid lat/lng in incident event id=%s", event_id
                        )
                        last_id = event_id
                        continue

                    congestion_level = SEVERITY_TO_CONGESTION[severity]

                    active_incident_boosts[incident_id] = {
                        "congestion_level": congestion_level,
                        "latitude":         latitude,
                        "longitude":        longitude,
                    }

                    logger.info(
                        "Incident boost applied | incident_id='%s' severity='%s' "
                        "congestion='%s' lat=%.4f lng=%.4f",
                        incident_id, severity, congestion_level, latitude, longitude,
                    )

                    last_id = event_id

        except asyncio.CancelledError:
            logger.info("Incident stream consumer cancelled — shutting down cleanly.")
            break

        except Exception as e:
            logger.error(
                "Incident stream consumer error: %s — retrying in 5s.", str(e)
            )
            await asyncio.sleep(5)