import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root and backend to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)
sys.path.append(os.path.join(root, "apps", "backend"))

from app.db.client import MongoClient
from app.db.repository import PlaceRepository

async def seed():
    print("🚀 Seeding Admin Data to MongoDB...")
    await MongoClient.connect()
    if not MongoClient.is_connected:
        print("❌ MongoDB not connected. Cannot seed.")
        return

    repo = PlaceRepository()
    await repo.init_indexes()

    # 1. Seed Users
    users = [
        {
            "name": "Admin User",
            "email": "admin@smarttravel.io",
            "role": "Administrator",
            "isActive": True,
            "createdAt": (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
        },
        {
            "name": "Operator Hanoi",
            "email": "hanoi.op@smarttravel.io",
            "role": "Operator",
            "isActive": True,
            "createdAt": (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        }
    ]
    for u in users:
        await repo.upsert_user(u)
    print(f"✅ Users seeded: {len(users)}")

    # 2. Seed Roles
    roles = [
        {
            "name": "Administrator",
            "description": "Full access to all system features and management",
            "permissions": ["all", "manage_users", "manage_keys", "system_config"]
        },
        {
            "name": "Operator",
            "description": "Can manage pipelines and view all data",
            "permissions": ["read_data", "trigger_pipelines", "manage_schedules"]
        }
    ]
    # Note: Upsert role by name (repository needs a small update for roles if we want it perfect, but we'll use insert for now)
    await repo.db["roles"].delete_many({}) # Clear for clean seed
    await repo.db["roles"].insert_many(roles)
    print(f"✅ Roles seeded: {len(roles)}")

    # 3. Seed API Keys
    keys = [
        {
            "short_key": "x-rapidapi-key...a1b2",
            "label": "Master Production Key",
            "status": "Ready",
            "status_code": 200
        }
    ]
    for k in keys:
        await repo.upsert_api_key(k)
    print(f"✅ API Keys seeded: {len(keys)}")

    # 4. Seed Settings
    settings = {
        "appName": "Smart Travel Data Platform (PROD)",
        "appDescription": "Professional workspace for tourism intelligence and data operations.",
        "enableRegistration": False,
        "enableAPI": True,
        "enableAuditLog": True,
        "maxConnections": 100,
        "retentionDays": 365
    }
    await repo.update_settings(settings)
    print("✅ System Settings seeded.")

    await MongoClient.disconnect()
    print("✨ Seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed())
