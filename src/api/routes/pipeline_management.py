"""
Pipeline Management API Routes
================================
API endpoints cho pipeline lifecycle management
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section II

Mục đích:
- Cung cấp REST API cho pipeline control (start, stop, pause, resume, restart)
- Theo dõi real-time pipeline status và progress
- Truy xuất execution history và metrics
- Quản lý errors và data quality reports

Base Path: /api/v1/pipeline
Authentication: JWT Bearer token (optional cho một số endpoints)
Rate Limiting: 60 requests/minute

Endpoints:
- POST /start              - Khởi động pipeline
- POST /stop/{id}          - Dừng pipeline
- POST /pause/{id}         - Tạm dừng pipeline
- POST /resume/{id}        - Tiếp tục pipeline
- POST /restart/{id}       - Khởi động lại pipeline
- GET  /status/{id}        - Lấy trạng thái pipeline
- GET  /active             - Danh sách pipeline đang chạy
- GET  /history            - Lịch sử executions
- GET  /dashboard          - Dashboard data
- GET  /metrics            - Performance metrics
- GET  /errors             - Error list
- GET  /data-quality       - Quality report
- POST /cleanup            - Dọn dẹp resources
- GET  /health             - Health check
"""

# Import asyncio để hỗ trợ async operations
import asyncio

# Import logging để ghi lại API operations
import logging

# Import datetime classes để xử lý timestamps
from datetime import datetime, timezone

# Import type hints
from typing import Dict, List, Any, Optional

# Import FastAPI components
# APIRouter: Tạo modular routes
# HTTPException: Raise HTTP errors
# BackgroundTasks: Chạy tasks async sau khi response
# Depends: Dependency injection
# Query: Query parameter validation
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query

# Import JSONResponse để trả về JSON format
from fastapi.responses import JSONResponse

# Import dependencies từ src.api.dependencies
# get_current_user: Xác thực JWT token
# get_mongo_client: Lấy MongoDB client
# get_redis_client: Lấy Redis client
from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_mongo_client, get_redis_client

# Import PipelineManagementService từ services
# Service layer xử lý business logic
from src.services.pipeline_management_service import PipelineManagementService

# Import Pydantic schemas cho request/response validation
# Các schemas định nghĩa trong src/api/schemas/pipeline_management.py
from src.api.schemas.pipeline_management import (
    PipelineExecutionRequest,     # Request model cho start pipeline
    PipelineExecutionResponse,   # Response model cho execution
    PipelineStatusResponse,       # Response model cho status
    PipelineHistoryResponse,     # Response model cho history
    PipelineControlRequest,       # Request model cho control actions
    PipelineDashboardResponse,   # Response model cho dashboard
    PipelineMetricsResponse,     # Response model cho metrics
    DataQualityReport,           # Response model cho quality report
)

# Tạo logger cho module này
# Logs sẽ có format: {"timestamp": "...", "level": "...", "logger": "src.api.routes.pipeline_management", ...}
logger = logging.getLogger(__name__)

# Tạo APIRouter với prefix và tags
# Prefix: /api/v1/pipeline - tất cả endpoints trong router này sẽ có prefix này
# Tags: ["Pipeline Management"] - cho OpenAPI documentation và grouping
router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["Pipeline Management"]
)


