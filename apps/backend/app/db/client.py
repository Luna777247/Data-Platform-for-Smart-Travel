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
        try:
            # Create client inside the running event loop to avoid "Event loop is closed"
            if cls.client is None:
                cls.client = AsyncIOMotorClient(MONGODB_URI)
                cls.db = cls.client[DB_NAME]
            # Ping to verify connection
            await cls.db.command("ping")
            cls.is_connected = True
            print(f"Connected to MongoDB: {DB_NAME}")
        except Exception as e:
            cls.is_connected = False
            print(f"MongoDB Connection Failed: {e}")


    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            cls.is_connected = False
            print("Disconnected from MongoDB")

    @classmethod
    def get_db(cls):
        return cls.db
