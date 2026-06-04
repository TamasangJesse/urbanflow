"""
auth.py — Token validation for the API Gateway.

Strategy (as designed):
  1. Decode the JWT locally using the shared SECRET_KEY (python-jose).
     This validates signature and expiry with zero network hops.
  2. Check the Redis token blacklist. Tokens are added to the blacklist
     by the User Service when a user calls POST /auth/logout.

Two fast in-process operations. No call to the User Service per request.
"""

import redis.asyncio as aioredis
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import settings


async def validate_token(token: str, redis_client: aioredis.Redis) -> dict:
    """
    Validate a Bearer token before the gateway forwards the request.

    Args:
        token:        Raw JWT string extracted from the Authorization header.
        redis_client: Async Redis client stored on app.state at startup.

    Returns:
        The decoded JWT payload dict (contains sub, exp, etc.).

    Raises:
        HTTPException 401 if the token is invalid, expired, or blacklisted.
    """
    # ------------------------------------------------------------------
    # Step 1 — Decode and verify the JWT signature + expiry locally.
    # python-jose raises JWTError for any failure: bad signature, expired,
    # malformed. We catch all of them and return a single 401 to the client
    # — never leak which specific check failed.
    # ------------------------------------------------------------------
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ------------------------------------------------------------------
    # Step 2 — Check the Redis blacklist.
    # The User Service writes blacklist:{token} to Redis on logout.
    # If the key exists, the token was explicitly revoked — reject it
    # even though the signature is still mathematically valid.
    # ------------------------------------------------------------------
    blacklist_key = f"blacklist:{token}"
    is_blacklisted = await redis_client.exists(blacklist_key)

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload