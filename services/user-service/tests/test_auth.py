import pytest

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