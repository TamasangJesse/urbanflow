"""
test_gateway.py — Integration tests for the full API Gateway.

Tests the complete request flow through the FastAPI app:
  client → rate limiter → auth → proxy → (mocked) downstream

No real Redis, no real downstream services — everything is mocked.

Scenarios covered:
  - Health check returns 200 with correct payload
  - Public routes (register, login) pass through without a token
  - Protected routes require a valid Bearer token
  - Missing Authorization header returns 401
  - Malformed Authorization header returns 401
  - Invalid/expired token returns 401
  - Blacklisted token returns 401
  - Valid token forwards request to downstream and returns its response
  - Unknown path returns 404
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import Response as HttpxResponse

from tests.conftest import make_token, make_expired_token


# =============================================================================
# Helpers
# =============================================================================

def mock_downstream_response(status_code: int = 200, json: dict = None) -> MagicMock:
    """
    Build a fake httpx Response that the mock http_client will return
    when the gateway tries to forward a request downstream.
    """
    import json as json_lib
    body = json_lib.dumps(json or {}).encode()

    response = MagicMock()
    response.status_code = status_code
    response.content     = body
    response.headers     = {"content-type": "application/json"}
    return response


# =============================================================================
# Health check
# =============================================================================

class TestHealthCheck:

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client):
        ac, mock_redis, _ = client
        response = await ac.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_correct_payload(self, client):
        ac, mock_redis, _ = client
        response = await ac.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "api-gateway"
        assert "redis" in data

    @pytest.mark.asyncio
    async def test_health_check_does_not_require_token(self, client):
        """Health check is a public route — no Authorization header needed."""
        ac, _, _ = client
        response = await ac.get("/health")
        assert response.status_code == 200


# =============================================================================
# Public routes — no token required
# =============================================================================

class TestPublicRoutes:

    @pytest.mark.asyncio
    async def test_login_passes_without_token(self, client):
        """POST /auth/login must be reachable without any token."""
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(200, {"access_token": "abc"})
        )
        response = await ac.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        # Gateway should forward it — not reject with 401
        assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_register_passes_without_token(self, client):
        """POST /auth/register must be reachable without any token."""
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(201, {"id": "user-1"})
        )
        response = await ac.post("/auth/register", json={
            "email": "new@example.com",
            "password": "password123"
        })
        assert response.status_code != 401


# =============================================================================
# Authentication enforcement on protected routes
# =============================================================================

class TestAuthEnforcement:

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self, client):
        """A request to a protected route with no Authorization header → 401."""
        ac, _, _ = client
        response = await ac.get("/users/42")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_auth_header_returns_401(self, client):
        """'Token abc' instead of 'Bearer abc' → 401."""
        ac, _, _ = client
        response = await ac.get("/users/42", headers={"Authorization": "Token abc123"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client):
        """A random string that is not a valid JWT → 401."""
        ac, _, _ = client
        response = await ac.get("/users/42", headers={
            "Authorization": "Bearer not.a.real.token"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client):
        """A correctly signed but expired JWT → 401."""
        ac, _, _ = client
        token = make_expired_token()
        response = await ac.get("/users/42", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_blacklisted_token_returns_401(self, client):
        """A valid token that is in the Redis blacklist → 401."""
        ac, mock_redis, _ = client

        # Simulate the token being blacklisted
        mock_redis.exists = AsyncMock(return_value=1)

        token = make_token()
        response = await ac.get("/users/42", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 401


# =============================================================================
# Successful request forwarding
# =============================================================================

class TestRequestForwarding:

    @pytest.mark.asyncio
    async def test_valid_token_forwards_to_downstream(self, client):
        """
        A valid token on a protected route should pass auth and be
        forwarded to the downstream service. The gateway returns
        whatever the downstream responded with.
        """
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(200, {"id": "user-123"})
        )

        token = make_token()
        response = await ac.get("/users/42", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 200
        assert mock_http.request.called

    @pytest.mark.asyncio
    async def test_gateway_forwards_correct_method(self, client):
        """The gateway must forward the same HTTP method — POST stays POST."""
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(201, {"incident_id": "abc"})
        )

        token = make_token()
        await ac.post(
            "/incidents",
            json={"type": "accident", "description": "Test"},
            headers={"Authorization": f"Bearer {token}"}
        )

        call_args = mock_http.request.call_args
        assert call_args.kwargs["method"] == "POST"

    @pytest.mark.asyncio
    async def test_gateway_forwards_correct_path(self, client):
        """The gateway must forward the original path to the downstream."""
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(200, {})
        )

        token = make_token()
        await ac.get("/incidents/near", headers={
            "Authorization": f"Bearer {token}"
        })

        call_args = mock_http.request.call_args
        assert "/incidents/near" in call_args.kwargs["url"]

    @pytest.mark.asyncio
    async def test_downstream_500_is_returned_to_client(self, client):
        """
        If the downstream service returns a 500, the gateway must pass
        it through — it is not the gateway's job to transform error responses.
        """
        ac, _, mock_http = client
        mock_http.request = AsyncMock(
            return_value=mock_downstream_response(500, {"detail": "Internal error"})
        )

        token = make_token()
        response = await ac.get("/users/42", headers={
            "Authorization": f"Bearer {token}"
        })

        assert response.status_code == 500


# =============================================================================
# Unknown routes
# =============================================================================

class TestUnknownRoutes:

    @pytest.mark.asyncio
    async def test_unknown_path_returns_404(self, client):
        """A path with no registered service prefix → 404."""
        ac, _, _ = client
        token = make_token()
        response = await ac.get("/this-does-not-exist", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 404