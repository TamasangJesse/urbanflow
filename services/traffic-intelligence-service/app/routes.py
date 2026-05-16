"""
routes.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
All HTTP endpoints — mounted onto the FastAPI app in main.py.
No startup logic, no lifespan, no database init lives here.

CQRS is enforced at the endpoint level:
  Command endpoints  → use TrafficCommandRepository (writes)
  Query endpoints    → use TrafficQueryRepository   (reads)
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.commands  import TrafficCommandRepository
from app.queries   import TrafficQueryRepository
from app.ml_model  import train_model, load_model, predict_congestion
from app.models    import (
    TrafficRecordCreate,
    TrafficRecordResponse,
    PredictResponse,
    ModelStatusResponse,
    RetrainResponse,
    LocationsResponse,
    HealthResponse,
)
import app.state as state

logger = logging.getLogger(__name__)

router = APIRouter()


# ── GET /health ───────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Liveness check",
)
def health_check():
    """
    Returns 200 OK if the service is running.
    Used by Docker healthcheck and any upstream load balancer.
    """
    return HealthResponse(status="ok", service="traffic-intelligence-service")


# ── GET /locations ────────────────────────────────────────────────────────────

@router.get(
    "/locations",
    response_model=LocationsResponse,
    tags=["Data"],
    summary="List all valid location names",
)
def get_locations():
    """
    Returns every distinct location name currently in the database.
    Call this first to know which values are valid for /predict.
    """
    repo      = TrafficQueryRepository()
    locations = repo.get_distinct_locations()
    return LocationsResponse(locations=locations, total=len(locations))


# ── GET /traffic-data ─────────────────────────────────────────────────────────

@router.get(
    "/traffic-data",
    response_model=list[TrafficRecordResponse],
    tags=["Data"],
    summary="Fetch all traffic records",
)
def get_traffic_data(
    location: str | None = Query(
        default=None,
        description="Filter by location name (case-insensitive). Omit to return all records.",
        examples={"Mokolo Market": {"value": "Mokolo Market"}},
    )
):
    """
    CQRS Query side.
    Returns all records ordered by created_at descending.
    Optionally filter by location name.
    """
    repo = TrafficQueryRepository()
    if location:
        records = repo.get_traffic_records_by_location(location)
    else:
        records = repo.get_all_traffic_records()
    return records


# ── POST /traffic-data ────────────────────────────────────────────────────────

@router.post(
    "/traffic-data",
    response_model=TrafficRecordResponse,
    status_code=201,
    tags=["Data"],
    summary="Submit a new traffic record",
)
def create_traffic_record(payload: TrafficRecordCreate):
    """
    CQRS Command side.
    Accepts a real-world traffic reading and persists it to PostgreSQL.
    Does not automatically retrain the model — call POST /model/retrain for that.
    """
    repo = TrafficCommandRepository()
    try:
        record = repo.insert_traffic_record(
            location_name    = payload.location_name,
            latitude         = payload.latitude,
            longitude        = payload.longitude,
            day_of_week      = payload.day_of_week,
            hour             = payload.hour,
            congestion_level = payload.congestion_level,
            source           = payload.source,
        )
        return record
    except Exception as e:
        logger.error("Failed to insert traffic record: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to save traffic record.")


# ── GET /predict ──────────────────────────────────────────────────────────────

@router.get(
    "/predict",
    response_model=PredictResponse,
    tags=["Prediction"],
    summary="Predict congestion level for a location and time",
)
def predict(
    location_name: str   = Query(..., description="Name of the location",        examples={"example": {"value": "Carrefour Warda"}}),
    latitude:      float = Query(..., description="Latitude of the location",     examples={"example": {"value": 3.8731}}),
    longitude:     float = Query(..., description="Longitude of the location",    examples={"example": {"value": 11.5321}}),
    day_of_week:   str   = Query(..., description="Day of the week",              examples={"example": {"value": "Friday"}}),
    hour:          int   = Query(..., ge=0, le=23, description="Hour (0–23)",     examples={"example": {"value": 18}}),
):
    """
    CQRS Query side.
    Checks active_incident_boosts first — if a live incident boost exists
    for this location it returns immediately without calling the ML model.
    Otherwise runs the RandomForestClassifier and returns the prediction.
    """
    if state._model_bundle is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model is not loaded. Training may still be in progress "
                "or failed at startup. Check logs or call POST /model/retrain."
            ),
        )
    try:
        result = predict_congestion(
            location_name          = location_name,
            latitude               = latitude,
            longitude              = longitude,
            day_of_week            = day_of_week,
            hour                   = hour,
            model_bundle           = state._model_bundle,
            active_incident_boosts = state.active_incident_boosts,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Prediction failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Prediction failed.")


# ── GET /model/status ─────────────────────────────────────────────────────────

@router.get(
    "/model/status",
    response_model=ModelStatusResponse,
    tags=["Model"],
    summary="Report model training status and accuracy",
)
def model_status():
    """
    Returns whether the model is loaded, how many records it trained on,
    and its test accuracy.
    """
    if state._model_bundle is None or state._training_summary is None:
        return ModelStatusResponse(status="not_trained")

    return ModelStatusResponse(
        status        = "ready",
        records_used  = state._training_summary.get("records_used"),
        test_accuracy = state._training_summary.get("test_accuracy"),
        classes       = state._training_summary.get("classes"),
        model_path    = state._training_summary.get("model_path"),
    )


# ── POST /model/retrain ───────────────────────────────────────────────────────

@router.post(
    "/model/retrain",
    response_model=RetrainResponse,
    tags=["Model"],
    summary="Retrain the model from current database data",
)
def retrain_model():
    """
    CQRS Command side.
    Triggers a full retrain using all current records in traffic_data —
    including any new real-world records submitted since last training.
    Replaces the in-memory model bundle and overwrites model.pkl on disk.
    """
    logger.info("Manual retrain triggered via POST /model/retrain ...")
    try:
        state._training_summary = train_model()
        state._model_bundle     = load_model()
        logger.info(
            "Retrain complete. Records: %d | Accuracy: %.2f%%",
            state._training_summary["records_used"],
            state._training_summary["test_accuracy"] * 100,
        )
        return RetrainResponse(**state._training_summary)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Retrain failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Model retraining failed.")