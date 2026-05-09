"""
Test Configuration - pytest Fixtures và Utilities
================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - tests/ section

Mục đích:
- Cung cấp fixtures dùng chung cho tất cả tests
- Setup test database connections (test isolation)
- Mock external services (OSM API, etc.)
- Create test data factories

Fixtures:
- event_loop: Async event loop cho async tests
- client: TestClient cho FastAPI app
- mongo_client: MongoDB test connection
- redis_client: Redis test connection
- mock_osm_data: Sample OSM response data

Usage:
    def test_something(client, mongo_client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
"""

# Import pytest để định nghĩa fixtures
import pytest

# Import asyncio cho async tests
import asyncio

# Import MongoDB async client
from motor.motor_asyncio import AsyncIOMotorClient

# Import Redis async client
import redis.asyncio as redis

# Import FastAPI TestClient
from fastapi.testclient import TestClient

# Import main app
from src.main import app

# Import settings
from src.core.config import settings


# ============================================
# ASYNC CONFIGURATION
# ============================================

# Fixture cho async event loop
# Cho phép các test async chạy đúng cách
@pytest.fixture(scope="session")
def event_loop():
    """
    Tạo event loop cho async tests
    
    Scope: session - Dùng chung cho cả test session
    """
    # Tạo new event loop
    loop = asyncio.get_event_loop_policy().new_event_loop()
    
    # Yield cho tests sử dụng
    yield loop
    
    # Cleanup sau khi tests hoàn thành
    loop.close()


# ============================================
# FASTAPI CLIENT
# ============================================

@pytest.fixture(scope="module")
def client():
    """
    FastAPI TestClient fixture
    
    Cung cấp HTTP client để test API endpoints
    Không cần chạy server thật
    
    Usage:
        def test_endpoint(client):
            response = client.get("/health")
            assert response.status_code == 200
    """
    # Tạo test client
    with TestClient(app) as test_client:
        yield test_client


# ============================================
# DATABASE FIXTURES
# ============================================

@pytest.fixture(scope="function")
async def mongo_client():
    """
    MongoDB test client fixture
    
    Kết nối đến test database và cleanup sau mỗi test
    
    Returns:
        AsyncIOMotorClient: MongoDB async client
    """
    # Tạo connection đến MongoDB test instance
    # Sử dụng test database riêng để không ảnh hưởng development data
    test_uri = settings.mongodb_uri.replace(
        settings.mongodb_db_name,
        f"{settings.mongodb_db_name}_test"
    )
    
    client = AsyncIOMotorClient(
        test_uri,
        serverSelectionTimeoutMS=5000  # 5 second timeout cho tests
    )
    
    # Verify connection
    await client.admin.command('ping')
    
    yield client
    
    # Cleanup: Drop test database sau mỗi test
    await client.drop_database(f"{settings.mongodb_db_name}_test")
    
    # Close connection
    client.close()


@pytest.fixture(scope="function")
async def redis_client():
    """
    Redis test client fixture
    
    Kết nối đến Redis test database (db=15 - reserved for tests)
    
    Returns:
        redis.Redis: Redis async client
    """
    # Sử dụng database 15 cho tests (Redis có 16 db: 0-15)
    test_redis_url = settings.redis_url.replace(
        f"/{settings.redis_db}",
        "/15"
    )
    
    client = redis.from_url(
        test_redis_url,
        decode_responses=True
    )
    
    # Verify connection
    await client.ping()
    
    yield client
    
    # Cleanup: Flush test database
    await client.flushdb()
    
    # Close connection
    await client.close()


# ============================================
# TEST DATA FACTORIES
# ============================================

@pytest.fixture
def mock_osm_data():
    """
    Sample OSM API response data
    
    Dùng để mock OSM Overpass API responses
    
    Returns:
        dict: Sample OSM elements
    """
    return {
        "version": 0.6,
        "generator": "Overpass API",
        "elements": [
            {
                "type": "node",
                "id": 123456789,
                "lat": 35.6762,
                "lon": 139.6503,
                "tags": {
                    "name": "Tokyo Tower",
                    "name:en": "Tokyo Tower",
                    "name:ja": "東京タワー",
                    "tourism": "attraction",
                    "amenity": "restaurant"
                }
            },
            {
                "type": "node",
                "id": 987654321,
                "lat": 35.6586,
                "lon": 139.7454,
                "tags": {
                    "name": "Sensō-ji",
                    "name:en": "Sensoji Temple",
                    "name:ja": "浅草寺",
                    "tourism": "attraction",
                    "religion": "buddhist"
                }
            }
        ]
    }


@pytest.fixture
def mock_bronze_record():
    """
    Sample Bronze layer record
    
    Returns:
        dict: BronzeRecord data
    """
    from datetime import datetime, timezone
    
    return {
        "record_id": "osm_tokyo_attraction_123456789",
        "source": "osm",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "raw_data": {
            "type": "node",
            "id": 123456789,
            "lat": 35.6762,
            "lon": 139.6503,
            "tags": {
                "name": "Tokyo Tower",
                "tourism": "attraction"
            }
        },
        "ingestion_metadata": {
            "city": "tokyo",
            "category": "attraction",
            "osm_id": "123456789"
        }
    }


@pytest.fixture
def mock_silver_place():
    """
    Sample Silver layer place
    
    Returns:
        dict: SilverPlace data
    """
    from datetime import datetime, timezone
    
    return {
        "u_key": "osm_tokyo_attraction_123456789",
        "source_id": "123456789",
        "name": "Tokyo Tower",
        "name_en": "Tokyo Tower",
        "category": "tourist_attraction",
        "subcategory": "landmark",
        "city": "tokyo",
        "country": "JP",
        "location": {"lat": 35.6762, "lon": 139.6503},
        "tags": {
            "tourism": "attraction",
            "name:ja": "東京タワー"
        },
        "source": "osm",
        "language": "en",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "status": "processed"
    }


# ============================================
# UTILITY FIXTURES
# ============================================

@pytest.fixture
def auth_headers():
    """
    JWT token headers cho authenticated requests
    
    Returns:
        dict: Headers với Bearer token
    """
    # Tạo test JWT token
    from src.api.dependencies.auth import create_access_token
    
    token = create_access_token(
        username="test_user",
        expires_delta=None
    )
    
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture(scope="function")
def temp_directory(tmp_path):
    """
    Temporary directory cho file operations trong tests
    
    Args:
        tmp_path: pytest built-in fixture
        
    Returns:
        Path: Temporary directory path
    """
    return tmp_path


# ============================================
# CONFIGURATION OVERRIDES
# ============================================

@pytest.fixture(autouse=True)
def override_settings():
    """
    Override settings cho test environment
    
    autouse=True: Tự động chạy cho tất cả tests
    """
    # Lưu original values
    original_env = settings.environment
    original_log_level = settings.log_level
    
    # Override với test values
    settings.environment = "test"
    settings.log_level = "DEBUG"
    
    yield
    
    # Restore original values
    settings.environment = original_env
    settings.log_level = original_log_level


# ============================================
# MODULE EXPORTS
# ============================================

# Không cần exports cho pytest fixtures
# Fixtures tự động available trong test files
