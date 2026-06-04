
import os
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# ── MongoDB ───────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB  = os.getenv("MONGO_DB", "urbanflow")

mongo_client         = AsyncIOMotorClient(MONGO_URI)
db                   = mongo_client[MONGO_DB]
incidents_collection = db["incidents"]

# ── Redis ─────────────────────────────────────────────────────────
REDIS_HOST     = os.getenv("REDIS_HOST", "redis")
REDIS_PORT     = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)







'''import os
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# ── MongoDB ───────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB  = os.getenv("MONGO_DB", "urbanflow")

mongo_client         = AsyncIOMotorClient(MONGO_URI)
db                   = mongo_client[MONGO_DB]
incidents_collection = db["incidents"]

# ── Redis ─────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = aioredis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)'''