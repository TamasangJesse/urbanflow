from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import incidents_collection
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await incidents_collection.create_index([("location", "2dsphere")])
    print("[MongoDB] 2dsphere index ready on incidents.location")
    yield


app = FastAPI(
    title="UrbanFlow — Incident Report Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)




'''from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from database import incidents_collection
from models import ReportIncidentRequest
from cqrs.commands import (
    cmd_report_incident,
    cmd_resolve_incident,
    cmd_delete_incident
)


from cqrs.queries import (
    qry_get_incidents_near,
    qry_get_incidents_by_area,
    qry_get_incident_by_id,
    qry_get_incidents_by_user
)



# ── Startup: create the 2dsphere index if it doesn't exist ───────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await incidents_collection.create_index([("location", "2dsphere")])
    print("[MongoDB] 2dsphere index ready on incidents.location")
    yield


app = FastAPI(
    title="UrbanFlow — Incident Report Service",
    version="1.0.0",
    lifespan=lifespan
)


# ════════════════════════════════════════════════════════════════
# COMMAND ROUTES  →  delegate to cqrs/commands.py
# ════════════════════════════════════════════════════════════════

@app.post("/incidents", status_code=201)
async def report_incident(body: ReportIncidentRequest):
    result = await cmd_report_incident(body.model_dump())
    return {"message": "Incident reported successfully", **result}


@app.put("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    success = await cmd_resolve_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident resolved", "incident_id": incident_id}


@app.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: str):
    success = await cmd_delete_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"message": "Incident deleted", "incident_id": incident_id}


# ════════════════════════════════════════════════════════════════
# QUERY ROUTES  →  delegate to cqrs/queries.py
# ════════════════════════════════════════════════════════════════

@app.get("/incidents/near")
async def get_incidents_near(lat: float, lng: float, radius: float = 5000):
    incidents = await qry_get_incidents_near(lat, lng, radius)
    return {"count": len(incidents), "incidents": incidents}




@app.get("/incidents/{incident_id}")
async def get_incident_by_id(incident_id: str):
    incident = await qry_get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


# ── Health check ─────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "incident-report", "port": 8004}


@app.get("/incidents")
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
    return {"count": len(incidents), "incidents": incidents}'''