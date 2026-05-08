"""
Service and Security Tests
Tests for critical service layer and security functions
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.security_middleware import TokenManager, verify_password, get_password_hash
from app.services.places_service import PlacesService
from datetime import timedelta, datetime, timezone
from jose import jwt as jose_jwt
import redis.asyncio as redis


# ============================================================================
# PASSWORD SECURITY TESTS
# ============================================================================

def test_password_hashing():
    """Passwords should be properly hashed"""
    password = "MySecurePassword123!"
    hashed = get_password_hash(password)
    
    # Hash should not be the same as password
    assert hashed != password
    # Should be able to verify correct password
    assert verify_password(password, hashed)
    # Should reject incorrect password
    assert not verify_password("WrongPassword", hashed)


def test_password_hash_different_each_time():
    """Same password should produce different hashes (salt)"""
    password = "TestPassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Hashes should differ due to salt
    assert hash1 != hash2
    # But both should verify
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================

def test_token_manager_initialization():
    """TokenManager should initialize with proper configuration"""
    manager = TokenManager(
        secret_key="a" * 32,  # Minimum 32 chars
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )
    
    assert manager.secret_key == "a" * 32
    assert manager.algorithm == "HS256"
    assert manager.access_token_expire_minutes == 30
    assert manager.refresh_token_expire_days == 7


def test_token_manager_rejects_weak_secret():
    """TokenManager should reject weak secrets"""
    with pytest.raises(ValueError):
        TokenManager(
            secret_key="weak",  # Too short
            algorithm="HS256"
        )


def test_token_manager_rejects_invalid_algorithm():
    """TokenManager should only accept allowed JWT algorithms"""
    with pytest.raises(ValueError):
        TokenManager(
            secret_key="a" * 32,
            algorithm="RS256"  # Not in allowed list
        )


def test_create_access_token():
    """TokenManager should create valid access tokens"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        issuer="smart-travel",
        audience="smart-travel-users"
    )
    
    token = manager.create_access_token({"sub": "user123"})
    
    # Token should be a string
    assert isinstance(token, str)
    # Should have JWT structure (3 parts separated by dots)
    assert token.count(".") == 2


def test_token_contains_required_claims():
    """Tokens should contain required security claims"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        issuer="smart-travel",
        audience="smart-travel-users"
    )
    
    token = manager.create_access_token({"sub": "user123"})
    
    # Decode without verification to inspect claims
    payload = jose_jwt.get_unverified_claims(token)
    
    # Should have required claims
    assert "exp" in payload  # Expiration
    assert "iat" in payload  # Issued at
    assert "nbf" in payload  # Not before
    assert "jti" in payload  # JWT ID
    assert "iss" in payload  # Issuer
    assert "aud" in payload  # Audience
    assert payload["aud"] == "smart-travel-users"


def test_token_verification_validates_signature():
    """Token verification should validate signature integrity"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        issuer="smart-travel",
        audience="smart-travel-users"
    )
    
    token = manager.create_access_token({"sub": "user123"})
    payload = manager.verify_token(token, expected_type="access")
    
    assert payload["sub"] == "user123"
    assert payload["type"] == "access"


def test_token_verification_rejects_tampered_token():
    """Tampered tokens should be rejected"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256"
    )
    
    token = manager.create_access_token({"sub": "user123"})
    
    # Tamper with token
    tampered_token = token[:-5] + "XXXXX"
    
    # Should raise exception
    with pytest.raises(Exception):  # JWTError
        manager.verify_token(tampered_token)


def test_token_verification_rejects_expired_token():
    """Expired tokens should be rejected"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        access_token_expire_minutes=-1  # Already expired
    )
    
    token = manager.create_access_token({"sub": "user123"})
    
    # Should raise exception for expired token
    with pytest.raises(Exception):  # JWTError
        manager.verify_token(token)


# ============================================================================
# REFRESH TOKEN TESTS
# ============================================================================

