"""
Pipeline Management API (v2)
============================

Sử dụng PipelineOrchestrator từ src/pipelines/

API endpoints cho pipeline lifecycle management:
- Start/Stop/Pause/Resume pipeline
- Get pipeline status và execution history
- Dashboard và metrics
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import status
from typing import List, Optional
from datetime import datetime
import logging

from src.api.dependencies.auth import get_current_active_user, get_current_admin_user
from src.api.dependencies.database import get_database
from src.pipelines.orchestration import PipelineOrchestrator, PipelineScheduler
from src.pipelines.orchestration.pipeline_orchestrator import PipelineStage, PipelineStatus
from src.pipelines.tasks import run_pipeline, run_bronze_pipeline, run_silver_pipeline, run_gold_pipeline
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["Pipeline Management"]
)

# Shared orchestrator instance
_orchestrator: Optional[PipelineOrchestrator] = None
_scheduler: Optional[PipelineScheduler] = None


def get_orchestrator() -> PipelineOrchestrator:
    """Get or create orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator


def get_scheduler() -> PipelineScheduler:
    """Get or create scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = PipelineScheduler(get_orchestrator())
    return _scheduler


@router.post("/start", summary="Start Pipeline")
async def start_pipeline(
    city: str,
    poi_types: Optional[List[str]] = None,
    skip_bronze: bool = False,
    skip_silver: bool = False,
    skip_gold: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: str = Depends(get_current_active_user)
):
    """Start pipeline cho một city."""
    logger.info(f"Starting pipeline for {city} (user={current_user})")
    
    try:
        orchestrator = get_orchestrator()
        
        # Start in background
        import asyncio
        asyncio.create_task(orchestrator.run_full_pipeline(
            city=city,
            poi_types=poi_types,
            skip_bronze=skip_bronze,
            skip_silver=skip_silver,
            skip_gold=skip_gold
        ))
        
        return {
            "status": "started",
            "city": city,
            "message": f"Pipeline started for {city}"
        }
    
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start pipeline: {str(e)}"
        )


@router.get("/active", summary="Get Active Pipelines")
async def get_active_pipelines(
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy danh sách active pipelines."""
    try:
        orchestrator = get_orchestrator()
        
        # Get running executions
        executions = orchestrator.get_executions(
            status=PipelineStatus.RUNNING,
            limit=50
        )
        
        return {
            "active_count": len(executions),
            "pipelines": [
                {
                    "execution_id": e.execution_id,
                    "city": e.city,
                    "stage": e.stage.value,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "records_processed": e.records_processed
                }
                for e in executions
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get active pipelines: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active pipelines: {str(e)}"
        )


@router.get("/history", summary="Get Pipeline History")
async def get_pipeline_history(
    city: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 50,
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy lịch sử pipeline executions."""
    try:
        orchestrator = get_orchestrator()
        
        # Parse stage
        stage_enum = None
        if stage:
            try:
                stage_enum = PipelineStage(stage)
            except ValueError:
                pass
        
        executions = orchestrator.get_executions(
            city=city,
            stage=stage_enum,
            limit=limit
        )
        
        return {
            "total": len(executions),
            "executions": [
                {
                    "execution_id": e.execution_id,
                    "city": e.city,
                    "stage": e.stage.value,
                    "status": e.status.value,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "records_processed": e.records_processed,
                    "error": e.error_message
                }
                for e in executions
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get pipeline history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


@router.get("/dashboard", summary="Get Pipeline Dashboard")
async def get_pipeline_dashboard(
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy pipeline dashboard data."""
    try:
        orchestrator = get_orchestrator()
        
        # Get recent executions
        executions = orchestrator.get_executions(limit=100)
        
        # Calculate stats
        total = len(executions)
        completed = sum(1 for e in executions if e.status == PipelineStatus.COMPLETED)
        failed = sum(1 for e in executions if e.status == PipelineStatus.FAILED)
        running = sum(1 for e in executions if e.status == PipelineStatus.RUNNING)
        
        # Get unique cities
        cities = list(set(e.city for e in executions))
        
        return {
            "stats": {
                "total_executions": total,
                "completed": completed,
                "failed": failed,
                "running": running,
                "success_rate": round(completed / total * 100, 1) if total > 0 else 0
            },
            "cities": cities,
            "recent_executions": [
                {
                    "execution_id": e.execution_id,
                    "city": e.city,
                    "stage": e.stage.value,
                    "status": e.status.value,
                    "records": e.records_processed
                }
                for e in executions[:10]
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get("/status/{execution_id}", summary="Get Pipeline Status")
async def get_pipeline_status(
    execution_id: str,
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy status của một pipeline execution."""
    try:
        orchestrator = get_orchestrator()
        execution = orchestrator.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        return {
            "execution_id": execution.execution_id,
            "city": execution.city,
            "stage": execution.stage.value,
            "status": execution.status.value,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "records_processed": execution.records_processed,
            "metrics": execution.metrics,
            "error": execution.error_message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/metrics", summary="Get Pipeline Metrics")
async def get_pipeline_metrics(
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy pipeline metrics."""
    try:
        from src.pipelines.monitoring import MetricsCollector
        
        metrics = MetricsCollector()
        summary = metrics.get_summary()
        
        return summary
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/data-quality", summary="Get Data Quality Report")
async def get_data_quality(
    city: str,
    current_user: Optional[str] = Depends(get_current_active_user)
):
    """Lấy data quality report cho city."""
    try:
        from src.pipelines.monitoring import QualityMonitor
        
        monitor = QualityMonitor()
        report = monitor.get_latest_report(city, "silver")
        
        if not report:
            return {
                "city": city,
                "status": "no_data",
                "message": "No quality report available"
            }
        
        return {
            "city": report.city,
            "stage": report.stage,
            "overall_score": round(report.overall_score, 3),
            "dimension_scores": {
                k: {
                    "score": round(v.score, 3),
                    "issues_count": len(v.issues)
                }
                for k, v in report.dimension_scores.items()
            },
            "record_count": report.record_count,
            "recommendations": report.recommendations,
            "timestamp": report.timestamp.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to get quality report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality report: {str(e)}"
        )
