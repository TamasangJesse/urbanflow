from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import incidents_collection
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await incidents_collection.create_index([("location", "2dsphere")])
    print("[MongoDB] 2dsphere index ready on incidents.location")
    yield


app = FastAPI(
    title="UrbanFlow — Incident Report Service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)




