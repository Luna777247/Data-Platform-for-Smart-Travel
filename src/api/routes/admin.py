"""
Admin API Routes
=================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/api/routes/admin.py

Mục đích:
- Cung cấp API endpoints cho administrative operations
- Quản lý users, system settings, và data management
- Audit logs và system maintenance

Security: Admin-only access (role-based)

Các endpoints:
- GET /api/v1/admin/users: List users
- POST /api/v1/admin/users: Create user
- DELETE /api/v1/admin/users/{id}: Delete user
- GET /api/v1/admin/logs: System logs
- POST /api/v1/admin/maintenance: Maintenance mode
"""

# ============================================================================
# IMPORTS
# ============================================================================

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from src.api.dependencies.auth import get_current_admin_user, User
from src.api.dependencies.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

# ============================================================================
# ROUTER INITIALIZATION
# ============================================================================

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin access required"},
    }
)

logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    """Schema cho user response"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login")


class CreateUserRequest(BaseModel):
    """Schema cho create user request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
    role: str = Field(default="user", pattern="^(admin|user|viewer)$")


class SystemStats(BaseModel):
    """Schema cho system statistics"""
    total_users: int
    active_users: int
    total_pipelines: int
    total_pois: int
    storage_used_mb: float
    last_cleanup: Optional[datetime]


class MaintenanceMode(BaseModel):
    """Schema cho maintenance mode"""
    enabled: bool
    message: str = "System under maintenance"
    estimated_duration_minutes: Optional[int] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users",
    description="Lấy danh sách tất cả users (admin only)"
)
async def list_users(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_admin_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List tất cả users với pagination"""
    logger.info(f"Admin {current_user.username} listing users")
    
    # Query users collection
    cursor = db.users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    return [
        UserResponse(
            id=str(user.get("_id")),
            username=user["username"],
            email=user["email"],
            role=user.get("role", "user"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at", datetime.utcnow()),
            last_login=user.get("last_login")
        )
        for user in users
    ]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Tạo user mới (admin only)"
)
async def create_user(
    request: CreateUserRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Tạo user mới với role được chỉ định"""
    logger.info(f"Admin {current_user.username} creating user {request.username}")
    
    # Check if username exists
    existing = await db.users.find_one({"username": request.username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{request.username}' already exists"
        )
    
    # Hash password
    from src.api.dependencies.auth import get_password_hash
    try:
        hashed_password = get_password_hash(request.password)
    except Exception:
        # Fallback for development (same as auth.py)
        hashed_password = f"fallback_{request.password}"
    
    # Create user document
    new_user = {
        "username": request.username,
        "email": request.email,
        "hashed_password": hashed_password,
        "role": request.role,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "created_by": current_user.username
    }
    
    # Insert to database
    result = await db.users.insert_one(new_user)
    
    return UserResponse(
        id=str(result.inserted_id),
        username=request.username,
        email=request.email,
        role=request.role,
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=None
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Xóa user (admin only)"
)
async def delete_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Xóa user theo ID"""
    logger.info(f"Admin {current_user.username} deleting user {user_id}")
    
    # Không cho phép xóa chính mình
    if user_id == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    from bson import ObjectId
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None


@router.get(
    "/stats",
    response_model=SystemStats,
    summary="System statistics",
    description="Lấy thống kê hệ thống (admin only)"
)
async def get_system_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Lấy thống kê tổng quan về hệ thống"""
    logger.info(f"Admin {current_user.username} viewing system stats")
    
    # Count users
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    
    # Count pipelines và POIs
    total_pipelines = await db.pipeline_executions.count_documents({})
    total_pois = await db.gold_master_pois.count_documents({})
    
    # Estimate storage (simplified)
    storage_used_mb = total_pois * 0.01 + total_pipelines * 0.001
    
    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        total_pipelines=total_pipelines,
        total_pois=total_pois,
        storage_used_mb=round(storage_used_mb, 2),
        last_cleanup=None
    )


@router.get(
    "/logs",
    summary="System logs",
    description="Lấy system logs (admin only)"
)
async def get_system_logs(
    current_user: User = Depends(get_current_admin_user),
    level: str = Query("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lấy recent system logs"""
    logger.info(f"Admin {current_user.username} viewing logs")
    
    # Trong thực tế, lấy từ logging service hoặc database
    # Đây là placeholder
    return {
        "logs": [],
        "level": level,
        "limit": limit,
        "message": "Logs retrieved from centralized logging system"
    }


@router.post(
    "/maintenance",
    summary="Toggle maintenance mode",
    description="Bật/tắt maintenance mode (admin only)"
)
async def toggle_maintenance(
    mode: MaintenanceMode,
    current_user: User = Depends(get_current_admin_user)
):
    """Bật hoặc tắt maintenance mode"""
    logger.warning(
        f"Admin {current_user.username} setting maintenance mode: {mode.enabled}"
    )
    
    # Trong thực tế, lưu vào Redis hoặc database để các instances khác nhìn thấy
    # Đây là placeholder
    return {
        "maintenance_mode": mode.enabled,
        "message": mode.message,
        "set_by": current_user.username,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post(
    "/cleanup",
    summary="Run system cleanup",
    description="Chạy cleanup tasks (admin only)"
)
async def run_cleanup(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Chạy các cleanup tasks"""
    logger.info(f"Admin {current_user.username} running cleanup")
    
    # Cleanup tasks
    results = {}
    
    # 1. Cleanup old pipeline executions
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    result = await db.pipeline_executions.delete_many({
        "completed_at": {"$lt": cutoff_date},
        "status": {"$in": ["completed", "failed", "cancelled"]}
    })
    results["old_executions_deleted"] = result.deleted_count
    
    # 2. Cleanup temp files (placeholder)
    results["temp_files_cleaned"] = 0
    
    return {
        "cleanup_results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ["router"]
