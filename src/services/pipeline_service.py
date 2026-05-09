"""
PipelineService — xử lý pipeline data với MongoDB.
Chuyển từ PostgreSQL sang MongoDB cho consistency.
"""
from datetime import datetime, timezone
import uuid
import logging
from typing import List, Optional

from app.api.dependencies.database import get_mongo_client

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, mongo_client):
        self.mongo_client = mongo_client

    async def start_pipeline_run(self, city: str, sources: List[str]) -> str:
        run_id = str(uuid.uuid4())
        sources_str = ",".join(sources)

        # Lưu pipeline run vào MongoDB
        db = self.mongo_client.smart_travel
        await db.pipeline_runs.insert_one({
            "_id": run_id,
            "city": city,
            "sources": sources_str,
            "status": "running",
            "started_at": datetime.now(timezone.utc),
        })
        logger.info(f"Pipeline run {run_id} started for city={city}")
        return run_id

    async def execute_pipeline_run(self, run_id: str):
        """Background task: Execute the pipeline and update status."""
        db = self.mongo_client.smart_travel
        try:
            # TODO: Trigger Airflow DAG here via REST API
            # For now, mark as completed
            await db.pipeline_runs.update_one(
                {"_id": run_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            logger.info(f"Pipeline run {run_id} completed")
        except Exception as e:
            await db.pipeline_runs.update_one(
                {"_id": run_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            logger.error(f"Pipeline run {run_id} failed: {e}")

    async def get_pipeline_runs(self, city: Optional[str] = None) -> List[dict]:
        db = self.mongo_client.smart_travel
        if city:
            cursor = db.pipeline_runs.find({"city": city}).sort("started_at", -1)
        else:
            cursor = db.pipeline_runs.find().sort("started_at", -1).limit(50)
        
        runs = []
        async for document in cursor:
            # Convert ObjectId to string for JSON serialization
            doc = dict(document)
            doc["_id"] = str(document["_id"])
            runs.append(doc)
        
        return runs