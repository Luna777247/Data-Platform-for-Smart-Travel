"""
Smart Tourism Data Platform - FastAPI Application Entry Point
===============================================================
Main application module để khởi động FastAPI server
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/ section

Mục đích:
- Khởi tạo FastAPI application với lifespan management
- Cấu hình middleware (CORS, security, logging)
- Đăng ký API routes
- Quản lý database connections (MongoDB, Redis)
- Cung cấp health checks và monitoring endpoints

Chạy ứng dụng:
    Development: uvicorn src.main:app --reload --port 8000
    Production:  gunicorn -k uvicorn.workers.UvicornWorker src.main:app

Environment Variables:
    ENVIRONMENT: development | staging | production
    LOG_LEVEL: DEBUG | INFO | WARNING | ERROR
    MONGODB_URI: MongoDB connection string
    REDIS_URL: Redis connection string
"""

# Import asyncio để hỗ trợ async operations trong lifespan
import asyncio

# Import logging để cấu hình logging cho toàn bộ ứng dụng
import logging

# Import sys để truy cập system-specific parameters
import sys

# Import FastAPI - web framework chính
# FastAPI: High-performance, dễ sử dụng, tự động validation
from fastapi import FastAPI, Request, status

# Import các middleware từ FastAPI
# CORSMiddleware: Cho phép cross-origin requests
from fastapi.middleware.cors import CORSMiddleware

# Import JSONResponse để trả về JSON format
from fastapi.responses import JSONResponse

# Import contextlib để tạo async context managers
from contextlib import asynccontextmanager

# Import các components từ core module
from src.core.config import settings, get_settings
from src.core.logging import setup_logging, get_logger, set_correlation_id
from src.core.database import connect_databases, disconnect_databases

# Import API routes
from src.api.routes import pipeline_management
from src.api.routes import pipeline_mongodb  # MongoDB pipeline (Bronze/Silver/Gold)
from src.api.routes import data_query
from src.api.routes import monitoring
from src.api.routes import health
from src.api.routes import admin
from src.api.routes import plugins  # Plugin system - dynamic sources
# from src.api.routes import pipeline_v2  # Commented out due to celery import error
from src.api.routes import auth

# ============================================
# LOGGING SETUP
# ============================================
# Cấu hình logging ngay khi module được load
# Đảm bảo logs có đúng format trước khi app khởi động

setup_logging(
    level=settings.log_level,
    indent=None,  # Compact JSON cho production
    format_json=True
)

# Tạo logger cho main module
logger = get_logger(__name__)


