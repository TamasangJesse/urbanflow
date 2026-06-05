"""
test_auth.py — Unit tests for app/core/auth.py

Tests validate_token() in isolation — no HTTP layer, no FastAPI app.
Just the function itself with a mock Redis client.

Scenarios covered:
  - Valid token passes through
  - Expired token is rejected
  - Token with wrong secret is rejected
  - Malformed token string is rejected
  - Valid token that is blacklisted is rejected
  this one is quite easy to understand for real
"""

import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

from tests.conftest import make_token, make_expired_token
from app.core.auth import validate_token


# =============================================================================
# Helpers
# =============================================================================

def make_redis(blacklisted: bool = False) -> AsyncMock:
    """Return a mock Redis client. Simulates blacklist state."""
    redis = AsyncMock()
    redis.exists = AsyncMock(return_value=1 if blacklisted else 0)
    return redis


# =============================================================================
# Tests
# =============================================================================

@pytest.mark.asyncio
async def test_valid_token_passes():
    """A correctly signed, non-expired, non-blacklisted token should pass."""
    token = make_token()
    redis = make_redis(blacklisted=False)

    payload = await validate_token(token, redis)

    assert payload["sub"] == "user-123"


@pytest.mark.asyncio
async def test_expired_token_is_rejected():
    """A token past its expiry time should raise HTTP 401."""
    token = make_expired_token()
    redis = make_redis(blacklisted=False)

    with pytest.raises(HTTPException) as exc:
        await validate_token(token, redis)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_wrong_secret_is_rejected():
    """A token signed with a different secret key should raise HTTP 401."""
    token = make_token(secret="completely-wrong-secret")
    redis = make_redis(blacklisted=False)

    with pytest.raises(HTTPException) as exc:
        await validate_token(token, redis)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_malformed_token_is_rejected():
    """A random string that is not a JWT at all should raise HTTP 401."""
    redis = make_redis(blacklisted=False)

    with pytest.raises(HTTPException) as exc:
        await validate_token("this.is.not.a.jwt", redis)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_blacklisted_token_is_rejected():
    """
    A valid token that exists in the Redis blacklist should raise HTTP 401.
    This simulates a user who has logged out — their token is still
    mathematically valid but must be rejected.
    """
    token = make_token()
    redis = make_redis(blacklisted=True)  # token IS in the blacklist

    with pytest.raises(HTTPException) as exc:
        await validate_token(token, redis)

    assert exc.value.status_code == 401
    assert "revoked" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_blacklist_key_format():
    """
    Verify the gateway checks the correct Redis key: blacklist:{token}.
    If this format ever changes it will break the contract with the
    User Service which writes blacklist:{token} on logout.
    """
    token = make_token()
    redis = make_redis(blacklisted=False)

    await validate_token(token, redis)

    # Confirm Redis was queried with the exact expected key format
    redis.exists.assert_called_once_with(f"blacklist:{token}")




    trying to cause an error intentionally