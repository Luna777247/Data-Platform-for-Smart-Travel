"""
Authentication Service
======================

Business logic cho authentication và authorization.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/services/auth_service.py

Responsibilities:
- User authentication
- Token management
- Role-based access control
- Session management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.api.dependencies.auth import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service cho authentication và authorization.
    
    Provides:
    - User authentication
    - JWT token management
    - Role management
    - Permission checking
    """
    
    # Mock user database - in production use actual DB
    _users: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self):
        logger.info("AuthService initialized")
        # Initialize default users in __init__ to avoid bcrypt issues at class level
        if not self._users:
            self._init_default_users()
    
    def _init_default_users(self):
        """Initialize default users."""
        # Luôn lưu plain text password cho fallback khi bcrypt lỗi
        default_users = {
            "admin": {"password": "admin123", "role": "admin"},
            "testuser": {"password": "test123", "role": "user"},
        }
        
        for uname, info in default_users.items():
            pwd = info["password"]
            try:
                hashed = get_password_hash(pwd)
            except Exception as e:
                logger.warning(f"bcrypt hash failed for {uname}: {e}")
                hashed = pwd  # fallback plain text
            
            self._users[uname] = {
                "username": uname,
                "password_hash": hashed,
                "_password_plain": pwd,  # Backup for dev when bcrypt is broken
                "role": info["role"],
                "is_active": True,
            }
        
        logger.info(f"Initialized {len(self._users)} default users")
    
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user và trả về token."""
        user = self._users.get(username)
        
        if not user:
            return None
        
        # Check password – support cả bcrypt hash lẫn plain-text fallback
        stored_hash = user["password_hash"]
        password_ok = False
        
        # 1) Plain text match (dev fallback)
        if stored_hash == password:
            password_ok = True
        
        # 2) Backup plain text field match (khi hash là bcrypt nhưng verify lỗi)
        if not password_ok and user.get("_password_plain") == password:
            password_ok = True
        
        # 3) bcrypt verify (production)
        if not password_ok:
            try:
                password_ok = verify_password(password, stored_hash)
            except Exception:
                password_ok = False
        
        if not password_ok:
            return None
        
        if not user["is_active"]:
            return None
        
        # Create access token
        token = create_access_token(
            username=username,
            expires_delta=timedelta(hours=24)
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": username,
            "role": user["role"],
            "expires_in": 86400  # 24 hours in seconds
        }
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token."""
        username = verify_token(token)
        if username:
            user = self._users.get(username)
            if user and user["is_active"]:
                return {
                    "username": username,
                    "role": user["role"]
                }
        return None
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        user = self._users.get(username)
        if user:
            return {
                "username": user["username"],
                "role": user["role"],
                "is_active": user["is_active"]
            }
        return None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        return [
            {
                "username": u["username"],
                "role": u["role"],
                "is_active": u["is_active"]
            }
            for u in self._users.values()
        ]
    
    async def create_user(
        self,
        username: str,
        password: str,
        role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """Create new user."""
        if username in self._users:
            return None
        
        self._users[username] = {
            "username": username,
            "password_hash": get_password_hash(password),
            "role": role,
            "is_active": True
        }
        
        logger.info(f"Created user: {username}")
        
        return {
            "username": username,
            "role": role,
            "is_active": True
        }
    
    async def delete_user(self, username: str) -> bool:
        """Delete user."""
        if username in self._users:
            del self._users[username]
            logger.info(f"Deleted user: {username}")
            return True
        return False
    
    async def check_permission(
        self,
        username: str,
        required_role: str
    ) -> bool:
        """Check if user has required role."""
        user = self._users.get(username)
        if not user:
            return False
        
        # Role hierarchy: admin > user
        if required_role == "user":
            return user["role"] in ["user", "admin"]
        elif required_role == "admin":
            return user["role"] == "admin"
        
        return False
