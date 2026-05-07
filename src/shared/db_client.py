"""
Shared MongoDB client singleton.

Used by both FastAPI backend and Airflow DAGs.
- Each process creates its own singleton instance
- Connection pooling configured for concurrent access
- Proper error handling for connection failures
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB connection configuration
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    os.getenv("MONGODB_URI", "mongodb://localhost:27017")
)

# Module-level singleton - created on first import
_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Get the MongoDB client singleton.
    
    Creates the client on first call, reuses it on subsequent calls.
    Each process (FastAPI, Airflow, tests, scripts) gets its own singleton instance.
    
    Returns:
        AsyncIOMotorClient connected to MongoDB
        
    Raises:
        ConnectionError: If unable to establish connection
    """
    global _mongo_client
    
    if _mongo_client is None:
        try:
            _mongo_client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
                socket_keepalive=True,
            )
            logger.info(f"✅ MongoDB client initialized to {MONGODB_URL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB client: {e}")
            raise
    
    return _mongo_client


def close_mongo_client() -> None:
    """
    Close the MongoDB client connection (for testing/shutdown).
    
    Safe to call even if client was never initialized.
    """
    global _mongo_client
    
    if _mongo_client is not None:
        try:
            _mongo_client.close()
            logger.info("✅ MongoDB client closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB client: {e}")
        finally:
            _mongo_client = None

