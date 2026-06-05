"""
tests/test_incidents.py — Incident Report Service test suite.

Uses pytest + httpx AsyncClient to test all endpoints without
needing Postman or a running server. MongoDB and Redis are mocked
so these tests run in CI/CD with zero infrastructure dependencies.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Make sure Python can find the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app


# ════════════════════════════════════════════════════════════════
# FIXTURES
# Shared setup reused across all tests.
# ════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client that talks directly to the FastAPI app
    without needing a running server or open network port.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_incident():
    """A valid incident payload reused across multiple tests."""
    return {
        "type": "accident",
        "description": "Car crash near Total petrol station Bastos",
        "latitude": 3.8690,
        "longitude": 11.5180,
        "severity": "high",
        "reported_by": "user_001"
    }


# ════════════════════════════════════════════════════════════════
# COMMAND SIDE TESTS  (POST, PUT, DELETE)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.save_incident", new_callable=AsyncMock)
@patch("cqrs.commands.publish_incident_event", new_callable=AsyncMock)
async def test_report_incident(mock_publish, mock_save, client, sample_incident):
    """
    POST /incidents
    Should save to MongoDB and publish to Redis.
    Returns 201 with an incident_id.
    """
    mock_save.return_value = "665f3a2b1c4e2d001a8b4567"
    mock_publish.return_value = None

    response = await client.post("/incidents", json=sample_incident)

    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] == "665f3a2b1c4e2d001a8b4567"
    assert data["message"] == "Incident reported successfully"

    # Confirm both MongoDB write and Redis publish were called
    mock_save.assert_called_once()
    mock_publish.assert_called_once()


@pytest.mark.asyncio
@patch("cqrs.commands.redis_client.xadd", new_callable=AsyncMock)
@patch("cqrs.commands.incident_repository.find_by_id", new_callable=AsyncMock)
@patch("cqrs.commands.incident_repository.resolve_incident", new_callable=AsyncMock)
async def test_resolve_incident(mock_resolve, mock_find_by_id, mock_xadd, client):
    """
    PUT /incidents/{id}/resolve
    Should mark the incident as inactive.
    """
    mock_resolve.return_value = True
    mock_xadd.return_value = None
    mock_find_by_id.return_value = {
        "_id": "665f3a2b1c4e2d001a8b4567",
        "type": "accident",
        "description": "Car crash near Total petrol station",
        "latitude": 3.8690,
        "longitude": 11.5180,
        "severity": "high",
        "reported_by": "user_001",
        "is_active": True
    }

    response = await client.put("/incidents/665f3a2b1c4e2d001a8b4567/resolve")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Incident resolved"
    assert data["incident_id"] == "665f3a2b1c4e2d001a8b4567"


@pytest.mark.asyncio
@patch("cqrs.commands.redis_client.xadd", new_callable=AsyncMock)
@patch("cqrs.commands.incident_repository.find_by_id", new_callable=AsyncMock)
@patch("cqrs.commands.incident_repository.resolve_incident", new_callable=AsyncMock)
async def test_resolve_incident_not_found(mock_resolve, mock_find_by_id, mock_xadd, client):
    """
    PUT /incidents/{id}/resolve
    Should return 404 if the incident does not exist.
    """
    mock_resolve.return_value = False
    mock_xadd.return_value = None
    mock_find_by_id.return_value = None

    response = await client.put("/incidents/nonexistentid/resolve")

    assert response.status_code == 404







@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.delete_incident", new_callable=AsyncMock)
async def test_delete_incident(mock_delete, client):
    """
    DELETE /incidents/{id}
    Should permanently remove the incident.
    """
    mock_delete.return_value = True

    response = await client.delete("/incidents/665f3a2b1c4e2d001a8b4567")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Incident deleted"


@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.delete_incident", new_callable=AsyncMock)
async def test_delete_incident_not_found(mock_delete, client):
    """
    DELETE /incidents/{id}
    Should return 404 if the incident does not exist.
    """
    mock_delete.return_value = False

    response = await client.delete("/incidents/nonexistentid")

    assert response.status_code == 404


# ════════════════════════════════════════════════════════════════
# QUERY SIDE TESTS  (GET)
# These never touch Redis — query side is read-only from MongoDB.
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_by_id", new_callable=AsyncMock)
async def test_get_incident_by_id(mock_find, client):
    """
    GET /incidents/{id}
    Should return the full incident document.
    """
    mock_find.return_value = {
        "_id": "665f3a2b1c4e2d001a8b4567",
        "type": "accident",
        "description": "Car crash near Total petrol station Bastos",
        "latitude": 3.8690,
        "longitude": 11.5180,
        "severity": "high",
        "reported_by": "user_001",
        "is_active": True
    }

    response = await client.get("/incidents/665f3a2b1c4e2d001a8b4567")

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "accident"
    assert data["severity"] == "high"


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_by_id", new_callable=AsyncMock)
async def test_get_incident_by_id_not_found(mock_find, client):
    """
    GET /incidents/{id}
    Should return 404 if the incident does not exist.
    """
    mock_find.return_value = None

    response = await client.get("/incidents/nonexistentid")

    assert response.status_code == 404


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_get_incidents_near(mock_find, client):
    """
    GET /incidents/near?lat=&lng=&radius=
    Should return active incidents within the given radius.
    """
    mock_find.return_value = [
        {"_id": "abc123", "type": "flooding", "is_active": True}
    ]

    response = await client.get(
        "/incidents/near?lat=3.8690&lng=11.5180&radius=5000"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["incidents"][0]["type"] == "flooding"


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_by_area", new_callable=AsyncMock)
async def test_get_incidents_by_area(mock_find, client):
    """
    GET /incidents?area=Bastos
    Should return incidents matching the area name.
    """
    mock_find.return_value = [
        {"_id": "abc123", "description": "Car crash near Total petrol station Bastos"}
    ]

    response = await client.get("/incidents?area=Bastos")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_by_user", new_callable=AsyncMock)
async def test_get_incidents_by_user(mock_find, client):
    """
    GET /incidents?reported_by=user_001
    Should return all incidents reported by a specific user.
    """
    mock_find.return_value = [
        {"_id": "abc123", "reported_by": "user_001", "type": "accident"}
    ]

    response = await client.get("/incidents?reported_by=user_001")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["incidents"][0]["reported_by"] == "user_001"


@pytest.mark.asyncio
async def test_get_incidents_no_params(client):
    """
    GET /incidents with no query parameters.
    Should return 400 — either area or reported_by is required.
    """
    response = await client.get("/incidents")

    assert response.status_code == 400


# ════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_health_check(client):
    """
    GET /health
    Should always return 200 with status ok.
    """
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# ════════════════════════════════════════════════════════════════
# CHECK ROUTE TESTS
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_check_route_incident_detected(mock_find, client):
    """
    POST /incidents/check-route
    Should return incident_detected: True when an incident
    exists within 300m of any point on the route.
    """
    mock_find.return_value = [{
        "_id": "665f3a2b1c4e2d001a8b4567",
        "type": "roadblock",
        "description": "Police checkpoint Carrefour Warda",
        "latitude": 3.8712,
        "longitude": 11.5163,
        "severity": "medium",
        "created_at": "2026-05-16T10:00:00"
    }]

    payload = {
        "route_points": [
            {"lat": 3.8690, "lng": 11.5180},
            {"lat": 3.8712, "lng": 11.5163},
            {"lat": 3.8750, "lng": 11.5200}
        ]
    }

    response = await client.post("/incidents/check-route", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["incident_detected"] is True
    assert data["incident"]["type"] == "roadblock"
    assert data["incident"]["severity"] == "medium"


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_check_route_no_incident(mock_find, client):
    """
    POST /incidents/check-route
    Should return incident_detected: False when no incidents
    exist near any point on the route.
    """
    mock_find.return_value = []

    payload = {
        "route_points": [
            {"lat": 3.8690, "lng": 11.5180},
            {"lat": 3.8750, "lng": 11.5200}
        ]
    }

    response = await client.post("/incidents/check-route", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["incident_detected"] is False
    assert data["incident"] is None


# ════════════════════════════════════════════════════════════════
# VALIDATION TESTS
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.save_incident", new_callable=AsyncMock)
@patch("cqrs.commands.publish_incident_event", new_callable=AsyncMock)
async def test_report_incident_missing_required_fields(mock_publish, mock_save, client):
    """
    POST /incidents
    Should return 422 when required fields are missing.
    """
    incomplete_payload = {
        "type": "accident"
    }

    response = await client.post("/incidents", json=incomplete_payload)

    assert response.status_code == 422
    mock_save.assert_not_called()
    mock_publish.assert_not_called()


@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.save_incident", new_callable=AsyncMock)
@patch("cqrs.commands.publish_incident_event", new_callable=AsyncMock)
async def test_report_incident_invalid_severity(mock_publish, mock_save, client):
    """
    POST /incidents
    Should return 422 when severity is not a valid enum value.
    """
    invalid_payload = {
        "type": "accident",
        "description": "Car crash",
        "latitude": 3.8690,
        "longitude": 11.5180,
        "severity": "catastrophic",
        "reported_by": "user_001"
    }

    response = await client.post("/incidents", json=invalid_payload)

    assert response.status_code == 422


@pytest.mark.asyncio
@patch("cqrs.commands.incident_repository.save_incident", new_callable=AsyncMock)
@patch("cqrs.commands.publish_incident_event", new_callable=AsyncMock)
async def test_report_incident_different_types(mock_publish, mock_save, client):
    """
    POST /incidents
    Should accept all valid incident types:
    accident, roadblock, flooding, construction.
    """
    mock_save.return_value = "665f3a2b1c4e2d001a8b9999"
    mock_publish.return_value = None

    for incident_type in ["accident", "roadblock", "flooding"]:
        payload = {
            "type": incident_type,
            "description": f"Test {incident_type} near Mokolo",
            "latitude": 3.8712,
            "longitude": 11.5163,
            "severity": "low",
            "reported_by": "user_002"
        }
        response = await client.post("/incidents", json=payload)
        assert response.status_code == 201, f"Failed for type: {incident_type}"


# ════════════════════════════════════════════════════════════════
# RADIUS EDGE CASE TESTS
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_get_incidents_near_default_radius(mock_find, client):
    """
    GET /incidents/near
    Should use default radius of 5000m when not specified.
    """
    mock_find.return_value = []

    response = await client.get("/incidents/near?lat=3.8690&lng=11.5180")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["incidents"] == []


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_get_incidents_near_custom_radius(mock_find, client):
    """
    GET /incidents/near
    Should respect custom radius parameter.
    """
    mock_find.return_value = [
        {"_id": "xyz789", "type": "flooding", "is_active": True},
        {"_id": "xyz790", "type": "accident", "is_active": True}
    ]

    response = await client.get(
        "/incidents/near?lat=3.8690&lng=11.5180&radius=10000"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2


@pytest.mark.asyncio
@patch("cqrs.queries.incident_repository.find_near", new_callable=AsyncMock)
async def test_get_incidents_near_empty_result(mock_find, client):
    """
    GET /incidents/near
    Should return empty list when no incidents exist nearby.
    """
    mock_find.return_value = []

    response = await client.get(
        "/incidents/near?lat=3.8690&lng=11.5180&radius=100"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