# ============================================
# LIFESPAN MANAGEMENT
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager để quản lý application lifecycle
    
    Lifespan hooks chạy:
    - Startup: Trước khi app bắt đầu nhận requests
    - Shutdown: Sau khi app dừng nhận requests, trước khi exit
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Control cho application execution
        
    Example:
        async with lifespan(app):
            # App running here
            await serve_requests()
    """
    
    # ========================================
    # STARTUP
    # ========================================
    logger.info("🚀 Starting up Smart Tourism Data Platform...")
    
    try:
        # Log cấu hình hiện tại (che giấu sensitive data)
        logger.info(
            "Configuration loaded",
            extra={
                "environment": settings.environment,
                "log_level": settings.log_level,
                "debug": settings.debug,
                "mongodb_host": settings.mongodb_host,
                "redis_host": settings.redis_host,
            }
        )
        
        # Kết nối databases
        # MongoDB và Redis cần được kết nối trước khi app nhận requests
        logger.info("Connecting to databases...")
        await connect_databases()
        logger.info("✅ Database connections established")
        
        # Tạo indexes cho MongoDB collections (nếu chưa có)
        # Indexes giúp tăng tốc queries
        logger.info("Setting up database indexes...")
        await _setup_database_indexes()
        logger.info("✅ Database indexes ready")
        
        # Khởi tạo plugin system
        # Dynamic plugin architecture cho data collectors
        logger.info("🔌 Initializing plugin system...")
        from src.plugins.registry import initialize_plugins
        await initialize_plugins()
        logger.info("✅ Plugin system ready")
        
        # Khởi tạo các background tasks nếu cần
        # Ví dụ: scheduled jobs, cleanup tasks
        logger.info("✅ Startup complete - Application ready")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        # Không raise exception để cho phép graceful degradation
        # Nhưng log lỗi để monitoring có thể phát hiện
    
    # Yield control cho application
    # App sẽ chạy ở đây cho đến khi nhận shutdown signal
    yield
    
    # ========================================
    # SHUTDOWN
    # ========================================
    logger.info("🛑 Shutting down Smart Tourism Data Platform...")
    
    try:
        # Đóng database connections
        logger.info("Closing database connections...")
        await disconnect_databases()
        logger.info("✅ Database connections closed")
        
        # Cleanup các resources khác nếu cần
        logger.info("✅ Shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}", exc_info=True)
        # Không raise exception để đảm bảo shutdown hoàn tất


async def _setup_database_indexes():
    """
    Tạo indexes cho MongoDB collections
    
    Indexes giúp tăng tốc queries và đảm bảo uniqueness
    Nên chạy một lần khi khởi động app
    
    Collections và indexes:
    - pipeline_execution: execution_id (unique), status, started_at
    - master_poi: poi_id (unique), location (2dsphere), city+category
    """
    from src.core.database import mongodb_manager
    
    # Lấy database instance
    db = mongodb_manager.get_database()
    
    # Pipeline execution indexes
    pipeline_collection = db.pipeline_execution
    await pipeline_collection.create_index("execution_id", unique=True)
    await pipeline_collection.create_index("status")
    await pipeline_collection.create_index("started_at")
    await pipeline_collection.create_index([("pipeline_name", 1), ("started_at", -1)])
    
    # Master POI indexes
    poi_collection = db.master_poi
    await poi_collection.create_index("poi_id", unique=True)
    await poi_collection.create_index([("location", "2dsphere")])  # Geospatial
    await poi_collection.create_index([("city", 1), ("category", 1)])
    await poi_collection.create_index("business_score")
    
    logger.info("Database indexes created/verified")


# ============================================
# FASTAPI APPLICATION
# ============================================
# Tạo FastAPI app với lifespan management
app = FastAPI(
    # Title cho OpenAPI documentation
    title="Smart Tourism Data Platform API",
    
    # Description cho OpenAPI
    description="""
    API cho Smart Tourism Data Platform - Hệ thống quản lý dữ liệu du lịch thông minh.
    
    ## Features
    
    * **Pipeline Management**: Điều khiển và giám sát data pipelines
    * **POI Data**: Quản lý Points of Interest data
    * **Real-time Monitoring**: Theo dõi pipeline execution real-time
    * **Data Quality**: Báo cáo chất lượng dữ liệu
    
    ## Authentication
    
    API sử dụng JWT Bearer token cho authentication.
    Thêm header: `Authorization: Bearer <token>`
    
    ## Rate Limiting
    
    60 requests/minute mỗi IP/user.
    """,
    
    # Version
    version="1.0.0",
    
    # Lifespan context manager
    lifespan=lifespan,
    
    # OpenAPI tags metadata
    openapi_tags=[
        {
            "name": "Pipeline Management",
            "description": "Operations cho pipeline lifecycle management",
        },
        {
            "name": "Data Query",
            "description": "POI data query và search operations",
        },
        {
            "name": "Monitoring",
            "description": "Health checks và system monitoring",
        },
        {
            "name": "Health",
            "description": "Health checks và readiness probes",
        },
    ],
    
    # Docs URLs
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
    openapi_url="/openapi.json",
)


# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

# CORS Middleware - Cho phép cross-origin requests
# Cần thiết cho frontend development và API consumption
cors_origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,           # Domains được phép
    allow_credentials=True,               # Cho phép cookies
    allow_methods=["*"],                  # Tất cả HTTP methods
    allow_headers=["*"],                  # Tất cả headers
    expose_headers=["X-Request-ID"],      # Headers expose cho client
)


# Request ID Middleware - Thêm correlation ID cho mỗi request
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """
    Middleware để thêm correlation ID cho mỗi HTTP request
    
    Correlation ID giúp trace một request qua toàn bộ hệ thống
    từ API → Service → Database và ngược lại
    
    Args:
        request: FastAPI Request object
        call_next: Function để gọi next middleware/route
        
    Returns:
        Response với X-Request-ID header
    """
    # Lấy correlation ID từ header hoặc tạo mới
    correlation_id = request.headers.get("X-Request-ID")
    if not correlation_id:
        import uuid
        correlation_id = str(uuid.uuid4())
    
    # Set correlation ID trong context
    set_correlation_id(correlation_id)
    
    # Log request bắt đầu
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Thêm correlation ID vào response headers
    response.headers["X-Request-ID"] = correlation_id
    
    # Log request kết thúc
    logger.info(
        f"Request completed: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        }
    )
    
    return response


# ============================================
# ROUTE REGISTRATION
# ============================================

# Đăng ký pipeline management routes
# Prefix: /api/v1/pipeline
app.include_router(pipeline_management.router)

# Đăng ký pipeline MongoDB routes (Bronze/Silver/Gold → MongoDB)
# Prefix: /api/v1/pipeline
app.include_router(pipeline_mongodb.router)

# Đăng ký pipeline v2 routes (sử dụng PipelineOrchestrator)
# Prefix: /api/v1/pipeline
# app.include_router(pipeline_v2.router)  # Commented out due to import error

# Đăng ký data query routes
# Prefix: /api/v1/data
print(f"DEBUG main.py: About to include data_query.router with id={id(data_query.router)}")
app.include_router(data_query.router)
print(f"DEBUG main.py: Included data_query.router, app routes count={len(app.routes)}")
# Print all routes
for i, route in enumerate(app.routes):
    if hasattr(route, 'path'):
        print(f"DEBUG: App route {i}: {route.path}")

# Đăng ký monitoring routes (public health endpoints)
# Routes: /health, /ready, /metrics
app.include_router(monitoring.router)

# Đăng ký health routes (legacy, có thể trùng lặp với monitoring)
# Nếu trùng lặp, monitoring sẽ được ưu tiên
app.include_router(health.router)

# Đăng ký admin routes
# Prefix: /api/v1/admin
# Requires: Admin role
app.include_router(admin.router)

# Đăng ký auth routes
# Prefix: /api/v1/auth
# Routes: /login, /register, /refresh, /me
app.include_router(auth.router)

# Đăng ký plugin management routes
# Prefix: /api/v1/plugins
# Routes: /plugins, /plugins/sources, /plugins/{id}/test
app.include_router(plugins.router)


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - Thông tin cơ bản về API
    
    Returns:
        JSON với thông tin ứng dụng
    """
    return {
        "name": "Smart Tourism Data Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint cho monitoring và load balancers
    
    Returns:
        200 OK nếu tất cả services healthy
        503 Service Unavailable nếu có vấn đề
    """
    from src.core.database import mongodb_manager, redis_manager
    
    health_status = {
        "state": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check MongoDB
    try:
        if mongodb_manager.is_connected:
            health_status["services"]["mongodb"] = "connected"
        else:
            health_status["services"]["mongodb"] = "disconnected"
            health_status["state"] = "unhealthy"
    except Exception as e:
        health_status["services"]["mongodb"] = f"error: {str(e)}"
        health_status["state"] = "unhealthy"
    
    # Check Redis
    try:
        if redis_manager.is_connected:
            health_status["services"]["redis"] = "connected"
        else:
            health_status["services"]["redis"] = "disconnected"
            health_status["state"] = "unhealthy"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["state"] = "unhealthy"
    
    # Return response
    if health_status["state"] == "healthy":
        return health_status
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check endpoint cho Kubernetes
    
    Returns:
        200 OK nếu app sẵn sàng nhận traffic
    """
    from fastapi import status as http_status
    from src.core.database import mongodb_manager
    
    if mongodb_manager.is_connected:
        return {"ready": True}
    else:
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "reason": "Database not connected"}
        )


# ============================================
# GLOBAL EXCEPTION HANDLERS
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler cho tất cả unhandled exceptions
    
    Log lỗi và trả về response phù hợp mà không expose internal details
    
    Args:
        request: Request object
        exc: Exception instance
        
    Returns:
        JSONResponse với error message
    """
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True
    )
    
    # Trong production, không expose internal error details
    if settings.environment == "production":
        message = "Internal server error"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": message,
            "type": type(exc).__name__
        }
    )


# ============================================
# MODULE IMPORTS (đặt ở cuối để tránh circular imports)
# ============================================
from datetime import datetime, timezone


# ============================================
# MAIN ENTRY POINT (cho development)
# ============================================
if __name__ == "__main__":
    """
    Entry point khi chạy trực tiếp: python src/main.py
    
    Chỉ dùng cho development. Trong production, dùng:
    - uvicorn src.main:app
    - gunicorn với uvicorn workers
    """
    import uvicorn
    
    logger.info("Starting development server...")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,           # Auto-reload khi code thay đổi
        log_level="info",
    )
