"""
Fix #4: PipelineService — sửa SQLAlchemy usage.
- Dùng text() thay vì raw string
- Dùng execute() thay vì fetch() (fetch là của asyncpg, không phải SQLAlchemy)
- Dùng :param thay vì $1 placeholder
- Fix background task session lifecycle
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
import uuid
import logging
from typing import List, Optional

from app.api.dependencies.database import async_session

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_pipeline_run(self, city: str, sources: List[str]) -> str:
        run_id = str(uuid.uuid4())
        sources_str = ",".join(sources)

        await self.db.execute(
            text(
                """
                INSERT INTO pipeline_runs (id, city, sources, status, started_at)
                VALUES (:id, :city, :sources, 'running', :started_at)
                """
            ),
            {
                "id": run_id,
                "city": city,
                "sources": sources_str,
                "started_at": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        logger.info(f"Pipeline run {run_id} started for city={city}")
        return run_id

    async def execute_pipeline_run(self, run_id: str):
        """Background task: Execute the pipeline and update status."""
        # Create new session for background task to avoid request-scoped session leak
        async with async_session() as session:
            try:
                # TODO: Trigger Airflow DAG here via REST API
                # For now, mark as completed
                await session.execute(
                    text(
                        """
                        UPDATE pipeline_runs
                        SET status = 'completed', completed_at = :completed_at
                        WHERE id = :id
                        """
                    ),
                    {
                        "completed_at": datetime.now(timezone.utc),
                        "id": run_id,
                    },
                )
                await session.commit()
                logger.info(f"Pipeline run {run_id} completed")
            except Exception as e:
                logger.error(f"Pipeline run {run_id} failed: {e}")
                await session.execute(
                    text(
                        "UPDATE pipeline_runs SET status = 'failed' WHERE id = :id"
                    ),
                    {"id": run_id},
                )
                await session.commit()

    async def get_pipeline_runs(self, city: Optional[str] = None) -> List[dict]:
        if city:
            result = await self.db.execute(
                text(
                    "SELECT * FROM pipeline_runs WHERE city = :city ORDER BY started_at DESC"
                ),
                {"city": city},
            )
        else:
            result = await self.db.execute(
                text(
                    "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 50"
                )
            )

        rows = result.mappings().all()
        return [dict(row) for row in rows]