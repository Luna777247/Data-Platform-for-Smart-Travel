import pytest
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def mongo_client():
    """MongoDB client for testing"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    # Clean up test databases
    # client.drop_database("test_smart_travel")


@pytest.fixture(scope="session")
async def redis_client():
    """Redis client for testing"""
    client = redis.Redis(host="localhost", port=6379, db=1)
    yield client
    await client.flushdb()


@pytest.fixture(scope="session")
async def db_session():
    """PostgreSQL session for testing"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/test_db", echo=False
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture
def sample_osm_data():
    """Sample OSM API response"""
    return {
        "elements": [
            {
                "id": 12345,
                "tags": {
                    "name": "Ho Chi Minh Mausoleum",
                    "tourism": "attraction",
                    "addr:street": "Hung Vuong",
                },
                "center": {"lat": 21.0368, "lon": 105.8347},
            }
        ]
    }


@pytest.fixture
def sample_google_data():
    """Sample Google Places API response"""
    return {
        "results": [
            {
                "place_id": "ChIJ1234567890",
                "name": "Temple of Literature",
                "formatted_address": "58 P. Quốc Tử Giám, Văn Miếu, Đống Đa, Hà Nội",
                "rating": 4.5,
                "user_ratings_total": 1200,
                "geometry": {"location": {"lat": 21.0285, "lng": 105.8357}},
                "types": ["tourist_attraction", "point_of_interest"],
            }
        ]
    }
