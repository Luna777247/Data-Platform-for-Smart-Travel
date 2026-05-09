"""
Database dependencies with proper lifecycle management.

Connection Management Patterns:
- MongoDB: Shared singleton client
  - Single client instance for entire application
  - Connection pooling handled by Motor (maxPoolSize=50)
  - Yields same client to all requests
  - Lifecycle managed by FastAPI lifespan
  - Connection timeout set to 10 seconds

CRITICAL: Do NOT create new clients per request. Reuse singletons.
This prevents connection pool exhaustion and memory leaks.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# MongoDB (shared singleton — do NOT create per request)
# ──────────────────────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(
    settings.mongodb_url,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=50,         # Max connections in pool
    minPoolSize=10,         # Min connections to maintain
)


async def get_mongo_client() -> AsyncIOMotorClient:
    """
    Get the MongoDB client singleton.
    
    PATTERN: Singleton client shared across all requests.
    Do NOT create new clients. Motor handles pooling internally.
    
    Usage in route:
    ```python
    @router.get("/places")
    async def list_places(mongo: AsyncIOMotorClient = Depends(get_mongo_client)):
        db = mongo['dataplatform_db']
        collection = db['places']
        # Use collection...
    ```
    """
    yield mongo_client


# ──────────────────────────────────────────────────────────────────────────
# Redis (shared singleton)
# ──────────────────────────────────────────────────────────────────────────
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
)


async def get_redis_client() -> redis.Redis:
    yield redis_client


# Aliases for compatibility with existing code
async def get_database():
    """
    Alias for get_mongo_client() - Get MongoDB client.
    
    Tương thích với code cũ sử dụng get_database().
    
    Returns:
        AsyncIOMotorClient: MongoDB client singleton
    """
    yield mongo_client


async def get_redis_pool():
    """
    Alias for get_redis_client() - Get Redis client.
    
    Tương thích với code cũ sử dụng get_redis_pool().
    
    Returns:
        redis.Redis: Redis client singleton
    """
    yield redis_client