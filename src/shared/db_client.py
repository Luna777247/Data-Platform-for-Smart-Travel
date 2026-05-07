from motor.motor_asyncio import AsyncIOMotorClient
from functools import lru_cache


@lru_cache()
def get_mongo_client(connection_string: str = "mongodb://localhost:27017") -> AsyncIOMotorClient:
    return AsyncIOMotorClient(connection_string)
