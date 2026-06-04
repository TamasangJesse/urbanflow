import asyncio
import logging

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.core.redis_client import close_redis
from app.workers.stream_consumer import consume_incident_stream

# ------------------------------------------------------------------ #
# Logging
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# FastAPI application
# ------------------------------------------------------------------ #
app = FastAPI(
    title="UrbanFlow — Notification Service",
    description=(
        "Listens for incident events from Redis Streams and pushes alerts "
        "to users within 5 km of the incident (geofencing via Haversine formula)."
    ),
    version="1.0.0",
)

app.include_router(router)


# ------------------------------------------------------------------ #
# Startup — launch the background stream consumer
# ------------------------------------------------------------------ #
@app.on_event("startup")
async def startup_event() -> None:
    """
    Start the Redis Streams consumer as an asyncio background task.

    This is what keeps consume_incident_stream() running continuously
    while the HTTP endpoints remain available on the same event loop.
    Without this, event consumption would never start.
    """
    logger.info(
        "Notification Service starting on port %d", settings.service_port
    )
    asyncio.create_task(consume_incident_stream())
    logger.info("Stream consumer background task launched")


# ------------------------------------------------------------------ #
# Shutdown — close Redis connection cleanly
# ------------------------------------------------------------------ #
@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Notification Service shutting down — closing Redis connection")
    await close_redis()