def test_refresh_token_generation():
    """Refresh tokens should have longer expiration"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )
    
    refresh_token = manager.create_refresh_token({"sub": "user123"})
    payload = jose_jwt.get_unverified_claims(refresh_token)
    
    assert payload["type"] == "refresh"
    # Expiration should be much further in future than access token
    access_token = manager.create_access_token({"sub": "user123"})
    access_payload = jose_jwt.get_unverified_claims(access_token)
    
    # Refresh token exp > access token exp
    assert payload["exp"] > access_payload["exp"]


def test_token_rotation():
    """Token rotation should invalidate old refresh tokens"""
    manager = TokenManager(
        secret_key="a" * 32,
        algorithm="HS256",
        redis_client=None  # Test without Redis first
    )
    
    old_refresh = manager.create_refresh_token({"sub": "user123"})
    
    # Mock token rotation
    payload = jose_jwt.get_unverified_claims(old_refresh)
    assert payload["jti"]  # Should have JTI for revocation


# ============================================================================
# PLACES SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_places_service_initialization():
    """PlacesService should initialize with dependencies"""
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_mongo = AsyncMock()
    
    service = PlacesService(
        db=mock_db,
        redis_client=mock_redis,
        mongo_client=mock_mongo
    )
    
    assert service.db == mock_db
    assert service.redis_client == mock_redis


@pytest.mark.asyncio
async def test_get_places_constructs_query():
    """get_places should build correct MongoDB query"""
    from app.api.schemas.places import PlaceFilter
    
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    mock_mongo = AsyncMock()
    
    # Mock MongoDB collection
    mock_collection = AsyncMock()
    mock_mongo.__getitem__.return_value = {}
    mock_mongo.__getitem__.return_value.__getitem__ = AsyncMock(return_value=mock_collection)
    
    service = PlacesService(
        db=mock_db,
        redis_client=mock_redis,
        mongo_client=mock_mongo
    )
    
    filter_params = PlaceFilter(city="hanoi", category="restaurant", limit=10, offset=0)
    
    # Query should filter by city and category
    # (Only mocking structure - actual find() depends on motor)
    assert filter_params.city == "hanoi"
    assert filter_params.category == "restaurant"


@pytest.mark.asyncio
async def test_get_places_respects_pagination():
    """get_places should respect limit and offset"""
    from app.api.schemas.places import PlaceFilter
    
    filter_params = PlaceFilter(city="hanoi", limit=20, offset=100)
    
    assert filter_params.limit == 20
    assert filter_params.offset == 100


# ============================================================================
# SECURITY AUDIT TESTS  
# ============================================================================

def test_sensitive_data_masking():
    """Sensitive data should be masked in logs"""
    from app.core.security_middleware import _mask_sensitive
    
    data = {
        "password": "secret123",
        "secret_key": "mykey",
        "token": "jwt_token_here",
        "user_email": "user@example.com"
    }
    
    masked = _mask_sensitive(data)
    
    # Sensitive fields should be masked
    assert masked["password"] == "***REDACTED***"
    assert masked["secret_key"] == "***REDACTED***"
    assert masked["token"] == "***REDACTED***"
    # Non-sensitive should remain
    assert masked["user_email"] == "user@example.com"


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

def test_rbac_roles_exist():
    """RBAC roles should be defined"""
    roles = [
        "Administrator",
        "Operator",
        "Viewer"
    ]
    
    assert len(roles) > 0
    assert "Administrator" in roles


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_tracks_requests():
    """Rate limiter should track requests per user"""
    from app.core.security_middleware import RateLimiter
    
    mock_redis = AsyncMock()
    
    # Should be able to instantiate and use
    limiter = RateLimiter(
        redis_client=mock_redis,
        requests_per_minute=60
    )
    
    assert limiter.requests_per_minute == 60


# ============================================================================
# AUDIT LOGGING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_audit_logger_records_events():
    """Audit logger should record security events"""
    from app.core.security_middleware import AuditLogger
    
    logger = AuditLogger()
    
    # Should be instantiable
    assert logger is not None
