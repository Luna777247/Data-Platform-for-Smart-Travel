"""
Pipeline Repository
===================

Repository cho pipeline data access.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/db/repositories/pipeline_repository.py
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class PipelineRepository:
    """
    Repository cho pipeline execution data.
    
    Provides CRUD operations cho:
    - Pipeline executions
    - Pipeline configurations
    - Execution logs
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.COLLECTION = "pipeline_executions"
        self.CONFIG_COLLECTION = "pipeline_configs"
        logger.info("PipelineRepository initialized")
    
    async def create_execution(
        self,
        execution_id: str,
        city: str,
        stage: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create pipeline execution record."""
        if not self.db:
            return False
        
        try:
            doc = {
                "execution_id": execution_id,
                "city": city,
                "stage": stage,
                "status": status,
                "started_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            await self.db[self.COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to create execution: {e}")
            return False
    
    async def update_execution(
        self,
        execution_id: str,
        status: str,
        records_processed: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Update pipeline execution."""
        if not self.db:
            return False
        
        try:
            update = {
                "status": status,
                "completed_at": datetime.utcnow().isoformat() if status in ["completed", "failed"] else None,
                "records_processed": records_processed
            }
            
            if error_message:
                update["error_message"] = error_message
            
            await self.db[self.COLLECTION].update_one(
                {"execution_id": execution_id},
                {"$set": update}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update execution: {e}")
            return False
    
    async def get_execution(
        self,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get execution by ID."""
        if not self.db:
            return None
        
        return await self.db[self.COLLECTION].find_one(
            {"execution_id": execution_id}
        )
    
    async def get_executions(
        self,
        city: Optional[str] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get executions with filters."""
        if not self.db:
            return []
        
        query = {}
        if city:
            query["city"] = city
        if stage:
            query["stage"] = stage
        if status:
            query["status"] = status
        
        cursor = self.db[self.COLLECTION].find(query).sort(
            "started_at", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def delete_old_executions(self, days: int = 30) -> int:
        """Delete executions older than specified days."""
        if not self.db:
            return 0
        
        try:
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            result = await self.db[self.COLLECTION].delete_many({
                "started_at": {"$lt": cutoff.isoformat()}
            })
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old executions: {e}")
            return 0
