import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps", "backend"))

from src.shared.path_manager import DOTENV_PATH
from dotenv import load_dotenv
load_dotenv(DOTENV_PATH)

from app.api.dependencies.database import mongo_client as client

async def check_health():
    print("--- SYSTEM HEALTH CHECK ---")
    
    # 1. MongoDB
    print("Checking MongoDB...")
    try:
        await client.admin.command('ping')
        print("✅ MongoDB: Connected")
        db_name = os.getenv("DB_NAME", "smart_travel")
        db = client[db_name]
        stats = await db.command("dbStats")
        print(f"   Collections: {stats.get('collections')}")
        print(f"   Objects: {stats.get('objects')}")
    except Exception as e:
        print(f"❌ MongoDB: Connection failed - {e}")

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

    # 4. PostgreSQL
    print("\nChecking PostgreSQL...")
    from app.api.dependencies.database import engine
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL: Connected")
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed - {e}")

    # 5. Redis
    print("\nChecking Redis...")
    from app.api.dependencies.database import redis_client
    try:
        await redis_client.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")

    client.close()
    await engine.dispose()
    await redis_client.aclose()
    print("\n--- HEALTH CHECK COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(check_health())
