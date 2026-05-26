from repository import incident_repository
from events import publish_incident_event

"""
CQRS — COMMAND SIDE
════════════════════════════════════════════════════════════════════
Every function here WRITES data and PUBLISHES events to Redis.
These functions NEVER perform read-only queries.
This file is the proof of the Command side of the CQRS pattern.
════════════════════════════════════════════════════════════════════
"""


async def cmd_report_incident(data: dict) -> dict:
    """
    COMMAND: Report a new incident.
    Step 1 — save to MongoDB via the repository.
    Step 2 — publish IncidentReported event to Redis Streams.
    Both steps must succeed for the command to be complete.
    """
    # Step 1: write to MongoDB
    incident_id = await incident_repository.save_incident(data)

    # Step 2: publish to Redis (Pub/Sub)
    await publish_incident_event(
        incident_id   = incident_id,
        incident_type = data["type"],
        latitude      = data["latitude"],
        longitude     = data["longitude"],
        severity      = data["severity"],
        reported_by   = data["reported_by"],
        description   = data.get("description", "")  # ← add this
    )

    return {"incident_id": incident_id}



    """
    COMMAND: Resolve an incident.
    Writes is_active=False to MongoDB. No event published.
    """




async def cmd_resolve_incident(incident_id: str) -> bool:
    # Fetch incident details before resolving so we can include them in the event
    incident = await incident_repository.find_by_id(incident_id)
    
    success = await incident_repository.resolve_incident(incident_id)
    if success and incident:
        from database import redis_client
        await redis_client.xadd("incident_stream", {
            "event":         "incident_resolved",
            "incident_id":   incident_id,
            "incident_type": incident.get("type", "Incident"),  
            "address":       incident.get("description", ""),
        })
    return success


async def cmd_delete_incident(incident_id: str) -> bool:
    """
    COMMAND: Delete a false or duplicate incident.
    Permanently removes the document from MongoDB. No event published.
    """
    return await incident_repository.delete_incident(incident_id)