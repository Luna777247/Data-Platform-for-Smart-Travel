import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/test_db", echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
async def redis_client():
    client = redis.Redis(host="localhost", port=6379, db=1)
    yield client
    await client.flushdb()


@pytest.fixture
async def mongo_client():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    # Clean up test database
    await client.drop_database("test_db")