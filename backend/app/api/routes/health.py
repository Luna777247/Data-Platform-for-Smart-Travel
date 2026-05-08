"""
Fix #7: Health routes — thêm /ready endpoint cho Kubernetes readinessProbe.
/health = liveness (app is alive)
/ready  = readiness (app + deps sẵn sàng nhận traffic)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import logging

from app.api.dependencies.database import get_db, get_mongo_client, get_redis_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Lightweight liveness probe — chỉ cần app respond."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """Deep readiness probe — kiểm tra tất cả dependencies."""
    checks = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception as e:
        checks["postgres"] = f"unhealthy: {e}"

    # MongoDB
    try:
        await mongo_client.admin.command("ping")
        checks["mongodb"] = "healthy"
    except Exception as e:
        checks["mongodb"] = f"unhealthy: {e}"

    # Redis
    try:
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

    status_code = 200 if overall == "healthy" else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "services": checks},
    )