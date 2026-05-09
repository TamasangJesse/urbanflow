"""
main.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
FastAPI application entry point.

Endpoints:
  GET  /health              — liveness check for Docker and load balancers
  GET  /locations           — list all valid location names in the dataset
  GET  /traffic-data        — fetch all traffic records (query side)
  POST /traffic-data        — submit a new traffic record (command side)
  GET  /predict             — predict congestion for a location/time
  GET  /model/status        — report model training status and accuracy
  POST /model/retrain       — retrain the model from current DB data

Startup flow:
  1. init_db()       — initialise PostgreSQL connection pool
  2. train_model()   — load all records, train RandomForestClassifier, save model.pkl
  3. load_model()    — load model.pkl into memory, cache as _model_bundle

Shutdown flow:
  1. close_db()      — close all connections in the pool cleanly
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from app.database import init_db, close_db
from app.commands import TrafficCommandRepository
from app.queries  import TrafficQueryRepository
from app.ml_model import train_model, load_model, predict_congestion
from app.models   import (
    TrafficRecordCreate,
    TrafficRecordResponse,
    PredictResponse,
    ModelStatusResponse,
    RetrainResponse,
    LocationsResponse,
    HealthResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory model cache
# Loaded once at startup — never read from disk per request
# ---------------------------------------------------------------------------
_model_bundle: dict | None = None
_training_summary: dict | None = None


# ---------------------------------------------------------------------------
# LIFESPAN — startup and shutdown logic
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model_bundle, _training_summary

    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Starting Traffic Intelligence Service ...")

    logger.info("Initialising database connection pool ...")
    init_db()
    logger.info("Database pool ready.")

    logger.info("Training model from PostgreSQL data ...")
    try:
        _training_summary = train_model()
        _model_bundle     = load_model()
        logger.info(
            "Model ready. Records used: %d | Test accuracy: %.2f%%",
            _training_summary["records_used"],
            _training_summary["test_accuracy"] * 100,
        )
    except Exception as e:
        logger.error("Model training failed at startup: %s", str(e))
        logger.warning("Service is running but /predict will be unavailable until retrain.")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("Shutting down — closing database connections ...")
    close_db()
    logger.info("Traffic Intelligence Service stopped.")


# ---------------------------------------------------------------------------
# APP INSTANCE
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UrbanFlow — Traffic Intelligence Service",
    description=(
        "Predicts road congestion levels across Yaoundé using a "
        "RandomForestClassifier trained on historical traffic patterns."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

# ── GET /health ──────────────────────────────────────────────────────────────

@app.get(
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


# ── GET /locations ───────────────────────────────────────────────────────────

@app.get(
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


# ── GET /traffic-data ────────────────────────────────────────────────────────

@app.get(
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
    Returns all records in traffic_data ordered by created_at descending.
    Optionally filter by location name.
    """
    repo = TrafficQueryRepository()

    if location:
        records = repo.get_traffic_records_by_location(location)
    else:
        records = repo.get_all_traffic_records()

    return records


# ── POST /traffic-data ───────────────────────────────────────────────────────

@app.post(
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


# ── GET /predict ─────────────────────────────────────────────────────────────

@app.get(
    "/predict",
    response_model=PredictResponse,
    tags=["Prediction"],
    summary="Predict congestion level for a location and time",
)
def predict(
    location_name: str = Query(..., description="Name of the location", examples={"Carrefour Warda": {"value": "Carrefour Warda"}}),
    latitude:      float = Query(..., description="Latitude of the location",  examples={"Warda lat": {"value": 3.8731}}),
    longitude:     float = Query(..., description="Longitude of the location", examples={"Warda lng": {"value": 11.5321}}),
    day_of_week:   str   = Query(..., description="Day of the week",           examples={"Friday": {"value": "Friday"}}),
    hour:          int   = Query(..., ge=0, le=23, description="Hour of the day (0–23)", examples={"Evening rush": {"value": 18}}),
):
    """
    CQRS Query side.
    Uses the in-memory RandomForestClassifier to predict congestion.
    The model is loaded at startup and cached — no disk I/O per request.

    Returns the predicted congestion level and the model's confidence score.
    """
    if _model_bundle is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Model is not loaded. The service may still be training, "
                "or training failed at startup. Check logs or call POST /model/retrain."
            ),
        )

    try:
        result = predict_congestion(
            location_name = location_name,
            latitude      = latitude,
            longitude     = longitude,
            day_of_week   = day_of_week,
            hour          = hour,
            model_bundle  = _model_bundle,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Prediction failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Prediction failed.")


# ── GET /model/status ────────────────────────────────────────────────────────

@app.get(
    "/model/status",
    response_model=ModelStatusResponse,
    tags=["Model"],
    summary="Report model training status and accuracy",
)
def model_status():
    """
    Returns whether the model is loaded, how many records it trained on,
    and its test accuracy. Useful for monitoring and debugging.
    """
    if _model_bundle is None or _training_summary is None:
        return ModelStatusResponse(status="not_trained")

    repo = TrafficQueryRepository()
    return ModelStatusResponse(
        status        = "ready",
        records_used  = _training_summary.get("records_used"),
        test_accuracy = _training_summary.get("test_accuracy"),
        classes       = _training_summary.get("classes"),
        model_path    = _training_summary.get("model_path"),
    )


# ── POST /model/retrain ──────────────────────────────────────────────────────

@app.post(
    "/model/retrain",
    response_model=RetrainResponse,
    tags=["Model"],
    summary="Retrain the model from current database data",
)
def retrain_model():
    """
    CQRS Command side.
    Triggers a full retrain of the RandomForestClassifier using all current
    records in traffic_data — including any new real-world records submitted
    via POST /traffic-data since the last training run.

    Replaces the in-memory model bundle and overwrites model.pkl on disk.
    """
    global _model_bundle, _training_summary

    logger.info("Manual retrain triggered via POST /model/retrain ...")
    try:
        _training_summary = train_model()
        _model_bundle     = load_model()
        logger.info(
            "Retrain complete. Records: %d | Accuracy: %.2f%%",
            _training_summary["records_used"],
            _training_summary["test_accuracy"] * 100,
        )
        return RetrainResponse(**_training_summary)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Retrain failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Model retraining failed.")