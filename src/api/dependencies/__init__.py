"""
API Dependencies Package
========================
FastAPI dependencies cho dependency injection

Dependencies:
- auth: Authentication và authorization (JWT, API keys)
- database: Database connection injectors
- monitoring: Monitoring setup injectors

Usage:
    from src.api.dependencies import get_current_user, get_database
    
    @router.get("/items")
    async def get_items(
        db: AsyncIOMotorDatabase = Depends(get_database),
        user: User = Depends(get_current_user)
    ):
        pass
"""

from .auth import (
    get_current_user,
    get_current_admin_user,
    get_current_user_optional,
    create_access_token,
    verify_password,
    get_password_hash,
    User,
)
from .database import get_database, get_redis_pool

__all__ = [
    # Auth
    "get_current_user",
    "get_current_admin_user",
    "get_current_user_optional",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "User",
    # Database
    "get_database",
    "get_redis_pool",
]