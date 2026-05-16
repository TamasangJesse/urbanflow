import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("DATABASE_NAME", "urbanflow_rag_test")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("INCIDENT_SERVICE_URL", "http://localhost:8004")
os.environ.setdefault("TRAFFIC_SERVICE_URL", "http://localhost:8002")

# Patch motor before importing app
with patch("motor.motor_asyncio.AsyncIOMotorClient"):
    from app.main import app

client = TestClient(app)

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]


def make_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)


# ─── Test 1 ──────────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ─── Test 2 ──────────────────────────────────────────────────────────────────

def test_chat_requires_auth():
    response = client.post(
        "/chat",
        json={"question": "Is there traffic in Bastos right now?"},
    )
    assert response.status_code == 401


# ─── Test 3 ──────────────────────────────────────────────────────────────────

def test_chat_returns_answer():
    token = make_token("user-123")

    mock_response = MagicMock()
    mock_response.text = "Traffic in Bastos is currently light with no reported incidents."

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models

    with (
        patch("app.rag_engine.genai.Client", return_value=mock_client),
        patch(
            "app.rag_engine.get_nearby_incidents",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "app.rag_engine.get_traffic_prediction",
            new=AsyncMock(return_value="low"),
        ),
        patch(
            "app.repository.ChatRepository.save_chat",
            new=AsyncMock(return_value="fake-id"),
        ),
    ):
        response = client.post(
            "/chat",
            json={"question": "Is there traffic in Bastos right now?"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    assert data["question"] == "Is there traffic in Bastos right now?"


# ─── Test 4 ──────────────────────────────────────────────────────────────────

def test_get_history_requires_auth():
    response = client.get("/chat/history/some-user-id")
    assert response.status_code == 401