from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import logging

from app.api.dependencies.database import get_mongo_client
from app.api.schemas.pipeline import PipelineRunRequest, PipelineRunResponse
from app.services.pipeline_service import PipelineService
from app.core.background_tasks import create_background_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)
):
    """
    Start a new pipeline run.
    
    PATTERN: Background task runs independently, not tied to request scope.
    - service.start_pipeline_run() uses request-scoped session: OK (synchronous)
    - service.execute_pipeline_run() creates its own session: OK (async background)
    - asyncio.create_task() with proper tracking: OK (graceful shutdown)
    """
    service = PipelineService(mongo_client)
    run_id = await service.start_pipeline_run(request.city, request.sources)

    # Schedule background execution WITHOUT passing request-scoped session
    # The service's execute_pipeline_run creates its own session independently
    create_background_task(
        service.execute_pipeline_run(run_id),
        name=f"pipeline_execute_{run_id}",
        error_callback=lambda e: logger.error(f"Pipeline {run_id} failed: {e}")
    )

    return PipelineRunResponse(run_id=run_id, status="started")

@router.get("/pipeline/runs", response_model=List[dict])
async def get_pipeline_runs(
    city: Optional[str] = None,
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)
):
    service = PipelineService(mongo_client)
    return await service.get_pipeline_runs(city)