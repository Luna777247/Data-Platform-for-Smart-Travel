"""
Quality Repository
==================

Repository cho data quality management.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/db/repositories/quality_repository.py
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class QualityRepository:
    """
    Repository cho quality management data.
    
    Provides CRUD operations cho:
    - Quality reports
    - Quality rules
    - Quality issues
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.REPORTS_COLLECTION = "quality_reports"
        self.RULES_COLLECTION = "quality_rules"
        self.ISSUES_COLLECTION = "quality_issues"
        logger.info("QualityRepository initialized")
    
    async def store_quality_report(
        self,
        report_id: str,
        city: str,
        layer: str,
        overall_score: float,
        dimension_scores: Dict[str, Any],
        total_records: int,
        recommendations: List[str]
    ) -> bool:
        """Store quality report."""
        if not self.db:
            return False
        
        try:
            doc = {
                "report_id": report_id,
                "timestamp": datetime.utcnow().isoformat(),
                "city": city,
                "layer": layer,
                "overall_score": overall_score,
                "dimension_scores": dimension_scores,
                "total_records": total_records,
                "recommendations": recommendations
            }
            
            await self.db[self.REPORTS_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to store quality report: {e}")
            return False
    
    async def get_quality_report(
        self,
        report_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get quality report by ID."""
        if not self.db:
            return None
        
        return await self.db[self.REPORTS_COLLECTION].find_one(
            {"report_id": report_id}
        )
    
    async def get_latest_quality_report(
        self,
        city: str,
        layer: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest quality report for city/layer."""
        if not self.db:
            return None
        
        cursor = self.db[self.REPORTS_COLLECTION].find(
            {"city": city, "layer": layer}
        ).sort("timestamp", -1).limit(1)
        
        reports = await cursor.to_list(length=1)
        return reports[0] if reports else None
    
    async def get_quality_reports(
        self,
        city: Optional[str] = None,
        layer: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get quality reports with filters."""
        if not self.db:
            return []
        
        query = {}
        if city:
            query["city"] = city
        if layer:
            query["layer"] = layer
        if since:
            query["timestamp"] = {"$gte": since.isoformat()}
        
        cursor = self.db[self.REPORTS_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def create_quality_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        layer: str,
        field: str,
        rule_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ) -> bool:
        """Create quality validation rule."""
        if not self.db:
            return False
        
        try:
            doc = {
                "rule_id": rule_id,
                "name": name,
                "description": description,
                "layer": layer,
                "field": field,
                "rule_type": rule_type,
                "parameters": parameters or {},
                "severity": severity,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self.db[self.RULES_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to create quality rule: {e}")
            return False
    
    async def get_quality_rules(
        self,
        layer: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get quality rules with filters."""
        if not self.db:
            return []
        
        query = {}
        if layer:
            query["layer"] = layer
        if is_active is not None:
            query["is_active"] = is_active
        
        cursor = self.db[self.RULES_COLLECTION].find(query)
        return await cursor.to_list(length=1000)
    
    async def create_quality_issue(
        self,
        issue_id: str,
        city: str,
        layer: str,
        rule_id: str,
        record_id: str,
        field: str,
        issue_type: str,
        message: str,
        severity: str = "error"
    ) -> bool:
        """Create quality issue."""
        if not self.db:
            return False
        
        try:
            doc = {
                "issue_id": issue_id,
                "timestamp": datetime.utcnow().isoformat(),
                "city": city,
                "layer": layer,
                "rule_id": rule_id,
                "severity": severity,
                "record_id": record_id,
                "field": field,
                "issue_type": issue_type,
                "message": message,
                "status": "open"
            }
            
            await self.db[self.ISSUES_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to create quality issue: {e}")
            return False
    
    async def get_quality_issues(
        self,
        city: Optional[str] = None,
        layer: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get quality issues with filters."""
        if not self.db:
            return []
        
        query = {}
        if city:
            query["city"] = city
        if layer:
            query["layer"] = layer
        if status:
            query["status"] = status
        
        cursor = self.db[self.ISSUES_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def resolve_quality_issue(
        self,
        issue_id: str,
        resolved_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Resolve quality issue."""
        if not self.db:
            return False
        
        try:
            await self.db[self.ISSUES_COLLECTION].update_one(
                {"issue_id": issue_id},
                {
                    "$set": {
                        "status": "resolved",
                        "resolved_at": datetime.utcnow().isoformat(),
                        "resolved_by": resolved_by,
                        "resolution_notes": notes
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to resolve quality issue: {e}")
            return False
    
    async def delete_old_quality_data(self, days: int = 90) -> int:
        """Delete old quality reports and issues."""
        if not self.db:
            return 0
        
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Delete old reports
            reports_result = await self.db[self.REPORTS_COLLECTION].delete_many({
                "timestamp": {"$lt": cutoff.isoformat()}
            })
            
            # Delete old issues
            issues_result = await self.db[self.ISSUES_COLLECTION].delete_many({
                "timestamp": {"$lt": cutoff.isoformat()}
            })
            
            total = reports_result.deleted_count + issues_result.deleted_count
            logger.info(f"Deleted {total} old quality records")
            return total
        except Exception as e:
            logger.error(f"Failed to delete old quality data: {e}")
            return 0
