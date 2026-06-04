"""
main.py — UrbanFlow API Gateway

Single entry point for all client requests. Responsibilities:
  1. Rate limiting     — 100 requests/minute per IP via slowapi
  2. Token validation  — decode JWT locally + check Redis blacklist
  3. Request routing   — forward to the correct downstream service

This service has no database and no business logic.
It routes, validates, and protects — nothing else.
"""

import redis.asyncio as aioredis
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.auth import validate_token
from app.core.proxy import route_request
from app.core.middleware import register_middleware
from fastapi import WebSocket
from app.core.proxy import route_request, forward_websocket


# =============================================================================
# Rate Limiter — slowapi
# Keyed on the client's remote IP address.
# Threshold: 100 requests per minute per IP (generous for users, strict for bots).
# =============================================================================
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


# =============================================================================
# Public routes — these paths bypass JWT validation.
# Format: frozenset of (METHOD, path_prefix) tuples.
# Prefix matching is used so /auth/register covers any deeper path under /auth.
#
# Public:
#   POST /auth/register — user has no token yet, they are creating an account
#   POST /auth/login    — user has no token yet, they are obtaining one
#   GET  /health        — Kubernetes liveness probe, no auth needed
# =============================================================================
PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset({
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("GET",  "/health"),
})


def _is_public(method: str, path: str) -> bool:
    """
    Return True if this request should bypass JWT validation.
    Matches on exact method + path prefix to cover trailing slashes
    and query strings without false positives.
    """
    for public_method, public_prefix in PUBLIC_ROUTES:
        if method == public_method and path.startswith(public_prefix):
            return True
    return False


# =============================================================================
# Lifespan — startup and shutdown for shared resources.
# Both Redis and the httpx client are expensive to create per-request.
# They are initialised once on startup and stored on app.state so every
# request handler can reuse them without re-connecting.
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    app.state.redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),  # 30s total; plenty for any downstream call
    )

    yield  # Application runs here

    # --- Shutdown ---
    await app.state.redis.aclose()
    await app.state.http_client.aclose()


# =============================================================================
# Application
# =============================================================================
app = FastAPI(
    title="UrbanFlow API Gateway",
    description="Single entry point for all UrbanFlow client requests. "
                "Handles routing, JWT validation, and rate limiting.",
    version="1.0.0",
    lifespan=lifespan,
    # Disable automatic /docs and /redoc in production — the gateway
    # is infrastructure, not a documented API. Toggle on for debugging.
    docs_url="/docs",
    redoc_url=None,
)

# FIX 1: register_middleware now called AFTER app is created (was erroneously
# called on line 29 before app existed, causing a NameError on startup).
register_middleware(app)

# FIX 2: app.state.limiter assigned only once (was duplicated — harmless but messy).
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================================================================
# Health check endpoint
# GET /health — returns 200 OK.
# Used by Kubernetes liveness probes to confirm the gateway is alive.
# This route is explicitly public (no JWT required).
# =============================================================================
@app.get("/health", tags=["Infrastructure"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Liveness probe endpoint. Kubernetes calls this on a schedule.
    Returns 200 as long as the process is responsive.
    Also verifies the Redis connection is alive.
    """
    try:
        await request.app.state.redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unreachable"

    return {
        "status": "ok",
        "service": "api-gateway",
        "redis": redis_status,
    }


# =============================================================================
# Gateway catch-all route
# Handles every other path by:
#   1. Checking rate limit (enforced by slowapi decorator)
#   2. Validating JWT for non-public routes
#   3. Forwarding the request to the correct downstream service
# =============================================================================
@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Gateway"],
    include_in_schema=False,  # Catch-all — no point documenting a wildcard
)

@limiter.limit("100/minute")
async def gateway(request: Request, path: str):
    """
    route_request() — Inspect the URL path and forward the request to the
    correct downstream service port.

    validate_token() — Check the JWT token in the Authorization header
    before allowing the request through (skipped for public routes).

    rate_limit() — Enforced via the @limiter.limit decorator above.
    100 requests per minute per IP. Exceeding this returns HTTP 429.
    """
    full_path = f"/{path}"

    # ----------------------------------------------------------------
    # validate_token() — skip for public routes (register, login, health)
    # ----------------------------------------------------------------
    if not _is_public(request.method, full_path):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing or malformed. "
                       "Expected format: 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ").strip()

        # Decode locally (python-jose) + check Redis blacklist.
        # Both operations happen in auth.validate_token().
        payload = await validate_token(token, request.app.state.redis)
        request.state.user_id = payload.get("sub")

    # ----------------------------------------------------------------
    # route_request() — resolve service and forward.
    # ----------------------------------------------------------------
    return await route_request(request, request.app.state.http_client)



@app.websocket("/ws/{user_id}")
async def websocket_gateway(websocket: WebSocket, user_id: str):
    """
    WebSocket gateway — forwards /ws/{user_id} to the notification service.
    Validates JWT token passed as a query parameter since WebSocket
    connections cannot send Authorization headers.
    """
    # JWT comes as query param: ws://host/ws/{user_id}?token=xxx
    token = websocket.query_params.get("token", "")

    if not token:
        await websocket.close(code=1008)  # 1008 = Policy Violation
        return

    try:
        await validate_token(token, websocket.app.state.redis)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await forward_websocket(f"/ws/{user_id}", token, websocket)


