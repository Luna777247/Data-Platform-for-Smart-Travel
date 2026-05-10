"""
Pipeline Orchestration Monitoring
=================================

Monitoring cho pipeline orchestration.
Theo RECOMMENDED_STRUCTURE.md - pipelines/orchestration/monitoring.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class OrchestrationMonitor:
    """
    Monitor pipeline orchestration và execution.
    
    Monitors:
    1. Pipeline execution status
    2. Stage completion times
    3. Error rates
    4. Throughput metrics
    5. Resource utilization
    """
    
    def __init__(self):
        self.executions: List[Dict[str, Any]] = []
        self.stage_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration_ms": 0,
            "total_records": 0
        })
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        logger.info("OrchestrationMonitor initialized")
    
    def record_execution(
        self,
        pipeline_id: str,
        city: str,
        stages: List[str],
        status: str,
        duration_ms: float,
        records_processed: int = 0,
        error: Optional[str] = None
    ):
        """
        Record một pipeline execution.
        
        Args:
            pipeline_id: Pipeline identifier
            city: Target city
            stages: List of executed stages
            status: Execution status
            duration_ms: Total duration
            records_processed: Number of records
            error: Error message if failed
        """
        execution = {
            "pipeline_id": pipeline_id,
            "city": city,
            "stages": stages,
            "status": status,
            "duration_ms": duration_ms,
            "records_processed": records_processed,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.executions.append(execution)
        
        # Update stage stats
        for stage in stages:
            stats = self.stage_stats[stage]
            stats["total_executions"] += 1
            
            if status == "completed":
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            # Update average duration
            stage_duration = duration_ms / len(stages)
            stats["avg_duration_ms"] = (
                (stats["avg_duration_ms"] * (stats["total_executions"] - 1) + stage_duration)
                / stats["total_executions"]
            )
            
            stats["total_records"] += records_processed
        
        # Record error
        if error:
            error_type = error.split(":")[0] if ":" in error else "unknown"
            self.error_counts[error_type] += 1
        
        logger.info(
            f"Recorded execution: {pipeline_id} for {city} - {status} "
            f"({records_processed} records, {duration_ms}ms)"
        )
    
    def record_stage_execution(
        self,
        stage_name: str,
        city: str,
        status: str,
        duration_ms: float,
        records_in: int = 0,
        records_out: int = 0,
        error: Optional[str] = None
    ):
        """Record một stage execution."""
        stats = self.stage_stats[stage_name]
        stats["total_executions"] += 1
        
        if status == "completed":
            stats["successful"] += 1
        else:
            stats["failed"] += 1
        
        # Update average duration
        stats["avg_duration_ms"] = (
            (stats["avg_duration_ms"] * (stats["total_executions"] - 1) + duration_ms)
            / stats["total_executions"]
        )
        
        stats["total_records"] += records_out
    
    def get_pipeline_stats(
        self,
        city: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get pipeline statistics."""
        executions = self.executions
        
        if city:
            executions = [e for e in executions if e["city"] == city]
        
        if since:
            executions = [
                e for e in executions
                if datetime.fromisoformat(e["timestamp"]) >= since
            ]
        
        total = len(executions)
        successful = sum(1 for e in executions if e["status"] == "completed")
        failed = total - successful
        
        total_records = sum(e.get("records_processed", 0) for e in executions)
        
        avg_duration = (
            sum(e["duration_ms"] for e in executions) / total if total > 0 else 0
        )
        
        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_records_processed": total_records,
            "avg_duration_ms": round(avg_duration, 2),
            "by_city": self._get_by_city_stats(executions)
        }
    
    def get_stage_stats(self) -> Dict[str, Any]:
        """Get stage-level statistics."""
        return dict(self.stage_stats)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error summary."""
        return dict(self.error_counts)
    
    def get_recent_executions(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent executions."""
        return sorted(
            self.executions,
            key=lambda e: e["timestamp"],
            reverse=True
        )[:limit]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        recent = self.get_recent_executions(50)
        
        if not recent:
            return {"status": "unknown", "message": "No executions recorded"}
        
        recent_success = sum(1 for e in recent if e["status"] == "completed")
        success_rate = recent_success / len(recent)
        
        if success_rate >= 0.95:
            status = "healthy"
        elif success_rate >= 0.8:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "success_rate": round(success_rate, 2),
            "recent_executions": len(recent),
            "last_execution": recent[0]["timestamp"] if recent else None
        }
    
    def _get_by_city_stats(
        self,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Get statistics grouped by city."""
        by_city: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "records": 0
        })
        
        for e in executions:
            city = e["city"]
            by_city[city]["total"] += 1
            
            if e["status"] == "completed":
                by_city[city]["successful"] += 1
            else:
                by_city[city]["failed"] += 1
            
            by_city[city]["records"] += e.get("records_processed", 0)
        
        return dict(by_city)
    
    def reset_stats(self):
        """Reset all statistics."""
        self.executions = []
        self.stage_stats = defaultdict(lambda: {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration_ms": 0,
            "total_records": 0
        })
        self.error_counts = defaultdict(int)
        
        logger.info("Statistics reset")
