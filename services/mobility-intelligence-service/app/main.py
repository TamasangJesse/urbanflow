from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Optional
import os
import joblib
import numpy as np
import redis
import json

app = FastAPI(
    title="UrbanFlow Mobility Intelligence Service",
    description="Traffic prediction, crowd-sourced reports, and route recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MODEL_PATH = os.getenv("MODEL_PATH", "/app/ml_model/traffic_model.joblib")

model = None
redis_client = None


@app.on_event("startup")
async def startup_event():
    global model, redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        redis_client.ping()
        print("Redis connection established")
    except Exception as e:
        print(f"Redis not available: {e}")
        redis_client = None

    try:
        model = joblib.load(MODEL_PATH)
        print("ML model loaded successfully")
    except Exception as e:
        print(f"ML model not found yet: {e}")
        model = None


class TrafficReport(BaseModel):
    location: str
    report_type: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PredictionRequest(BaseModel):
    location: str
    day_of_week: int
    hour_of_day: int


class RouteRequest(BaseModel):
    origin: str
    destination: str
    day_of_week: int
    hour_of_day: int


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "mobility-intelligence-service",
        "model_loaded": model is not None,
        "redis_connected": redis_client is not None
    }


@app.post("/mobility/predict")
async def predict_congestion(request: PredictionRequest):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction model not loaded yet"
        )
    day_map = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
    features = np.array([[
        day_map.get(request.day_of_week, 0),
        request.hour_of_day,
        hash(request.location) % 100
    ]])
    prediction = model.predict(features)[0]
    congestion_labels = {0: "Low", 1: "Medium", 2: "High", 3: "Very High"}
    return {
        "location": request.location,
        "day_of_week": request.day_of_week,
        "hour_of_day": request.hour_of_day,
        "congestion_level": int(prediction),
        "congestion_label": congestion_labels.get(int(prediction), "Unknown")
    }


@app.post("/mobility/reports")
async def submit_traffic_report(report: TrafficReport):
    event = {
        "event_type": "TrafficIncidentReported",
        "location": report.location,
        "report_type": report.report_type,
        "description": report.description,
        "latitude": report.latitude,
        "longitude": report.longitude
    }
    if redis_client:
        redis_client.xadd("traffic_events", event)
        published = True
    else:
        published = False

    return {
        "message": "Traffic report received",
        "location": report.location,
        "report_type": report.report_type,
        "event_published": published
    }


@app.get("/mobility/congestion/{location}")
async def get_congestion(location: str, day_of_week: int = 0, hour_of_day: int = 8):
    if model is None:
        return {
            "location": location,
            "congestion_level": 1,
            "congestion_label": "Medium",
            "note": "Model not loaded, returning default"
        }
    features = np.array([[day_of_week, hour_of_day, hash(location) % 100]])
    prediction = model.predict(features)[0]
    congestion_labels = {0: "Low", 1: "Medium", 2: "High", 3: "Very High"}
    return {
        "location": location,
        "congestion_level": int(prediction),
        "congestion_label": congestion_labels.get(int(prediction), "Unknown")
    }
