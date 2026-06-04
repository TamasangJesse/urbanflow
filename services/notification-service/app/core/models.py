from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class IncidentEvent(BaseModel):
    """
    Shape of the event payload published to Redis Streams by the
    Incident Report Service (Publisher-Subscriber pattern).
    """

    incident_id: str
    type: str
    latitude: float
    longitude: float
    severity: Literal["low", "medium", "high", "critical"]
    created_at: datetime
    reported_by: str | None = None
    description: str | None = None  # ← add this


class Notification(BaseModel):
    """
    A single notification stored under notification:{user_id} in Redis.
    """

    incident_id: str
    type: str
    severity: str
    latitude: float
    longitude: float
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False


class NotificationListResponse(BaseModel):
    user_id: str
    notifications: list[Notification]
    total: int