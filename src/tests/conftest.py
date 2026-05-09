import pytest
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient




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