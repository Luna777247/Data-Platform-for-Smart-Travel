"""
Monitoring Repository
=====================

Repository cho monitoring data access.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/db/repositories/monitoring_repository.py
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MonitoringRepository:
    """
    Repository cho monitoring data.
    
    Provides CRUD operations cho:
    - System metrics
    - Health checks
    - Logs
    - Alerts
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.METRICS_COLLECTION = "system_metrics"
        self.HEALTH_COLLECTION = "health_checks"
        self.LOGS_COLLECTION = "application_logs"
        self.ALERTS_COLLECTION = "alerts"
        logger.info("MonitoringRepository initialized")
    
    async def store_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        unit: str = ""
    ) -> bool:
        """Store system metric."""
        if not self.db:
            return False
        
        try:
            doc = {
                "timestamp": datetime.utcnow().isoformat(),
                "metric_name": metric_name,
                "value": value,
                "labels": labels or {},
                "unit": unit
            }
            
            await self.db[self.METRICS_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to store metric: {e}")
            return False
    
    async def store_health_check(
        self,
        component: str,
        status: str,
        response_time_ms: float,
        error_message: Optional[str] = None
    ) -> bool:
        """Store health check."""
        if not self.db:
            return False
        
        try:
            doc = {
                "timestamp": datetime.utcnow().isoformat(),
                "component": component,
                "status": status,
                "response_time_ms": response_time_ms,
                "error_message": error_message
            }
            
            await self.db[self.HEALTH_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to store health check: {e}")
            return False
    
    async def store_log(
        self,
        level: str,
        logger_name: str,
        message: str,
        correlation_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store application log."""
        if not self.db:
            return False
        
        try:
            doc = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "logger": logger_name,
                "message": message,
                "correlation_id": correlation_id,
                "extra": extra or {}
            }
            
            await self.db[self.LOGS_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to store log: {e}")
            return False
    
    async def store_alert(
        self,
        alert_id: str,
        severity: str,
        category: str,
        title: str,
        message: str,
        source: str
    ) -> bool:
        """Store alert."""
        if not self.db:
            return False
        
        try:
            doc = {
                "alert_id": alert_id,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": severity,
                "category": category,
                "title": title,
                "message": message,
                "source": source,
                "status": "active"
            }
            
            await self.db[self.ALERTS_COLLECTION].insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
            return False
    
    async def get_metrics(
        self,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get metrics with filters."""
        if not self.db:
            return []
        
        query = {}
        if metric_name:
            query["metric_name"] = metric_name
        if since:
            query["timestamp"] = {"$gte": since.isoformat()}
        
        cursor = self.db[self.METRICS_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_health_checks(
        self,
        component: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get health checks with filters."""
        if not self.db:
            return []
        
        query = {}
        if component:
            query["component"] = component
        if since:
            query["timestamp"] = {"$gte": since.isoformat()}
        
        cursor = self.db[self.HEALTH_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_logs(
        self,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get logs with filters."""
        if not self.db:
            return []
        
        query = {}
        if level:
            query["level"] = level
        if logger_name:
            query["logger"] = logger_name
        if since:
            query["timestamp"] = {"$gte": since.isoformat()}
        
        cursor = self.db[self.LOGS_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alerts with filters."""
        if not self.db:
            return []
        
        query = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        
        cursor = self.db[self.ALERTS_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Resolve an alert."""
        if not self.db:
            return False
        
        try:
            await self.db[self.ALERTS_COLLECTION].update_one(
                {"alert_id": alert_id},
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
            logger.error(f"Failed to resolve alert: {e}")
            return False
