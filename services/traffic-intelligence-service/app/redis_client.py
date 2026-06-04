"""
redis_client.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Shared Redis connection.
Every module that needs Redis imports redis_client from here.
Nobody creates their own Redis connection directly.

Reads REDIS_URL from .env. Falls back to the urbanflow_redis
container hostname if not set.

Environment variable (set in .env):
    REDIS_URL=redis://:urbanflow_redis_pass_2026@urbanflow_redis:6379/0
"""

import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://urbanflow_redis:6379/0"   # fallback — no auth, plain Docker network
)

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,   # all keys and values come back as str, not bytes
)