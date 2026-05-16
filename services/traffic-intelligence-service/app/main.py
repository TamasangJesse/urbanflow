"""
main.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
App instance and lifespan only. Nothing else lives here.

  routes.py  — all HTTP endpoints
  state.py   — shared in-memory model cache and incident boosts
  consumer.py — Redis stream background worker
  database.py — PostgreSQL connection pool
  ml_model.py — ML pipeline functions

Startup flow:
  1. init_db()                    — initialise PostgreSQL connection pool
  2. train_model() + load_model() — train and cache the ML model
  3. consume_incident_stream()    — start Redis stream background worker

Shutdown flow:
  1. cancel consumer task
  2. close_db()
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db, close_db
from app.consumer import consume_incident_stream
from app.ml_model import train_model, load_model
from app.routes   import router
import app.state  as state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LIFESPAN — startup and shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Starting Traffic Intelligence Service ...")

    logger.info("Initialising database connection pool ...")
    init_db()
    logger.info("Database pool ready.")

    logger.info("Training model from PostgreSQL data ...")
    try:
        state._training_summary = train_model()
        state._model_bundle     = load_model()
        logger.info(
            "Model ready. Records used: %d | Test accuracy: %.2f%%",
            state._training_summary["records_used"],
            state._training_summary["test_accuracy"] * 100,
        )
    except Exception as e:
        logger.error("Model training failed at startup: %s", str(e))
        logger.warning("Service running but /predict unavailable until retrain.")

    logger.info("Starting incident stream consumer ...")
    consumer_task = asyncio.create_task(
        consume_incident_stream(state.active_incident_boosts)
    )
    logger.info("Incident stream consumer started.")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    consumer_task.cancel()
    logger.info("Shutting down — closing database connections ...")
    close_db()
    logger.info("Traffic Intelligence Service stopped.")


# ---------------------------------------------------------------------------
# APP INSTANCE
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UrbanFlow — Traffic Intelligence Service",
    description=(
        "Predicts road congestion levels across Yaoundé using a "
        "RandomForestClassifier trained on historical traffic patterns."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)