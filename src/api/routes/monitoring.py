"""
Monitoring & Health Check API Routes
====================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/api/routes/monitoring.py

Mục đích:
- Cung cấp health check endpoints cho load balancers và monitoring systems
- Expose Prometheus metrics
- API status và version information
- Database connectivity checks

Các endpoints:
- GET /health: Basic health check (liveness)
- GET /ready: Readiness check (includes database connectivity)
- GET /metrics: Prometheus metrics
- GET /api/v1/monitoring/status: Detailed system status
- GET /api/v1/monitoring/version: API version info

Security:
- Health checks: Public (no auth required)
- Detailed monitoring: JWT authentication
- Metrics: Prometheus scraping (internal network)
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Import FastAPI components
from fastapi import APIRouter           # Router cho endpoints
from fastapi import Depends             # Dependency injection
from fastapi import HTTPException       # Exception handling
from fastapi import status              # HTTP status codes

# Import JSONResponse cho custom responses
from fastapi.responses import JSONResponse

# Import Response cho raw responses
from fastapi.responses import Response

# Import Pydantic BaseModel
from pydantic import BaseModel

# Import Field cho field validation
from pydantic import Field

# Import Optional type
from typing import Optional

# Import Dict cho dictionary types
from typing import Dict

# Import Any cho flexible typing
from typing import Any

# Import List cho list types
from typing import List

# Import datetime cho timestamps
from datetime import datetime

# Import timezone
from datetime import timezone

# Import os cho environment variables
import os

# Import json cho JSON operations
import json

# Import platform cho system info
import platform

# Import sys cho Python version
import sys

# Import time cho uptime calculation
import time

# Import logging
import logging

# Import async operations
import asyncio

# Import dependencies
from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.auth import User
from src.api.dependencies.database import get_database

# Import Motor database
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import settings
from src.core.config import get_settings

# Import Redis client
from src.db.client import get_redis_pool

# ============================================================================
# ROUTER INITIALIZATION
# ============================================================================

# Tạo router cho monitoring endpoints
router = APIRouter(
    tags=["Monitoring"],  # Tag cho OpenAPI docs grouping
)

# Logger cho module này
logger = logging.getLogger(__name__)

# Settings instance
settings = get_settings()

# Start time để tính uptime
START_TIME = time.time()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class HealthStatus(BaseModel):
    """
    Schema cho basic health check response
    
    Attributes:
        status: Health status (healthy/unhealthy)
        timestamp: Current UTC timestamp
        uptime_seconds: Application uptime in seconds
    """
    status: str = Field(..., description="Health status: healthy or unhealthy")
    timestamp: str = Field(..., description="Current UTC timestamp (ISO format)")
    uptime_seconds: float = Field(..., ge=0, description="Application uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-06-15T10:30:00.000Z",
                "uptime_seconds": 86400.5
            }
        }


class ReadinessStatus(BaseModel):
    """
    Schema cho readiness check response
    
    Kiểm tra tất cả dependencies có sẵn sàng không.
    
    Attributes:
        status: Overall readiness status
        checks: Chi tiết từng dependency check
        timestamp: Current UTC timestamp
    """
    status: str = Field(..., description="Overall status: ready or not_ready")
    checks: Dict[str, Any] = Field(..., description="Individual dependency checks")
    timestamp: str = Field(..., description="Current UTC timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ready",
                "checks": {
                    "mongodb": {"status": "connected", "latency_ms": 5.2},
                    "redis": {"status": "connected", "latency_ms": 2.1}
                },
                "timestamp": "2024-06-15T10:30:00.000Z"
            }
        }


class VersionInfo(BaseModel):
    """
    Schema cho API version information
    
    Attributes:
        version: API version string
        build: Build number/hash
        environment: Deployment environment
        python_version: Python version
        platform: Operating system platform
    """
    version: str = Field(..., description="API version (semver)")
    build: str = Field(..., description="Build identifier")
    environment: str = Field(..., description="Deployment environment")
    python_version: str = Field(..., description="Python version")
    platform: str = Field(..., description="OS platform")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "1.0.0",
                "build": "abc123d",
                "environment": "production",
                "python_version": "3.11.4",
                "platform": "Linux-5.15-x86_64"
            }
        }


class SystemMetrics(BaseModel):
    """
    Schema cho system metrics
    
    Attributes:
        cpu_percent: CPU usage percentage
        memory_percent: Memory usage percentage
        disk_usage_percent: Disk usage percentage
        active_connections: Số active connections
    """
    cpu_percent: Optional[float] = Field(None, description="CPU usage %")
    memory_percent: Optional[float] = Field(None, description="Memory usage %")
    disk_usage_percent: Optional[float] = Field(None, description="Disk usage %")
    active_connections: Optional[int] = Field(None, description="Active connections")


class DetailedStatus(BaseModel):
    """
    Schema cho detailed monitoring status
    
    Attributes:
        health: Basic health status
        version: Version information
        metrics: System metrics
        dependencies: Dependency statuses
        config: Public configuration info
    """
    health: HealthStatus
    version: VersionInfo
    metrics: SystemMetrics
    dependencies: Dict[str, Any]
    config: Dict[str, Any]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_mongodb_health(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Kiểm tra MongoDB connection health
    
    Args:
        db: MongoDB database instance
    
    Returns:
        Dict[str, Any]: Health check result với status và latency
    """
    try:
        # Đo thời gian ping
        start = time.time()
        
        # Thực hiện ping command
        await db.command('ping')
        
        # Tính latency
        latency = (time.time() - start) * 1000  # Convert to ms
        
        return {
            "status": "connected",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e)
        }