@router.post("/start", response_model=PipelineExecutionResponse)
async def start_pipeline(
    request: PipelineExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Khởi động pipeline execution
    - Full sync: Đồng bộ toàn bộ dữ liệu
    - Incremental sync: Đồng bộ dữ liệu mới
    - Specific city/category: Đồng bộ theo target
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        # Validate request - only require cities/categories for incremental_sync
        if request.execution_type == "incremental_sync" and not request.cities and not request.categories:
            raise HTTPException(
                status_code=400,
                detail="Phải cung cấp ít nhất một city hoặc category cho incremental_sync"
            )
        
        # Start pipeline execution
        execution_id = await pipeline_service.start_pipeline(
            cities=request.cities or [],
            categories=request.categories or [],
            execution_type=request.execution_type,
            background_tasks=background_tasks,
            user_id=current_user
        )
        
        logger.info(f"🚀 Pipeline started: {execution_id}")
        
        return PipelineExecutionResponse(
            execution_id=execution_id,
            status="started",
            message="Pipeline execution started successfully",
            started_at=datetime.now(timezone.utc),
            cities=request.cities,
            categories=request.categories,
            execution_type=request.execution_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi khởi động pipeline: {str(e)}"
        )


@router.post("/stop/{execution_id}", response_model=Dict[str, Any])
async def stop_pipeline(
    execution_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Dừng pipeline execution
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        success = await pipeline_service.stop_pipeline(
            execution_id=execution_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline execution {execution_id} không tìm thấy hoặc không thể dừng"
            )
        
        logger.info(f"⏹️ Pipeline stopped: {execution_id}")
        
        return {
            "execution_id": execution_id,
            "status": "stopped",
            "message": "Pipeline execution stopped successfully",
            "stopped_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error stopping pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi dừng pipeline: {str(e)}"
        )


@router.post("/pause/{execution_id}", response_model=Dict[str, Any])
async def pause_pipeline(
    execution_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Tạm dừng pipeline execution
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        success = await pipeline_service.pause_pipeline(
            execution_id=execution_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline execution {execution_id} không tìm thấy hoặc không thể tạm dừng"
            )
        
        logger.info(f"⏸️ Pipeline paused: {execution_id}")
        
        return {
            "execution_id": execution_id,
            "status": "paused",
            "message": "Pipeline execution paused successfully",
            "paused_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error pausing pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạm dừng pipeline: {str(e)}"
        )


@router.post("/resume/{execution_id}", response_model=Dict[str, Any])
async def resume_pipeline(
    execution_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Tiếp tục pipeline execution đã tạm dừng
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        success = await pipeline_service.resume_pipeline(
            execution_id=execution_id,
            user_id=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline execution {execution_id} không tìm thấy hoặc không thể tiếp tục"
            )
        
        logger.info(f"▶️ Pipeline resumed: {execution_id}")
        
        return {
            "execution_id": execution_id,
            "status": "running",
            "message": "Pipeline execution resumed successfully",
            "resumed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resuming pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tiếp tục pipeline: {str(e)}"
        )


@router.post("/restart/{execution_id}", response_model=PipelineExecutionResponse)
async def restart_pipeline(
    execution_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Khởi động lại pipeline execution đã thất bại
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        new_execution_id = await pipeline_service.restart_pipeline(
            execution_id=execution_id,
            background_tasks=background_tasks,
            user_id=current_user
        )
        
        if not new_execution_id:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline execution {execution_id} không tìm thấy hoặc không thể khởi động lại"
            )
        
        logger.info(f"🔄 Pipeline restarted: {execution_id} -> {new_execution_id}")
        
        return PipelineExecutionResponse(
            execution_id=new_execution_id,
            status="started",
            message="Pipeline execution restarted successfully",
            started_at=datetime.now(timezone.utc),
            execution_type="restart",
            original_execution_id=execution_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error restarting pipeline: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi khởi động lại pipeline: {str(e)}"
        )


@router.get("/status/{execution_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    execution_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy trạng thái chi tiết của pipeline execution
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        status = await pipeline_service.get_pipeline_status(execution_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline execution {execution_id} không tìm thấy"
            )
        
        return PipelineStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting pipeline status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy trạng thái pipeline: {str(e)}"
        )


@router.get("/active", response_model=List[PipelineStatusResponse])
async def get_active_pipelines(
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy danh sách các pipeline đang chạy
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        active_pipelines = await pipeline_service.get_active_pipelines()
        
        return [PipelineStatusResponse(**pipeline) for pipeline in active_pipelines]
        
    except Exception as e:
        logger.error(f"❌ Error getting active pipelines: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách pipeline đang chạy: {str(e)}"
        )


@router.get("/history", response_model=PipelineHistoryResponse)
async def get_pipeline_history(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy lịch sử pipeline execution với filtering và pagination
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        history = await pipeline_service.get_pipeline_history(
            limit=limit,
            offset=offset,
            city=city,
            category=category,
            status=status
        )
        
        return PipelineHistoryResponse(
            executions=history["executions"],
            total_count=history["total_count"],
            limit=limit,
            offset=offset,
            has_more=history["has_more"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy lịch sử pipeline: {str(e)}"
        )


@router.get("/dashboard", response_model=PipelineDashboardResponse)
async def get_pipeline_dashboard(
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy dashboard data cho pipeline monitoring
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        dashboard_data = await pipeline_service.get_dashboard_data()
        
        return PipelineDashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy dashboard data: {str(e)}"
        )


@router.get("/metrics", response_model=PipelineMetricsResponse)
async def get_pipeline_metrics(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy pipeline metrics cho monitoring
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        metrics = await pipeline_service.get_pipeline_metrics(time_range)
        
        return PipelineMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy pipeline metrics: {str(e)}"
        )


@router.get("/errors", response_model=List[Dict[str, Any]])
async def get_pipeline_errors(
    limit: int = Query(50, ge=1, le=1000),
    severity: Optional[str] = Query(None, description="Error severity: critical, error, warning"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy danh sách errors từ pipeline executions
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        errors = await pipeline_service.get_pipeline_errors(
            limit=limit,
            severity=severity
        )
        
        return errors
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline errors: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy pipeline errors: {str(e)}"
        )


@router.get("/data-quality", response_model=Dict[str, Any])
async def get_data_quality_report(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Lấy data quality report
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        quality_report = await pipeline_service.get_data_quality_report(time_range)
        
        return quality_report
        
    except Exception as e:
        logger.error(f"❌ Error getting data quality report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy data quality report: {str(e)}"
        )


@router.delete("/cleanup", response_model=Dict[str, Any])
async def cleanup_pipeline_resources(
    older_than_days: int = Query(30, ge=1, le=365, description="Cleanup resources older than X days"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Dọn dẹp pipeline resources cũ
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        cleanup_result = await pipeline_service.cleanup_resources(
            older_than_days=older_than_days,
            user_id=current_user
        )
        
        logger.info(f"🧹 Pipeline cleanup completed: {cleanup_result}")
        
        return {
            "message": "Pipeline cleanup completed successfully",
            "cleaned_resources": cleanup_result,
            "cleanup_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error during pipeline cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi dọn dẹp pipeline resources: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_pipeline_health(
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client),
    redis_client = Depends(get_redis_client)
):
    """
    Health check cho pipeline management system
    """
    try:
        pipeline_service = PipelineManagementService(mongo_client, redis_client)
        
        health_status = await pipeline_service.get_system_health()
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/status", summary="Get Pipeline System Status")
async def get_pipeline_system_status(
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Lấy trạng thái tổng quan của pipeline system.
    """
    try:
        # Lấy thống kê từ database
        db = mongo_client.smart_travel
        
        # Đếm số executions
        total_executions = await db.pipeline_executions.count_documents({})
        active_executions = await db.pipeline_executions.count_documents({"status": "running"})
        completed_executions = await db.pipeline_executions.count_documents({"status": "completed"})
        failed_executions = await db.pipeline_executions.count_documents({"status": "failed"})
        
        return {
            "status": "healthy",
            "executions": {
                "total": total_executions,
                "active": active_executions,
                "completed": completed_executions,
                "failed": failed_executions
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline system status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy trạng thái pipeline: {str(e)}"
        )
