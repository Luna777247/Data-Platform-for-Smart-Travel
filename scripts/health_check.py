import asyncio
import os
from app.db.client import MongoClient

async def check_health():
    print("--- SYSTEM HEALTH CHECK ---")
    
    # 1. MongoDB
    print("Checking MongoDB...")
    await MongoClient.connect()
    if MongoClient.is_connected:
        print("✅ MongoDB: Connected")
        db = MongoClient.get_db()
        stats = await db.command("dbStats")
        print(f"   Collections: {stats.get('collections')}")
        print(f"   Objects: {stats.get('objects')}")
    else:
        print("❌ MongoDB: Disconnected")

    # 2. Storage
    print("\nChecking Local Storage...")
    paths = [
        "storage/bronze",
        "storage/silver/pois_osm",
        "storage/silver/pois_google",
        "storage/silver/pois_cleaned"
    ]
    for p in paths:
        exists = os.path.exists(p)
        print(f"   {p}: {'✅' if exists else '❌'}")

    # 3. MinIO (Optional check)
    print("\nChecking MinIO...")
    from src.ingestion.bronze_writer import BronzeWriter
    writer = BronzeWriter()
    if writer.minio_active:
        print("✅ MinIO: Active")
    else:
        print("⚠️ MinIO: Offline (Local Fallback Active)")

    await MongoClient.disconnect()
    print("\n--- HEALTH CHECK COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(check_health())