async def check_redis_health() -> Dict[str, Any]:
    """
    Kiểm tra Redis connection health
    
    Returns:
        Dict[str, Any]: Health check result với status và latency
    """
    try:
        # Lấy Redis client
        redis_client = await get_redis_pool()
        
        # Đo thời gian ping
        start = time.time()
        
        # Thực hiện ping
        await redis_client.ping()
        
        # Tính latency
        latency = (time.time() - start) * 1000
        
        return {
            "status": "connected",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e)
        }


def get_system_metrics() -> SystemMetrics:
    """
    Lấy system metrics (CPU, memory, disk)
    
    Returns:
        SystemMetrics: Current system metrics
    """
    try:
        # Import psutil nếu có
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemMetrics(
                cpu_percent=round(cpu_percent, 1),
                memory_percent=round(memory.percent, 1),
                disk_usage_percent=round(disk.percent, 1),
                active_connections=None  # Có thể implement nếu cần
            )
        except ImportError:
            # psutil không được install, trả về None values
            return SystemMetrics()
    except Exception as e:
        logger.warning(f"Could not get system metrics: {e}")
        return SystemMetrics()


# ============================================================================
# PUBLIC ENDPOINTS (No auth required)
# ============================================================================

@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Basic health check",
    description="""
    Simple health check endpoint cho load balancers và monitoring systems.
    
    Returns:
        - status: "healthy" nếu API đang chạy
        - timestamp: Thời gian hiện tại
        - uptime_seconds: Thời gian đã chạy
    
    This endpoint KHÔNG require authentication và KHÔNG check dependencies.
    Dùng cho Kubernetes liveness probes.
    """,
    responses={
        200: {"description": "API is healthy"},
    }
)
async def health_check():
    """
    Basic health check - liveness probe.
    
    Chỉ check API có đang chạy không, không check dependencies.
    """
    # Tính uptime
    uptime = time.time() - START_TIME
    
    # Current timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    return HealthStatus(
        status="healthy",
        timestamp=timestamp,
        uptime_seconds=round(uptime, 2)
    )


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="Readiness check",
    description="""
    Readiness check endpoint cho load balancers.
    
    Kiểm tra tất cả dependencies (MongoDB, Redis):
    - Trả về "ready" nếu tất cả dependencies healthy
    - Trả về "not_ready" và HTTP 503 nếu có dependency fail
    
    This endpoint KHÔNG require authentication.
    Dùng cho Kubernetes readiness probes.
    """,
    responses={
        200: {"description": "All dependencies ready"},
        503: {"description": "One or more dependencies not ready"},
    }
)
async def readiness_check(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Readiness check - kiểm tra tất cả dependencies.
    
    Returns:
        ReadinessStatus với chi tiết từng dependency
    """
    # Check tất cả dependencies
    checks = {}
    all_ready = True
    
    # Check MongoDB
    mongo_status = await check_mongodb_health(db)
    checks["mongodb"] = mongo_status
    if mongo_status["status"] != "connected":
        all_ready = False
    
    # Check Redis
    redis_status = await check_redis_health()
    checks["redis"] = redis_status
    if redis_status["status"] != "connected":
        all_ready = False
    
    # Timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Determine overall status
    from fastapi import status as http_status
    readiness_status = "ready" if all_ready else "not_ready"
    
    response = ReadinessStatus(
        status=readiness_status,
        checks=checks,
        timestamp=timestamp
    )
    
    # Return 503 nếu not ready
    if not all_ready:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.dict()
        )
    
    return response


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="""
    Prometheus metrics endpoint cho monitoring.
    
    Returns metrics ở Prometheus exposition format.
    
    This endpoint typically được access bởi Prometheus scraper
    từ internal network, không cần authentication.
    """,
    responses={
        200: {"description": "Prometheus metrics", "content": {"text/plain": {}}},
    }
)
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    
    Trong thực tế, có thể dùng prometheus-client library để
    generate metrics. Ở đây là simplified version.
    
    Returns:
        Plain text Prometheus format
    """
    # Tạo simple metrics (trong thực tế, dùng prometheus-client)
    uptime = time.time() - START_TIME
    
    # Metrics ở Prometheus format
    metrics_text = f"""# HELP smart_tourism_uptime_seconds Application uptime
# TYPE smart_tourism_uptime_seconds counter
smart_tourism_uptime_seconds {uptime}

# HELP smart_tourism_info Application information
# TYPE smart_tourism_info gauge
smart_tourism_info{{version="1.0.0",environment="{settings.environment}"}} 1
"""
    
    return Response(
        content=metrics_text,
        media_type="text/plain"
    )


# ============================================================================
# AUTHENTICATED ENDPOINTS (JWT required)
# ============================================================================

@router.get(
    "/api/v1/monitoring/status",
    response_model=DetailedStatus,
    summary="Detailed system status",
    description="""
    Lấy detailed system status và metrics.
    
    Requires JWT authentication.
    
    Returns:
        - Health status
        - Version information
        - System metrics
        - Dependency statuses
        - Configuration info
    """,
    responses={
        200: {"description": "Detailed status retrieved"},
        401: {"description": "Unauthorized"},
    }
)
async def get_detailed_status(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed system status.
    
    Args:
        db: Database instance
        current_user: Authenticated user
    
    Returns:
        DetailedStatus với comprehensive system information
    """
    logger.info(f"Detailed status requested by user: {current_user.username}")
    
    # Health status
    uptime = time.time() - START_TIME
    health = HealthStatus(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(uptime, 2)
    )
    
    # Version info
    # Lấy git commit hash nếu có
    build = os.getenv("GIT_COMMIT", "unknown")
    if build == "unknown":
        build = "development"
    
    version = VersionInfo(
        version="1.0.0",
        build=build,
        environment=settings.environment,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.platform()
    )
    
    # System metrics
    metrics = get_system_metrics()
    
    # Dependencies
    dependencies = {
        "mongodb": await check_mongodb_health(db),
        "redis": await check_redis_health()
    }
    
    # Public config (không expose secrets)
    config = {
        "environment": settings.environment,
        "log_level": settings.log_level,
        "mongodb_host": settings.mongodb_host,
        "mongodb_port": settings.mongodb_port,
        "redis_host": settings.redis_host,
        "redis_port": settings.redis_port,
    }
    
    return DetailedStatus(
        health=health,
        version=version,
        metrics=metrics,
        dependencies=dependencies,
        config=config
    )


@router.get(
    "/api/v1/monitoring/version",
    response_model=VersionInfo,
    summary="API version information",
    description="""
    Lấy API version và build information.
    
    Requires JWT authentication.
    """,
)
async def get_version(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get API version information.
    
    Returns:
        VersionInfo với version, build, environment
    """
    logger.info(f"Version info requested by user: {current_user.username}")
    
    # Lấy build info
    build = os.getenv("GIT_COMMIT", "unknown")
    if build == "unknown":
        build = "development"
    
    return VersionInfo(
        version="1.0.0",
        build=build,
        environment=settings.environment,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        platform=platform.platform()
    )


@router.get(
    "/api/v1/monitoring/dependencies",
    summary="Dependency health status",
    description="""
    Lấy chi tiết health status của tất cả dependencies.
    
    Requires JWT authentication.
    """,
)
async def get_dependencies_status(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed dependency health status.
    
    Returns:
        Dict với status của từng dependency
    """
    logger.info(f"Dependencies status requested by user: {current_user.username}")
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "mongodb": await check_mongodb_health(db),
            "redis": await check_redis_health()
        }
    }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ["router"]
