"""
Authentication Routes
======================

API endpoints cho authentication và authorization.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from src.api.dependencies.auth import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()

# Service instance
auth_service = AuthService()


# ============= SCHEMAS =============

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class RegisterRequest(BaseModel):
    """Register request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    username: str


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserInfo(BaseModel):
    """User info response."""
    username: str
    email: Optional[str] = None
    role: str = "user"
    is_active: bool = True


# ============= ENDPOINTS =============

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login và nhận JWT token.
    
    Example:
        ```json
        {
            "username": "admin",
            "password": "admin123"
        }
        ```
    """
    # Authenticate user
    user = await auth_service.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token = create_access_token(
        username=user["username"],
        expires_delta=timedelta(hours=24)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
        username=user["username"]
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register new user và nhận JWT token.
    
    Example:
        ```json
        {
            "username": "newuser",
            "password": "password123",
            "email": "user@example.com"
        }
        ```
    """
    # Check if user exists
    if request.username in auth_service._users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    try:
        password_hash = get_password_hash(request.password)
    except Exception:
        # Fallback for development
        password_hash = request.password
    
    auth_service._users[request.username] = {
        "username": request.username,
        "password_hash": password_hash,
        "email": request.email,
        "role": "user",
        "is_active": True
    }
    
    # Create token
    access_token = create_access_token(
        username=request.username,
        expires_delta=timedelta(hours=24)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,
        username=request.username
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh JWT token.
    
    Cung cấp valid token để nhận token mới.
    """
    token = credentials.credentials
    
    # Verify current token
    username = verify_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user exists
    if username not in auth_service._users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new token
    new_token = create_access_token(
        username=username,
        expires_delta=timedelta(hours=24)
    )
    
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=86400,
        username=username
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information."""
    token = credentials.credentials
    username = verify_token(token)
    
    if not username or username not in auth_service._users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service._users[username]
    
    return UserInfo(
        username=user["username"],
        email=user.get("email"),
        role=user.get("role", "user"),
        is_active=user.get("is_active", True)
    )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout (client-side token removal).
    
    Note: JWT tokens are stateless, so logout is handled client-side.
    Server can add token to blacklist if needed.
    """
    return {"message": "Logged out successfully"}


@router.get("/validate")
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate if token is still valid."""
    token = credentials.credentials
    username = verify_token(token)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "username": username
    }
