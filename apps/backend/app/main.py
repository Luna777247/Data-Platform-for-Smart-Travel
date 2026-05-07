#!/usr/bin/env python3
"""
Smart Travel API - Main Application

Features:
- Async FastAPI with proper lifespan management
- Database connections (MongoDB, PostgreSQL, Redis)
- Security middleware (rate limiting, audit logging, security headers)
- Prometheus metrics
- Structured logging
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import places, pipeline, health
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.client import MongoClient
from app.api.dependencies.database import engine, redis_client
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuditMiddleware,
    AuditLogger,
)

# ============================================================================
# LOGGING
# ============================================================================
setup_logging()
logger = logging.getLogger(__name__)
audit_logger = AuditLogger()


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events.
    """

    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("🚀 Starting up Smart Travel API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Rate limiting: {settings.rate_limit_enabled}")

    _validate_runtime_security_configuration()

    try:
        # 1. MongoDB
        logger.info("Connecting to MongoDB...")
        await MongoClient.connect()
        if MongoClient.is_connected:
            logger.info("✅ MongoDB connected")
        else:
            logger.warning("⚠️  MongoDB NOT connected – running with fallback")

        # 2. PostgreSQL (async engine)
        logger.info("Connecting to PostgreSQL...")
        try:
            async with engine.connect() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            logger.info("✅ PostgreSQL connected")
        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL NOT connected: {e}")

        # 3. Redis
        logger.info("Connecting to Redis...")
        try:
            await redis_client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"⚠️  Redis NOT connected: {e}")

        logger.info("✅ API startup completed successfully")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

    yield  # ←── APP IS RUNNING

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("🛑 Shutting down Smart Travel API...")

    try:
        await MongoClient.disconnect()
        await engine.dispose()
        await redis_client.aclose()
        logger.info("✅ All connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# ============================================================================
# APPLICATION FACTORY
# ============================================================================
app = FastAPI(
    title="Smart Travel Data Platform API",
    description="API for collecting, processing, and analyzing travel destination data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def _validate_runtime_security_configuration() -> None:
    settings.validate_security_configuration()
    if any(origin == "*" for origin in settings.allowed_origins_list):
        raise RuntimeError("Wildcard CORS origins are forbidden")
    if settings.environment.lower() in {"prod", "production"} and settings.debug:
        raise RuntimeError("DEBUG must be disabled in production")


# ============================================================================
# MIDDLEWARE STACK (Order matters - from bottom to top of stack)
# ============================================================================

# 1. Audit Middleware (runs last, logs all requests)
app.add_middleware(AuditMiddleware, audit_logger=audit_logger)

# 2. Rate Limiting Middleware
app.add_middleware(
    RateLimitMiddleware,
    redis_client=redis_client,
    enabled=settings.rate_limit_enabled,
)

# 3. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 4. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Process-Time", "X-Request-ID"],
    max_age=3600,
)


# ============================================================================
# ROUTES
# ============================================================================
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(places.router, prefix="/api", tags=["places"])
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])


# ============================================================================
# METRICS
# ============================================================================
# Prometheus metrics - exposes at /metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check for load balancers."""
    return {"status": "healthy", "environment": settings.environment}


# ============================================================================
# STARTUP EVENT
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Additional startup tasks."""
    logger.info("✅ FastAPI startup event completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Additional shutdown tasks."""
    logger.info("✅ FastAPI shutdown event completed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug and settings.environment.lower() not in {"prod", "production"},
        log_level=settings.log_level.lower(),
    )
