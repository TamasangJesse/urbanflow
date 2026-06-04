"""
database.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Single shared PostgreSQL connection pool.
Every other module imports get_connection() and release_connection() from here.
Nobody opens their own psycopg2 connection directly.

Environment variable required (set in .env):
    DATABASE_URL=postgresql://urbanflow:yourpassword@db:5432/urbanflow_traffic

The host 'db' must match the PostgreSQL service name in docker-compose.yml exactly.
"""

import os
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Add it to your .env file: "
        "postgresql://urbanflow:yourpassword@db:5432/urbanflow_traffic"
    )

# minconn=1  — one connection always kept alive, low idle overhead on VPS
# maxconn=10 — enough for concurrent requests without exhausting PostgreSQL
_pool: pool.SimpleConnectionPool | None = None


def init_db() -> None:
    """
    Initialise the connection pool.
    Called once at service startup in the FastAPI lifespan handler in main.py.
    Never call this more than once.
    """
    global _pool
    if _pool is not None:
        return

    _pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=DATABASE_URL,
    )


def get_connection():
    """
    Borrow a connection from the pool.
    Always pair with release_connection() in a finally block.

    Usage:
        conn = get_connection()
        try:
            ...
        finally:
            release_connection(conn)
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Ensure init_db() is called at startup."
        )
    return _pool.getconn()


def release_connection(conn) -> None:
    """
    Return a borrowed connection back to the pool.
    Always call this in a finally block — never let connections leak.
    """
    if _pool is not None:
        _pool.putconn(conn)


def close_db() -> None:
    """
    Close all connections in the pool.
    Called at service shutdown in the FastAPI lifespan handler in main.py.
    """
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None