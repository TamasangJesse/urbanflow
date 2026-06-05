import pytest
import json
from unittest.mock import AsyncMock, patch
pytestmark = pytest.mark.asyncio

# ─── Register ───────────────────────────────────────────────────

async def test_register_success(client):
    response = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client):
    # Register once
    await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    # Try again with same email
    response = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    assert response.status_code == 409


# ─── Login ───────────────────────────────────────────────────────

async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    response = await client.post("/auth/login", json={
        "email": "test@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user_id" in data


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    response = await client.post("/auth/login", json={
        "email": "test@gmail.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


async def test_login_nonexistent_user(client):
    response = await client.post("/auth/login", json={
        "email": "ghost@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 401



# ─── Logout ──────────────────────────────────────────────────────

async def test_logout_success(client):
    await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    login = await client.post("/auth/login", json={
        "email": "test@gmail.com",
        "password": "password123"
    })
    token = login.json()["access_token"]
    response = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


async def test_logout_unauthenticated(client):
    response = await client.post("/auth/logout")
    assert response.status_code in (401, 403)


async def test_logout_invalid_token(client):
    response = await client.post("/auth/logout", headers={"Authorization": "Bearer bad.token.here"})
    assert response.status_code == 401


# ─── Verify ──────────────────────────────────────────────────────

async def test_verify_token_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.get("/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == user_id


async def test_verify_token_invalid(client):
    response = await client.get("/auth/verify", headers={"Authorization": "Bearer bad.token.here"})
    assert response.status_code == 401


async def test_verify_token_missing(client):
    response = await client.get("/auth/verify")
    assert response.status_code in (401, 403)


# ─── GET /users/{user_id} ────────────────────────────────────────

async def test_get_own_profile_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id


async def test_get_profile_not_found(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    response = await client.get("/users/00000000-0000-0000-0000-000000000000", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


async def test_get_profile_unauthenticated(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    user_id = register.json()["user_id"]
    response = await client.get(f"/users/{user_id}")
    assert response.status_code in (401, 403)


# ─── PUT /users/{user_id} ────────────────────────────────────────

async def test_update_own_profile_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.put(
        f"/users/{user_id}",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


async def test_update_profile_forbidden(client):
    r1 = await client.post("/auth/register", json={
        "email": "a@gmail.com",
        "password": "password123",
        "full_name": "User A"
    })
    r2 = await client.post("/auth/register", json={
        "email": "b@gmail.com",
        "password": "password123",
        "full_name": "User B"
    })
    user_id_a = r1.json()["user_id"]
    token_b = r2.json()["access_token"]
    response = await client.put(
        f"/users/{user_id_a}",
        json={"full_name": "Hacker"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code in (401, 403)


async def test_update_profile_unauthenticated(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    user_id = register.json()["user_id"]
    response = await client.put(f"/users/{user_id}", json={"full_name": "No Token"})
    assert response.status_code in (401, 403)


# ─── DELETE /users/{user_id} ────────────────────────────────────

async def test_delete_own_account_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.delete(f"/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


async def test_delete_account_forbidden(client):
    r1 = await client.post("/auth/register", json={
        "email": "a@gmail.com",
        "password": "password123",
        "full_name": "User A"
    })
    r2 = await client.post("/auth/register", json={
        "email": "b@gmail.com",
        "password": "password123",
        "full_name": "User B"
    })
    user_id_a = r1.json()["user_id"]
    token_b = r2.json()["access_token"]
    response = await client.delete(f"/users/{user_id_a}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 403


async def test_delete_unauthenticated(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    user_id = register.json()["user_id"]
    response = await client.delete(f"/users/{user_id}")
    assert response.status_code in (401, 403)


# ─── PUT /users/{user_id}/location ──────────────────────────────

async def test_update_location_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    with patch("app.redis_client.redis_client.setex", new_callable=AsyncMock):
        response = await client.put(
            f"/users/{user_id}/location",
            json={"latitude": 3.848, "longitude": 11.502},
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert response.json()["message"] == "Location updated"


async def test_update_location_forbidden(client):
    r1 = await client.post("/auth/register", json={
        "email": "a@gmail.com",
        "password": "password123",
        "full_name": "User A"
    })
    r2 = await client.post("/auth/register", json={
        "email": "b@gmail.com",
        "password": "password123",
        "full_name": "User B"
    })
    user_id_a = r1.json()["user_id"]
    token_b = r2.json()["access_token"]
    response = await client.put(
        f"/users/{user_id_a}/location",
        json={"latitude": 3.848, "longitude": 11.502},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403


async def test_update_location_missing_coordinates(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.put(
        f"/users/{user_id}/location",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


# ─── GET /users/{user_id}/routes ────────────────────────────────

async def test_get_routes_empty(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.get(f"/users/{user_id}/routes", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["routes"] == []


async def test_get_routes_unauthenticated(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    user_id = register.json()["user_id"]
    response = await client.get(f"/users/{user_id}/routes")
    assert response.status_code in (401, 403)


# ─── POST /users/{user_id}/routes ───────────────────────────────

async def test_save_route_success(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.post(
        f"/users/{user_id}/routes",
        json={"origin": "Home", "destination": "Work"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["origin"] == "Home"
    assert data["destination"] == "Work"


async def test_save_route_forbidden(client):
    r1 = await client.post("/auth/register", json={
        "email": "a@gmail.com",
        "password": "password123",
        "full_name": "User A"
    })
    r2 = await client.post("/auth/register", json={
        "email": "b@gmail.com",
        "password": "password123",
        "full_name": "User B"
    })
    user_id_a = r1.json()["user_id"]
    token_b = r2.json()["access_token"]
    response = await client.post(
        f"/users/{user_id_a}/routes",
        json={"origin": "Home", "destination": "Work"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403


async def test_save_route_missing_fields(client):
    register = await client.post("/auth/register", json={
        "email": "test@gmail.com",
        "password": "password123",
        "full_name": "Test User"
    })
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]
    response = await client.post(
        f"/users/{user_id}/routes",
        json={"origin": "Only Origin"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


