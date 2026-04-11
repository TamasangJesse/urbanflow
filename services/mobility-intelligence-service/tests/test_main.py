from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mobility-intelligence-service"
    assert "model_loaded" in data
    assert "redis_connected" in data


def test_submit_traffic_report_no_redis():
    payload = {
        "location": "Warda",
        "report_type": "accident",
        "description": "Car accident near roundabout"
    }
    response = client.post("/mobility/reports", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Warda"
    assert data["report_type"] == "accident"
    assert "event_published" in data


def test_get_congestion_no_model():
    response = client.get("/mobility/congestion/Mokolo?day_of_week=0&hour_of_day=8")
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Mokolo"
    assert "congestion_level" in data
    assert "congestion_label" in data


def test_predict_no_model():
    payload = {
        "location": "Biyem-Assi",
        "day_of_week": 1,
        "hour_of_day": 7
    }
    response = client.post("/mobility/predict", json=payload)
    assert response.status_code in [200, 503]


def test_traffic_report_required_fields():
    payload = {"report_type": "accident"}
    response = client.post("/mobility/reports", json=payload)
    assert response.status_code == 422
