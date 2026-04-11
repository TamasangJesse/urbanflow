from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "api-gateway"


def test_health_check_response_structure():
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "service" in data
