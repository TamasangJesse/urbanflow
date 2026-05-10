import sys
import os

# Tell Python where to find the app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override environment variables for testing.
# Docker is not running during tests so container names like
# "user-service" and "redis" don't resolve. We set dummy values here.
# All external connections (Redis, downstream services) are mocked
# anyway so these values are never actually used.
os.environ["SECRET_KEY"]                = "test_secret_key"
os.environ["ALGORITHM"]                 = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REDIS_URL"]                 = "redis://localhost:6379"
os.environ["USER_SERVICE_URL"]          = "http://user-service:8001"
os.environ["TRAFFIC_SERVICE_URL"]       = "http://traffic-intelligence-service:8002"
os.environ["NOTIFICATION_SERVICE_URL"]  = "http://notification-service:8003"
os.environ["INCIDENT_SERVICE_URL"]      = "http://incident-report-service:8004"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from jose import jwt
from datetime import datetime, timedelta, timezone


# =============================================================================
# Token helpers
# =============================================================================

def make_token(
    sub: str = "user-123",
    secret: str = "test_secret_key",
    algorithm: str = "HS256",
    expire_minutes: int = 30,
) -> str:
   
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, secret, algorithm=algorithm)


def make_expired_token(
    sub: str = "user-123",
    secret: str = "test_secret_key",
    algorithm: str = "HS256",
) -> str:
    
    expire = datetime.now(timezone.utc) - timedelta(minutes=5)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, secret, algorithm=algorithm)


# =============================================================================
# Redis mock fixture
# Shared across all test files. Simulates Redis with no real connection.
# =============================================================================

@pytest.fixture
def mock_redis():
    
    redis = AsyncMock()
    redis.exists = AsyncMock(return_value=0)   # 0 = key does not exist = not blacklisted
    redis.ping   = AsyncMock(return_value=True)
    return redis


# =============================================================================
# HTTP client fixture
# Spins up the FastAPI app with a fake Redis and a fake httpx client
# so no real network calls are made during tests.
# =============================================================================

@pytest.fixture
async def client(mock_redis):
   
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        # Inject the mock Redis into app state
        app.state.redis = mock_redis

        # Inject a mock httpx client — downstream calls go nowhere
        mock_http = AsyncMock()
        app.state.http_client = mock_http

        yield ac, mock_redis, mock_http