from pydantic import BaseModel
from typing import Optional
from datetime import datetime




class CheckRouteRequest(BaseModel):
    route_points: list[list[float]]




class ReportIncidentRequest(BaseModel):
    type: str            # e.g. "accident", "flooding", "roadblock"
    description: str
    latitude: float
    longitude: float
    severity: str        # "low", "medium", "high"
    reported_by: str     # user_id as a string


class ResolveIncidentRequest(BaseModel):
    pass                 # no body needed — ID comes from the URL


class IncidentResponse(BaseModel):
    incident_id: str
    type: str
    description: str
    latitude: float
    longitude: float
    severity: str
    reported_by: str
    created_at: datetime
    is_active: bool