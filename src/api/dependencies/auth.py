"""
Authentication Dependencies - JWT Token Validation
==================================================
FastAPI dependency functions cho user authentication
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section VIII - Security

Mục đích:
- Xác thực JWT tokens từ Authorization header
- Trích xuất user information từ token payload
- Cung cấp dependency injection cho protected routes

Security Features:
- HTTP Bearer token authentication
- JWT signature verification
- Token expiration validation
- Audience validation
- HS256/HS384/HS512 algorithm support

Usage trong API routes:
    @router.get("/protected")
    async def protected_endpoint(
        current_user: str = Depends(get_current_user)
    ):
        return {"message": f"Hello {current_user}"}
"""

# Import typing components cho type hints
# Optional: Type cho giá trị có thể là None
from typing import Optional

# Import datetime components cho JWT expiration
# timedelta: Duration cho token expiration calculation
from datetime import datetime, timedelta

# Import FastAPI components cho dependency injection và error handling
# Depends: Dependency injection decorator
# HTTPException: Exception để trả về HTTP error responses
# status: HTTP status codes constants
from fastapi import Depends, HTTPException, status

# Import FastAPI components cho dependencies
# HTTPBearer: Security scheme cho JWT token extraction
# HTTPAuthorizationCredentials: Type cho credentials object
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import Pydantic cho User model
from pydantic import BaseModel, Field

class User(BaseModel):
    """User model cho authenticated user."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    role: str = Field(default="user", description="User role")
    is_active: bool = Field(default=True, description="Is active")

# Import jose (JavaScript Object Signing and Encryption) cho JWT operations
# JWTError: Exception khi JWT validation thất bại
# jwt: Module để encode/decode JWT tokens
from jose import JWTError, jwt

# Import settings từ core config để lấy JWT secret và algorithm
from src.core.config import settings


# ============================================
# SECURITY SETUP
# ============================================

# Tạo HTTPBearer security scheme instance
# Đây là FastAPI security scheme yêu cầu Bearer token trong header
# Format: Authorization: Bearer <jwt_token>
# Tự động xuất hiện trong OpenAPI/Swagger docs
security = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Enter your JWT token",
    auto_error=False  # Cho phép public endpoints - không tự động trả về 401
)


# ============================================
# AUTHENTICATION DEPENDENCY
# ============================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Validate JWT token và trả về username
    
    FastAPI dependency function để xác thực user trong protected routes.
    Được sử dụng với Depends() trong route handlers.
    
    Args:
        credentials: HTTPAuthorizationCredentials object từ HTTPBearer
                    Chứa scheme ("Bearer") và credentials (JWT token string)
    
    Returns:
        str: Username từ JWT token payload (sub claim)
    
    Raises:
        HTTPException: 401 Unauthorized nếu token invalid hoặc expired
    
    Example:
        >>> @router.get("/profile")
        ... async def get_profile(current_user: str = Depends(get_current_user)):
        ...     return {"user": current_user}
    
    JWT Payload Structure:
        {
            "sub": "username",      # Subject (user identifier)
            "exp": 1234567890,      # Expiration time
            "iat": 1234567800,      # Issued at
            "aud": "smart-travel-users",  # Audience
            "iss": "smart-travel-api"     # Issuer
        }
    """
    # Nếu không có credentials (public endpoint), trả về None
    if credentials is None:
        return None
        
    try:
        # Decode và validate JWT token
        # Sử dụng PyJWT/jose library với các security options
        payload = jwt.decode(
            # Token string từ Authorization header (sau "Bearer ")
            token=credentials.credentials,
            
            # Secret key để verify signature
            # Phải match với key dùng để encode token
            key=settings.jwt_secret,
            
            # JWT algorithms được phép
            # HS256, HS384, HS512 là HMAC-SHA algorithms
            algorithms=[settings.algorithm],
            
            # Audience validation - đảm bảo token đúng audience
            # Ngăn chặn token từ ứng dụng khác
            audience="smart-travel-users",
            
            # Additional validation options
            options={
                "require_exp": True,        # Yêu cầu expiration claim
                "verify_signature": True,   # Verify JWT signature
                "verify_aud": True,         # Verify audience
                "verify_iat": True,         # Verify issued at
                "verify_exp": True,         # Verify expiration
            },
        )
        
        # Trích xuất username từ "sub" (subject) claim
        # "sub" là standard JWT claim cho subject/user identifier
        username: str = payload.get("sub")
        
        # Kiểm tra username tồn tại trong payload
        if username is None:
            # Token không chứa subject claim
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return username cho route handler
        return username
        
    except JWTError as e:
        # JWTError được raise khi:
        # - Signature verification thất bại
        # - Token expired
        # - Invalid token format
        # - Algorithm không được phép
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# OPTIONAL AUTHENTICATION
# ============================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)  # Không auto error nếu thiếu token
    )
) -> Optional[str]:
    """
    Optional authentication - không require token nhưng validate nếu có
    
    Dùng cho endpoints cho phép cả authenticated và anonymous access
    Ví dụ: Public API với rate limiting khác nhau
    
    Args:
        credentials: Optional HTTPAuthorizationCredentials
    
    Returns:
        str: Username nếu có valid token
        None: Nếu không có token hoặc token invalid
    
    Example:
        >>> @router.get("/public-data")
        ... async def get_public_data(
        ...     current_user: Optional[str] = Depends(get_current_user_optional)
        ... ):
        ...     if current_user:
        ...         return {"data": premium_data}
        ...     return {"data": basic_data}
    """
    # Nếu không có credentials, return None (anonymous user)
    if credentials is None:
        return None
    
    try:
        # Thử validate token giống như get_current_user
        payload = jwt.decode(
            token=credentials.credentials,
            key=settings.jwt_secret,
            algorithms=[settings.algorithm],
            audience="smart-travel-users",
            options={
                "require_exp": True,
                "verify_signature": True,
            },
        )
        
        username: str = payload.get("sub")
        return username
        
    except JWTError:
        # Nếu token invalid, return None thay vì raise exception
        # Cho phép anonymous access
        return None


