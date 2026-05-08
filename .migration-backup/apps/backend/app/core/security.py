from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if settings.algorithm not in ALLOWED_JWT_ALGORITHMS:
        raise ValueError(f"Unsupported JWT algorithm: {settings.algorithm}")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(timezone.utc)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.algorithm)
    return encoded_jwt