from datetime import datetime, timezone
from database import redis_client

STREAM_NAME = "incident_stream"


async def publish_incident_event(
    incident_id: str,
    incident_type: str,
    latitude: float,
    longitude: float,
    severity: str
):
    """
    Publisher-Subscriber Pattern.
    Publishes an IncidentReported event to Redis Streams.
    Called ONLY from the Command side — never from queries.
    """
    payload = {
        "incident_id": incident_id,
        "type":        incident_type,
        "latitude":    str(latitude),
        "longitude":   str(longitude),
        "severity":    severity.lower(),
        "created_at":  datetime.now(timezone.utc).isoformat()
    }
    await redis_client.xadd(STREAM_NAME, payload)
    print(f"[Redis] Event published to '{STREAM_NAME}': {payload}")