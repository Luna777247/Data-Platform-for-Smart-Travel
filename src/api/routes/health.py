"""
Health Check API Routes
=======================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/api/routes/health.py

Mục đích:
- Cung cấp health check endpoints cho Kubernetes probes và load balancers
- /health: Liveness probe - kiểm tra app có đang chạy không
- /ready: Readiness probe - kiểm tra app + dependencies sẵn sàng nhận traffic

Kubernetes Probes:
- Liveness: Restart container nếu fail
- Readiness: Remove pod from service endpoints nếu fail

Security: Public endpoints - không cần authentication
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Import FastAPI components
from fastapi import APIRouter               # Router cho grouping endpoints
from fastapi import Depends                 # Dependency injection

# Import Motor MongoDB client
from motor.motor_asyncio import AsyncIOMotorClient

# Import Redis async client
import redis.asyncio as redis

# Import logging
import logging

# Import JSONResponse cho custom status codes
from fastapi.responses import JSONResponse

# Import time cho timing
import time

# Import datetime
from datetime import datetime, timezone

# Import database dependencies
from src.api.dependencies.database import get_mongo_client, get_redis_client

# ============================================================================
# ROUTER INITIALIZATION
# ============================================================================

# Tạo router cho health endpoints
# Không có prefix - sẽ được mount ở root level trong main.py
router = APIRouter(
    tags=["Health"],  # Tag cho OpenAPI docs
)

# Logger cho module này
logger = logging.getLogger(__name__)

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

@router.get(
    "/health",
    summary="Liveness health check",
    description="""
    Liveness probe endpoint cho Kubernetes.
    
    Chỉ kiểm tra application có đang respond hay không.
    Không check dependencies.
    
    Returns:
        {"status": "alive", "timestamp": "..."}
    
    Status Codes:
        200: App is alive
    """
)
async def health_check():
    """
    Lightweight liveness probe.
    
    Kubernetes sẽ restart container nếu endpoint này fail.
    Keep this endpoint lightweight và không check external dependencies.
    """
    # Log health check (nhưng không log quá thường xuyên để tránh spam)
    # logger.debug("Health check requested")  # Optional
    
    # Return simple alive status
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/ready",
    summary="Readiness health check",
    description="""
    Readiness probe endpoint cho Kubernetes.
    
    Kiểm tra cả application và tất cả dependencies:
    - MongoDB: Ping database
    - Redis: Ping cache
    
    Returns:
        200 nếu tất cả healthy
        503 nếu có service nào degraded
    
    Status Codes:
        200: All dependencies ready
        503: One or more dependencies not ready
    """
)
async def readiness_check(
    # Dependency injection cho MongoDB client
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
    # Dependency injection cho Redis client
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Deep readiness probe với dependency checks.
    
    Kubernetes sẽ stop routing traffic đến pod nếu endpoint này fail.
    Điều này giúp đảm bảo app không nhận traffic khi dependencies down.
    
    Args:
        mongo_client: MongoDB client từ dependency
        redis_client: Redis client từ dependency
    
    Returns:
        JSONResponse với status và checks chi tiết
    """
    # Dictionary chứa kết quả check từng service
    checks = {}
    
    # Timestamp cho checks
    check_timestamp = datetime.now(timezone.utc).isoformat()
    
    # ========================================
    # CHECK 1: MongoDB
    # ========================================
    try:
        # Đo thời gian ping
        mongo_start = time.time()
        
        # Thực hiện ping command
        await mongo_client.admin.command("ping")
        
        # Tính latency
        mongo_latency = (time.time() - mongo_start) * 1000
        
        # MongoDB healthy
        checks["mongodb"] = {
            "status": "healthy",
            "latency_ms": round(mongo_latency, 2)
        }
        
        logger.debug(f"MongoDB health check passed: {mongo_latency:.2f}ms")
        
    except Exception as e:
        # MongoDB unhealthy - log error
        checks["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        logger.error(f"MongoDB health check failed: {e}")
    
    # ========================================
    # CHECK 2: Redis
    # ========================================
    try:
        # Đo thời gian ping
        redis_start = time.time()
        
        # Thực hiện ping
        await redis_client.ping()
        
        # Tính latency
        redis_latency = (time.time() - redis_start) * 1000
        
        # Redis healthy
        checks["redis"] = {
            "status": "healthy",
            "latency_ms": round(redis_latency, 2)
        }
        
        logger.debug(f"Redis health check passed: {redis_latency:.2f}ms")
        
    except Exception as e:
        # Redis unhealthy - log error
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        logger.error(f"Redis health check failed: {e}")
    
    # ========================================
    # DETERMINE OVERALL STATUS
    # ========================================
    # Đếm số service healthy
    healthy_services = sum(
        1 for check in checks.values()
        if isinstance(check, dict) and check.get("status") == "healthy"
    )
    
    total_services = len(checks)
    
    # Xác định overall status
    if healthy_services == total_services:
        # Tất cả services healthy
        overall = "healthy"
        status_code = 200
    elif healthy_services > 0:
        # Một số services healthy, một số degraded
        overall = "degraded"
        status_code = 503
    else:
        # Tất cả services unhealthy
        overall = "unhealthy"
        status_code = 503
    
    # Log readiness status
    if status_code == 200:
        logger.debug("Readiness check passed - all services healthy")
    else:
        logger.warning(
            f"Readiness check failed - {healthy_services}/{total_services} "
            f"services healthy"
        )
    
    # ========================================
    # BUILD RESPONSE
    # ========================================
    response_data = {
        "status": overall,
        "services": checks,
        "timestamp": check_timestamp,
        "healthy_count": healthy_services,
        "total_count": total_services
    }
    
    # Trả về JSONResponse với status code phù hợp
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


# ============================================================================
# ADDITIONAL HEALTH ENDPOINTS
# ============================================================================

@router.get(
    "/health/detailed",
    summary="Detailed health information",
    description="""
    Detailed health check với thông tin bổ sung.
    
    Returns:
        - Basic health status
        - Uptime
        - Version info
        - All dependency statuses
    """
)
async def detailed_health_check(
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Detailed health check với comprehensive information.
    
    Useful cho debugging và manual health checks.
    
    Args:
        mongo_client: MongoDB client
        redis_client: Redis client
    
    Returns:
        Dict với detailed health information
    """
    # Import settings cho version info
    from src.core.config import get_settings
    
    settings = get_settings()
    
    # Check tất cả services
    services = {}
    
    # MongoDB check
    try:
        start = time.time()
        await mongo_client.admin.command("ping")
        services["mongodb"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2),
            "host": settings.mongodb_host,
            "port": settings.mongodb_port
        }
    except Exception as e:
        services["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis check
    try:
        start = time.time()
        await redis_client.ping()
        services["redis"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - start) * 1000, 2),
            "host": settings.redis_host,
            "port": settings.redis_port
        }
    except Exception as e:
        services["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    all_healthy = all(
        s.get("status") == "healthy"
        for s in services.values()
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": services,
        "version": "1.0.0"  # Có thể lấy từ settings hoặc git
    }


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ["router"]