"""
Database dependencies with proper lifecycle management.

Connection Management Patterns:
- PostgreSQL: Async SQLAlchemy engine with connection pooling (10-20 connections)
  - Session per request via Depends(get_db)
  - Automatic cleanup on request end
  
- MongoDB: Shared singleton client
  - Single client instance for entire application
  - Connection pooling handled by Motor (maxPoolSize=50)
  - Yields same client to all requests
  - Lifecycle managed by FastAPI lifespan
  
- Redis: Shared singleton client
  - Single client instance for entire application
  - Connection pooling and reconnection handled by redis library
  - Yields same client to all requests
  - Lifecycle managed by FastAPI lifespan

CRITICAL: Do NOT create new clients per request. Reuse singletons.
This prevents connection pool exhaustion and memory leaks.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# PostgreSQL (async engine — singleton per app instance)
# ──────────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.postgres_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before reusing from pool
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """
    Get a new database session for this request.
    
    PATTERN: Session-per-request. SQLAlchemy manages connection pooling.
    
    Usage in route:
    ```python
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_db)):
        # Session is request-scoped
        # Automatically closed after response
    ```
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


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