# ============================================
# ACTIVE USER DEPENDENCY
# ============================================

async def get_current_active_user(
    current_user: Optional[str] = Depends(get_current_user)
) -> str:
    """Get current active user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_current_admin_user(
    current_user: Optional[str] = Depends(get_current_user)
) -> str:
    """Get current admin user."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO: Check if user is admin
    return current_user


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_access_token(
    username: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT access token cho user
    
    Dùng trong login endpoint để tạo token sau khi authenticate
    
    Args:
        username: User identifier (sub claim)
        expires_delta: Token lifetime (default: 30 minutes)
    
    Returns:
        str: JWT token string
    
    Example:
        >>> token = create_access_token("user123")
        >>> return {"access_token": token, "token_type": "bearer"}
    """
    from datetime import datetime, timezone, timedelta
    
    # Tính thời điểm tạo token
    now = datetime.now(timezone.utc)
    
    # Tính thời điểm hết hạn
    if expires_delta:
        expire = now + expires_delta
    else:
        # Default: 30 minutes
        expire = now + timedelta(minutes=30)
    
    # Tạo JWT payload (claims)
    to_encode = {
        "sub": username,                    # Subject (user)
        "exp": expire,                      # Expiration time
        "iat": now,                         # Issued at
        "aud": "smart-travel-users",        # Audience
        "iss": "smart-travel-api",          # Issuer
        "type": "access",                   # Token type
    }
    
    # Encode thành JWT string
    encoded_jwt = jwt.encode(
        claims=to_encode,
        key=settings.jwt_secret,
        algorithm=settings.algorithm,  # Dùng algorithm đầu tiên
    )
    
    return encoded_jwt


# ============================================
# ADMIN AUTHENTICATION
# ============================================

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency cho admin-only endpoints
    
    Kiểm tra:
    1. Token hợp lệ
    2. User có role là 'admin'
    
    Args:
        credentials: HTTPAuthorizationCredentials từ request header
    
    Returns:
        User: Admin user object
    
    Raises:
        HTTPException: 403 nếu không phải admin, 401 nếu token invalid
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(get_current_admin_user)
        ):
            return {"message": f"Hello admin {current_user.username}"}
    """
    # Lấy username từ token (reuse existing logic)
    username = await get_current_user(credentials)
    
    # Kiểm tra nếu không có token hoặc token invalid
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Trong thực tế, query database để lấy user details và role
    # Đây là simplified version - giả định user là admin nếu username có suffix "_admin"
    # Hoặc có thể kiểm tra trong JWT payload
    
    # Ví dụ: giả định user là admin
    # Trong thực tế, nên query database hoặc decode JWT payload để lấy role
    is_admin = "_admin" in username or username in ["admin", "superuser"]
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        id=username,
        username=username,
        email=f"{username}@system.local",
        role="admin",
        is_active=True
    )


# ============================================
# PASSWORD UTILITIES
# ============================================

from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash password sử dụng bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        bool: True nếu match
    """
    return pwd_context.verify(plain_password, hashed_password)


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token và trả về username.
    
    Args:
        token: JWT token string
        
    Returns:
        str: Username nếu token hợp lệ, None nếu không hợp lệ
    """
    try:
        payload = jwt.decode(
            token=token,
            key=settings.jwt_secret,
            algorithms=[settings.algorithm],
            audience="smart-travel-users",
        )
        return payload.get("sub")
    except JWTError:
        return None


# ============================================
# MODULE IMPORTS
# ============================================
from datetime import timedelta


# ============================================
# EXPORTS
# ============================================
__all__ = [
    "security",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_admin_user",
    "create_access_token",
    "verify_token",
    "get_password_hash",
    "verify_password",
    "User",
]