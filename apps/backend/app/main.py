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

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("🚀 Starting up Smart Travel API...")

    # 1. MongoDB
    await MongoClient.connect()
    if MongoClient.is_connected:
        logger.info("✅ MongoDB connected")
    else:
        logger.warning("⚠️  MongoDB NOT connected – running with fallback")

    # 2. PostgreSQL (async engine – ping via connect)
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("✅ PostgreSQL connected")
    except Exception as e:
        logger.warning(f"⚠️  PostgreSQL NOT connected: {e}")

    # 3. Redis
    try:
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️  Redis NOT connected: {e}")

    yield  # ←── app is running

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("🛑 Shutting down Smart Travel API...")
    await MongoClient.disconnect()
    await engine.dispose()
    await redis_client.aclose()
    logger.info("✅ All connections closed")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Smart Travel API",
    description="API for Smart Travel Data Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(places.router, prefix="/api", tags=["places"])
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])

# Prometheus metrics – exposes /metrics automatically
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
