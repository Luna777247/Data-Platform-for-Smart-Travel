# backend/app/db/client.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smart_travel")

class MongoClient:
    client: AsyncIOMotorClient | None = None
    db = None
    is_connected = False

    @classmethod
    async def connect(cls):
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Create client inside the running event loop to avoid "Event loop is closed"
            if cls.client is None:
                cls.client = AsyncIOMotorClient(MONGODB_URI)
                cls.db = cls.client[DB_NAME]
            # Ping to verify connection
            await cls.db.command("ping")
            cls.is_connected = True
            logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
        except Exception as e:
            cls.is_connected = False
            logger.error(f"❌ MongoDB Connection Failed: {e}", exc_info=True)


    @classmethod
    async def disconnect(cls):
        import logging
        logger = logging.getLogger(__name__)
        try:
            if cls.client:
                cls.client.close()
                cls.client = None
                cls.db = None
                cls.is_connected = False
                logger.info("✅ Disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error during MongoDB disconnect: {e}", exc_info=True)

    @classmethod
    def get_db(cls):
        return cls.db


# Module-level convenience functions for easier imports
def get_database():
    """
    Get MongoDB database instance.

    Hàm tiện ích để lấy database instance từ MongoClient.
    Được sử dụng trong dependencies và repositories.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance

    Example:
        >>> db = get_database()
        >>> await db.pois.find_one({"_id": "123"})
    """
    return MongoClient.get_db()


# Redis client placeholder (to be implemented with actual Redis client)
_redis_pool = None


def get_redis_pool():
    """
    Get Redis connection pool.

    Hàm tiện ích để lấy Redis connection pool.
    Hiện tại trả về None (placeholder cho future implementation).

    Returns:
        Optional[Redis]: Redis client instance hoặc None

    Example:
        >>> redis = get_redis_pool()
        >>> if redis:
        ...     await redis.set("key", "value")
    """
    global _redis_pool
    return _redis_pool
