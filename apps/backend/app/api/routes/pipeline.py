from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.dependencies.database import get_db
from app.api.schemas.pipeline import PipelineRunRequest, PipelineRunResponse
from app.services.pipeline_service import PipelineService

router = APIRouter()

@router.post("/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    service = PipelineService(db)
    run_id = await service.start_pipeline_run(request.city, request.sources)

    # Run in background
    background_tasks.add_task(service.execute_pipeline_run, run_id)

    return PipelineRunResponse(run_id=run_id, status="started")

@router.get("/pipeline/runs", response_model=List[dict])
async def get_pipeline_runs(
    city: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    service = PipelineService(db)
    return await service.get_pipeline_runs(city)