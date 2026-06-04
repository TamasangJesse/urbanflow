"""
models.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Pydantic schemas for all request bodies and response shapes.
Every endpoint in main.py uses these — no raw dicts in or out.

Keeping schemas here and away from main.py means:
  - Validation logic is testable independently
  - Adding a new field means changing one place, not hunting through endpoints
  - FastAPI auto-generates accurate OpenAPI docs from these schemas
"""


from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# VALID VALUES — single source of truth for accepted inputs
# ---------------------------------------------------------------------------

VALID_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

VALID_CONGESTION_LEVELS = ["Low", "Medium", "High", "Very High"]


# ---------------------------------------------------------------------------
# REQUEST SCHEMAS — what the API accepts
# ---------------------------------------------------------------------------

class TrafficRecordCreate(BaseModel):
    """
    Body for POST /traffic-data
    Submitted when a real-world traffic reading is recorded.
    """
    location_name:    str   = Field(..., min_length=2, max_length=100, examples=["Mokolo Market"])
    latitude:         float = Field(..., ge=-90,  le=90,  examples=[3.8784])
    longitude:        float = Field(..., ge=-180, le=180, examples=[11.5058])
    day_of_week:      str   = Field(..., examples=["Monday"])
    hour:             int   = Field(..., ge=0, le=23, examples=[8])
    congestion_level: str   = Field(..., examples=["High"])
    source:           str   = Field(default="api", examples=["api"])

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: str) -> str:
        if v not in VALID_DAYS:
            raise ValueError(
                f"'{v}' is not a valid day. Must be one of: {VALID_DAYS}"
            )
        return v

    @field_validator("congestion_level")
    @classmethod
    def validate_congestion(cls, v: str) -> str:
        if v not in VALID_CONGESTION_LEVELS:
            raise ValueError(
                f"'{v}' is not a valid congestion level. "
                f"Must be one of: {VALID_CONGESTION_LEVELS}"
            )
        return v


class PredictRequest(BaseModel):
    """
    Body for GET /predict (passed as query parameters, schema used for validation).
    Describes the conditions for which a congestion prediction is requested.
    """
    location_name: str = Field(..., min_length=2, max_length=100, examples=["Carrefour Warda"])
    latitude:      float = Field(..., ge=-90,  le=90,  examples=[3.8731])
    longitude:     float = Field(..., ge=-180, le=180, examples=[11.5321])
    day_of_week:   str   = Field(..., examples=["Friday"])
    hour:          int   = Field(..., ge=0, le=23, examples=[18])

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: str) -> str:
        if v not in VALID_DAYS:
            raise ValueError(
                f"'{v}' is not a valid day. Must be one of: {VALID_DAYS}"
            )
        return v


# ---------------------------------------------------------------------------
# RESPONSE SCHEMAS — what the API returns
# ---------------------------------------------------------------------------

class TrafficRecordResponse(BaseModel):
    """
    Returned by POST /traffic-data and GET /traffic-data (per record).
    """
    id:               int
    location_name:    str
    latitude:         float
    longitude:        float
    day_of_week:      str
    hour:             int
    congestion_level: str
    source:           str
    created_at:       datetime

    class Config:
        from_attributes = True


class PredictResponse(BaseModel):
    """
    Returned by GET /predict.
    confidence — probability of the predicted class (0.0 – 1.0).
    """
    location:         str
    day_of_week:      str
    hour:             int
    congestion_level: str
    confidence:       float
    boosted:          bool = False


class ModelStatusResponse(BaseModel):
    """
    Returned by GET /model/status.
    Reports whether the model is loaded and what it was trained on.
    """
    model_config = ConfigDict(protected_namespaces=())
    status:         str            # "ready" or "not_trained"
    records_used:   Optional[int]  = None
    test_accuracy:  Optional[float] = None
    classes:        Optional[list[str]] = None
    model_path:     Optional[str]  = None


class RetrainResponse(BaseModel):
    """
    Returned by POST /model/retrain.
    """
    model_config = ConfigDict(protected_namespaces=())
    status:        str
    records_used:  int
    test_accuracy: float
    classes:       list[str]
    model_path:    str


class LocationsResponse(BaseModel):
    """
    Returned by GET /locations.
    """
    locations: list[str]
    total:     int


class HealthResponse(BaseModel):
    """
    Returned by GET /health.
    Quick liveness check — used by Docker and load balancers.
    """
    status:  str   # "ok"
    service: str   # "traffic-intelligence-service"