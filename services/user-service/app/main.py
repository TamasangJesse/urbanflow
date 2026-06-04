from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables in PostgreSQL when the service starts
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup on shutdown
    await engine.dispose()


app = FastAPI(
    title="UrbanFlow — User Service",
    description="Manages user identity, authentication, saved routes, and GPS location.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register route groups
app.include_router(auth_router)
app.include_router(user_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """GET /health — used by Kubernetes liveness probes."""
    return {"status": "ok", "service": "user-service"}