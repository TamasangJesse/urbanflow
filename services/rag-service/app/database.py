import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "urbanflow_rag")

client: AsyncIOMotorClient = None
database = None


async def connect_db():
    global client, database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]


async def close_db():
    global client
    if client:
        client.close()


def get_database():
    return database