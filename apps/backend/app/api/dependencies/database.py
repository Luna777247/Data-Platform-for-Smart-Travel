"""
Fix #3 & #4: Database dependencies — unified connection management.
- PostgreSQL: SQLAlchemy async engine
- MongoDB: Shared singleton motor client
- Redis: Shared singleton async client
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# PostgreSQL (async engine — singleton)
# ──────────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.postgres_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# ──────────────────────────────────────────────────────────────────────────
# MongoDB (shared singleton — Fix #3: KHÔNG tạo mới mỗi request)
# ──────────────────────────────────────────────────────────────────────────
mongo_client = AsyncIOMotorClient(
    settings.mongodb_url,
    serverSelectionTimeoutMS=5000,
    maxPoolSize=50,
)


async def get_mongo_client() -> AsyncIOMotorClient:
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