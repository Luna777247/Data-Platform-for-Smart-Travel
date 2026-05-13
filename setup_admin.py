import asyncio
from src.services.auth_service import AuthService
from src.core.database import mongodb_manager

async def setup_admin():
    # Connect
    await mongodb_manager.connect()
    auth_service = AuthService()
    
    # Try to register admin
    try:
        user = await auth_service.register_user("admin", "admin123", email="admin@smarttravel.vn")
        print(f"Admin user created: {user.get('username')}")
    except Exception as e:
        print(f"Failed to create admin (it might already exist): {e}")
    
    await mongodb_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_admin())
