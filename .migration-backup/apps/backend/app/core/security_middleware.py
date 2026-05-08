"""Security, rate-limiting, and audit middleware for Smart Travel API."""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging_config import clear_request_id, set_request_id

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


def _mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        masked = {}
        for key, item in value.items():
            if any(sensitive in key.lower() for sensitive in {"password", "secret", "token", "key", "cookie", "authorization"}):
                masked[key] = "***REDACTED***"
            else:
                masked[key] = _mask_sensitive(item)
        return masked
    if isinstance(value, list):
        return [_mask_sensitive(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith("bearer ") or "secret" in lowered or "token" in lowered:
            return "***REDACTED***"
    return value


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


class TokenManager:
    """Manage JWT access/refresh tokens with validation and rotation."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        issuer: str = "smart-travel",
        audience: str = "smart-travel-users",
        redis_client: redis.Redis | None = None,
    ):
        normalized_algorithm = algorithm.upper().strip()
        if normalized_algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise ValueError(f"Unsupported JWT algorithm: {algorithm}")

        if not secret_key or len(secret_key) < 32:
            raise ValueError("JWT secret must be a strong secret")

        self.secret_key = secret_key
        self.algorithm = normalized_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        self.audience = audience
        self.redis_client = redis_client

    def _base_claims(self, data: dict, token_type: str, expires_delta: timedelta) -> dict:
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + expires_delta
        to_encode.update(
            {
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int(expire.timestamp()),
                "type": token_type,
                "jti": str(uuid.uuid4()),
                "iss": self.issuer,
                "aud": self.audience,
            }
        )
        return to_encode

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = self._base_claims(
            data,
            token_type="access",
            expires_delta=expires_delta or timedelta(minutes=self.access_token_expire_minutes),
        )
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = self._base_claims(
            data,
            token_type="refresh",
            expires_delta=expires_delta or timedelta(days=self.refresh_token_expire_days),
        )
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def _decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require_exp": True, "verify_signature": True},
            )
        except JWTError as exc:
            logger.warning("JWT verification failed", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    def verify_token(self, token: str, expected_type: str | None = None) -> Dict[str, Any]:
        payload = self._decode_token(token)
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

    async def revoke_token(self, jti: str, expires_at: int) -> None:
        if not self.redis_client:
            return
        ttl = max(1, expires_at - int(datetime.now(timezone.utc).timestamp()))
        await self.redis_client.set(f"jwt:revoked:{jti}", "1", ex=ttl)

    async def is_token_revoked(self, jti: str) -> bool:
        if not self.redis_client:
            return False
        return await self.redis_client.exists(f"jwt:revoked:{jti}") > 0

    async def rotate_refresh_token(self, refresh_token: str) -> Dict[str, str]:
        payload = self.verify_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        exp = int(payload.get("exp", 0))
        if jti:
            await self.revoke_token(jti, exp)

        subject = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_payload = {key: value for key, value in payload.items() if key not in {"exp", "nbf", "iat", "jti", "type", "aud", "iss"}}
        token_payload["sub"] = subject
        return {
            "access_token": self.create_access_token(token_payload),
            "refresh_token": self.create_refresh_token(token_payload),
        }

    def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = self.verify_token(refresh_token, expected_type="refresh")
            subject = payload.get("sub")
            if not subject:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return self.create_access_token({"sub": subject, "role": payload.get("role")})
        except HTTPException:
            raise
        except JWTError as exc:
            logger.warning("Refresh token failed", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc


class RateLimiter:
    def __init__(
        self,
        redis_client: redis.Redis,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def is_allowed(self, key: str) -> bool:
        try:
            minute_key = f"rate_limit:minute:{key}:{int(time.time() / 60)}"
            minute_count = await self.redis_client.incr(minute_key)
            if minute_count == 1:
                await self.redis_client.expire(minute_key, 60)
            if minute_count > self.requests_per_minute:
                return False

            hour_key = f"rate_limit:hour:{key}:{int(time.time() / 3600)}"
            hour_count = await self.redis_client.incr(hour_key)
            if hour_count == 1:
                await self.redis_client.expire(hour_key, 3600)
            return hour_count <= self.requests_per_hour
        except Exception as exc:
            logger.error("Rate limit check failed", extra={"error": str(exc)})
            return True


class AuditLogger:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("audit")

    async def log_request(
        self,
        request: Request,
        user_id: Optional[str] = None,
        response_status: int | None = None,
        request_id: str | None = None,
    ):
        log_entry = {
            "event": "api_request",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
            "method": request.method,
            "path": request.url.path,
            "query": _mask_sensitive(dict(request.query_params)),
            "client_ip": self._get_client_ip(request),
            "user_id": user_id,
            "response_status": response_status,
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        return log_entry["request_id"]

    async def log_error(self, request: Request, error: Exception, user_id: Optional[str] = None):
        log_entry = {
            "event": "api_error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "user_id": user_id,
            "error": _mask_sensitive(str(error)),
            "error_type": type(error).__name__,
        }
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        if request.client:
            return request.client.host
        return request.headers.get("x-forwarded-for", "unknown").split(",")[0].strip() or "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
            "form-action 'self'; img-src 'self' data: https:; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; connect-src 'self' https: wss:"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis, enabled: bool = True):
        super().__init__(app)
        self.redis_client = redis_client
        self.enabled = enabled
        self.limiter = RateLimiter(redis_client)

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path in ["/api/health", "/metrics", "/health"]:
            return await call_next(request)

        client_id = self._get_client_id(request)
        if not await self.limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)

    @staticmethod
    def _get_client_id(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, audit_logger: AuditLogger | None = None):
        super().__init__(app)
        self.audit_logger = audit_logger or AuditLogger()

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{time.time() - start_time:.6f}"
            await self.audit_logger.log_request(
                request,
                response_status=response.status_code,
                request_id=request_id,
            )
            return response
        except Exception as exc:
            await self.audit_logger.log_error(request, exc)
            raise
        finally:
            clear_request_id()
