"""
Pipeline Celery Tasks
=====================

Celery tasks cho pipeline execution.
Được gọi bởi Celery Beat scheduler hoặc API endpoints.

Tasks:
- run_pipeline: Chạy full pipeline cho một city
- run_bronze_pipeline: Chỉ chạy bronze stage
- run_silver_pipeline: Chỉ chạy silver stage
- run_gold_pipeline: Chỉ chạy gold stage
- cleanup_old_data: Cleanup data cũ
"""

import asyncio
import logging
from typing import List, Optional

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from src.pipelines.orchestration import PipelineOrchestrator
from src.pipelines.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


def get_orchestrator():
    """Get pipeline orchestrator instance."""
    return PipelineOrchestrator()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def run_pipeline(
    self,
    city: str,
    poi_types: Optional[List[str]] = None,
    skip_bronze: bool = False,
    skip_silver: bool = False,
    skip_gold: bool = False
):
    """
    Chạy full pipeline cho một city.
    
    Args:
        city: Tên thành phố
        poi_types: Danh sách POI types (None = all)
        skip_bronze: Skip bronze stage
        skip_silver: Skip silver stage
        skip_gold: Skip gold stage
        
    Returns:
        Dict với execution result
    """
    logger.info(f"Starting pipeline task for {city}")
    
    try:
        orchestrator = get_orchestrator()
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(orchestrator.run_full_pipeline(
            city=city,
            poi_types=poi_types,
            skip_bronze=skip_bronze,
            skip_silver=skip_silver,
            skip_gold=skip_gold
        ))
        
        if result.status.value == "completed":
            logger.info(f"Pipeline completed for {city}: {result.execution_id}")
            return {
                "status": "success",
                "execution_id": result.execution_id,
                "city": result.city,
                "records_processed": result.records_processed,
                "metrics": result.metrics
            }
        else:
            error_msg = result.error_message or "Unknown error"
            logger.error(f"Pipeline failed for {city}: {error_msg}")
            
            # Retry if not exceeded max retries
            if self.request.retries < self.max_retries:
                raise self.retry(exc=Exception(error_msg))
            
            return {
                "status": "failed",
                "execution_id": result.execution_id,
                "city": result.city,
                "error": error_msg
            }
    
    except MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for {city}")
        return {
            "status": "failed",
            "city": city,
            "error": "Max retries exceeded"
        }
    
    except Exception as e:
        logger.exception(f"Pipeline task error for {city}: {e}")
        
        # Retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        return {
            "status": "failed",
            "city": city,
            "error": str(e)
        }


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def run_bronze_pipeline(
    self,
    city: str,
    poi_types: Optional[List[str]] = None
):
    """Chạy bronze pipeline task."""
    logger.info(f"Starting bronze pipeline task for {city}")
    
    try:
        orchestrator = get_orchestrator()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(orchestrator.run_bronze_pipeline(
            city=city,
            poi_types=poi_types
        ))
        
        if result.status.value == "completed":
            return {
                "status": "success",
                "execution_id": result.execution_id,
                "stage": "bronze",
                "records_collected": result.records_processed
            }
        else:
            raise Exception(result.error_message or "Bronze pipeline failed")
    
    except Exception as e:
        logger.exception(f"Bronze pipeline error: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {
            "status": "failed",
            "city": city,
            "stage": "bronze",
            "error": str(e)
        }


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30
)
def run_silver_pipeline(self, city: str):
    """Chạy silver pipeline task."""
    logger.info(f"Starting silver pipeline task for {city}")
    
    try:
        orchestrator = get_orchestrator()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(orchestrator.run_silver_pipeline(city=city))
        
        if result.status.value == "completed":
            return {
                "status": "success",
                "execution_id": result.execution_id,
                "stage": "silver",
                "records_processed": result.records_processed,
                "quality_score": result.metrics.get("quality_score")
            }
        else:
            raise Exception(result.error_message or "Silver pipeline failed")
    
    except Exception as e:
        logger.exception(f"Silver pipeline error: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {
            "status": "failed",
            "city": city,
            "stage": "silver",
            "error": str(e)
        }


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30
)
def run_gold_pipeline(self, city: str):
    """Chạy gold pipeline task."""
    logger.info(f"Starting gold pipeline task for {city}")
    
    try:
        orchestrator = get_orchestrator()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(orchestrator.run_gold_pipeline(city=city))
        
        if result.status.value == "completed":
            return {
                "status": "success",
                "execution_id": result.execution_id,
                "stage": "gold",
                "records_aggregated": result.records_processed
            }
        else:
            raise Exception(result.error_message or "Gold pipeline failed")
    
    except Exception as e:
        logger.exception(f"Gold pipeline error: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {
            "status": "failed",
            "city": city,
            "stage": "gold",
            "error": str(e)
        }


@shared_task
def cleanup_old_data(max_age_days: int = 30):
    """Cleanup old pipeline data."""
    logger.info(f"Starting cleanup task (max_age={max_age_days} days)")
    
    try:
        orchestrator = get_orchestrator()
        loop = asyncio.get_event_loop()
        
        # Cleanup old executions
        exec_count = loop.run_until_complete(
            orchestrator.cleanup_old_executions(days=max_age_days)
        )
        
        # Cleanup old metrics
        metrics = MetricsCollector()
        metrics_count = metrics.cleanup_old_metrics(max_age_hours=max_age_days * 24)
        
        return {
            "status": "success",
            "executions_cleaned": exec_count,
            "metrics_cleaned": metrics_count
        }
    
    except Exception as e:
        logger.exception(f"Cleanup error: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


@shared_task
def collect_all_cities():
    """Collect data cho tất cả configured cities."""
    from src.core.config import settings
    
    # Get cities từ config
    cities = getattr(settings, 'target_cities', ['hanoi', 'hochiminh', 'danang'])
    
    logger.info(f"Starting collection for {len(cities)} cities: {cities}")
    
    results = []
    for city in cities:
        try:
            # Trigger pipeline task
            result = run_pipeline.delay(city=city)
            results.append({
                "city": city,
                "task_id": result.id,
                "status": "queued"
            })
        except Exception as e:
            logger.error(f"Failed to queue pipeline for {city}: {e}")
            results.append({
                "city": city,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "status": "success",
        "cities_queued": len([r for r in results if r["status"] == "queued"]),
        "results": results
    }
