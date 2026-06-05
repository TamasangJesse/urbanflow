import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["SECRET_KEY"]                  = "test_secret_key"
os.environ["ALGORITHM"]                   = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REDIS_URL"]                   = "redis://localhost:6379"
os.environ["USER_SERVICE_URL"]            = "http://user-service:8001"
os.environ["TRAFFIC_SERVICE_URL"]         = "http://traffic-intelligence-service:8002"
os.environ["NOTIFICATION_SERVICE_URL"]    = "http://notification-service:8003"
os.environ["INCIDENT_SERVICE_URL"]        = "http://incident-report-service:8004"
os.environ["RAG_SERVICE_URL"]             = "http://rag-service:8005"

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from jose import jwt
from datetime import datetime, timedelta, timezone


def make_token(sub="user-123", secret="test_secret_key", algorithm="HS256", expire_minutes=30):
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode({"sub": sub, "exp": expire}, secret, algorithm=algorithm)


def make_expired_token(sub="user-123", secret="test_secret_key", algorithm="HS256"):
    expire = datetime.now(timezone.utc) - timedelta(minutes=5)
    return jwt.encode({"sub": sub, "exp": expire}, secret, algorithm=algorithm)


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.exists = AsyncMock(return_value=0)
    redis.ping   = AsyncMock(return_value=True)
    return redis


@pytest.fixture
async def client(mock_redis):
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        app.state.redis = mock_redis
        mock_http = AsyncMock()
        app.state.http_client = mock_http
        yield ac, mock_redis, mock_http