from fastapi import APIRouter, HTTPException
from models import ReportIncidentRequest, CheckRouteRequest
from cqrs.commands import (
    cmd_report_incident,
    cmd_resolve_incident,
    cmd_delete_incident
)
from cqrs.queries import (
    qry_get_incidents_near,
    qry_get_incidents_by_area,
    qry_get_incident_by_id,
    qry_get_incidents_by_user,
    qry_check_route_for_incidents
)

router = APIRouter()


# ════════════════════════════════════════════════════════════════
# COMMAND ROUTES
# ════════════════════════════════════════════════════════════════

@router.post("/incidents", status_code=201)
async def report_incident(body: ReportIncidentRequest):
    result = await cmd_report_incident(body.model_dump())
    return {"message": "Incident reported successfully", **result}


@router.put("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    success = await cmd_resolve_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident resolved", "incident_id": incident_id}


@router.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: str):
    success = await cmd_delete_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident deleted", "incident_id": incident_id}


# ════════════════════════════════════════════════════════════════
# QUERY ROUTES
# ════════════════════════════════════════════════════════════════

@router.get("/incidents/near")
async def get_incidents_near(lat: float, lng: float, radius: float = 5000):
    incidents = await qry_get_incidents_near(lat, lng, radius)
    return {"count": len(incidents), "incidents": incidents}


@router.get("/incidents")
async def get_incidents(area: str = None, reported_by: str = None):
    if reported_by:
        incidents = await qry_get_incidents_by_user(reported_by)
    elif area:
        incidents = await qry_get_incidents_by_area(area)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'area' or 'reported_by' as a query parameter"
        )
    return {"count": len(incidents), "incidents": incidents}


@router.get("/incidents/{incident_id}")
async def get_incident_by_id(incident_id: str):
    incident = await qry_get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# ── Health check ─────────────────────────────────────────────────
@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "incident-report", "port": 8004}



@router.post("/incidents/check-route")
async def check_route(body: CheckRouteRequest):
    incident = await qry_check_route_for_incidents(body.route_points)
    if incident:
        return {
            "incident_detected": True,
            "incident": {
                "id":          incident["_id"],
                "type":        incident["type"],
                "description": incident["description"],
                "latitude":    incident["latitude"],
                "longitude":   incident["longitude"],
                "severity":    incident["severity"],
                "created_at":  incident["created_at"]
            }
        }
    return {
        "incident_detected": False,
        "incident": None
    }

