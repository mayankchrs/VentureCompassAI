from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from datetime import datetime, timedelta
import hashlib
import json
from typing import Optional, Any

client: AsyncIOMotorClient = None
database = None

async def init_db():
    global client, database
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client[settings.DB_NAME]
    
    await create_indexes()

async def create_indexes():
    await database.companies.create_index([("name", "text"), ("aliases", 1)])
    await database.sources.create_index("run_id")
    await database.patents.create_index([("run_id", 1), ("assignee", 1), ("filing_date", -1)])
    await database.runs.create_index([("company_id", 1), ("started_at", -1)])
    
    # Cache indexes
    await database.cache.create_index("cache_key", unique=True)
    await database.cache.create_index("expires_at", expireAfterSeconds=0)  # TTL index

def get_database():
    return database

# Cache management functions
def generate_cache_key(operation: str, params: dict) -> str:
    """Generate a consistent cache key from operation and parameters."""
    cache_data = {"operation": operation, "params": sorted(params.items())}
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()

async def get_from_cache(cache_key: str) -> Optional[Any]:
    """Retrieve data from cache if not expired."""
    cache_doc = await database.cache.find_one({"cache_key": cache_key})
    if cache_doc and cache_doc["expires_at"] > datetime.utcnow():
        return cache_doc["data"]
    return None

async def set_cache(cache_key: str, data: Any, ttl_hours: int = 24) -> None:
    """Store data in cache with TTL."""
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    await database.cache.replace_one(
        {"cache_key": cache_key},
        {
            "cache_key": cache_key,
            "data": data,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        },
        upsert=True
    )