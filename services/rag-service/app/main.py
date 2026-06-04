import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_db, connect_db
from app.routes import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="UrbanFlow RAG Service", version="1.0.0", lifespan=lifespan)

app.include_router(router)