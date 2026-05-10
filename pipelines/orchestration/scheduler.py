"""
Pipeline Scheduler
==================

Pipeline scheduler cho Smart Tourism Platform.
Theo RECOMMENDED_STRUCTURE.md - pipelines/orchestration/scheduler.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Pipeline schedule types."""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    CRON = "cron"


class PipelineScheduler:
    """
    Schedule pipeline executions.
    
    Supports:
    - One-time execution
    - Recurring schedules (hourly, daily, weekly)
    - Cron expressions
    - City-specific schedules
    """
    
    def __init__(self):
        self.schedules: Dict[str, Dict[str, Any]] = {}
        logger.info("PipelineScheduler initialized")
    
    def schedule_pipeline(
        self,
        pipeline_id: str,
        city: str,
        schedule_type: ScheduleType,
        start_time: Optional[datetime] = None,
        cron_expression: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schedule một pipeline execution.
        
        Args:
            pipeline_id: Unique pipeline identifier
            city: Target city
            schedule_type: Type of schedule
            start_time: When to start (for ONCE, DAILY, WEEKLY)
            cron_expression: Cron expression (for CRON type)
            metadata: Additional metadata
            
        Returns:
            Schedule configuration
        """
        schedule_id = f"{pipeline_id}_{city}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        schedule = {
            "schedule_id": schedule_id,
            "pipeline_id": pipeline_id,
            "city": city,
            "type": schedule_type.value,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "metadata": metadata or {}
        }
        
        # Set execution parameters based on type
        if schedule_type == ScheduleType.ONCE:
            schedule["execute_at"] = (start_time or datetime.utcnow()).isoformat()
        
        elif schedule_type == ScheduleType.HOURLY:
            schedule["interval_hours"] = 1
            schedule["next_execution"] = self._get_next_hourly()
        
        elif schedule_type == ScheduleType.DAILY:
            schedule["execute_at"] = start_time.strftime("%H:%M") if start_time else "02:00"
            schedule["next_execution"] = self._get_next_daily(start_time)
        
        elif schedule_type == ScheduleType.WEEKLY:
            schedule["execute_at"] = start_time.strftime("%H:%M") if start_time else "02:00"
            schedule["day_of_week"] = start_time.weekday() if start_time else 0
            schedule["next_execution"] = self._get_next_weekly(start_time)
        
        elif schedule_type == ScheduleType.CRON:
            schedule["cron"] = cron_expression
            schedule["next_execution"] = self._get_next_cron(cron_expression)
        
        # Store schedule
        self.schedules[schedule_id] = schedule
        
        logger.info(f"Created schedule: {schedule_id} ({schedule_type.value})")
        return schedule
    
    def get_schedules(
        self,
        city: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all schedules with optional filters."""
        schedules = list(self.schedules.values())
        
        if city:
            schedules = [s for s in schedules if s["city"] == city]
        
        if active_only:
            schedules = [s for s in schedules if s["is_active"]]
        
        return schedules
    
    def get_due_schedules(self) -> List[Dict[str, Any]]:
        """Get schedules that are due for execution."""
        now = datetime.utcnow()
        due = []
        
        for schedule in self.schedules.values():
            if not schedule["is_active"]:
                continue
            
            next_exec = schedule.get("next_execution")
            if next_exec:
                next_time = datetime.fromisoformat(next_exec)
                if now >= next_time:
                    due.append(schedule)
        
        return due
    
    def deactivate_schedule(self, schedule_id: str) -> bool:
        """Deactivate một schedule."""
        if schedule_id in self.schedules:
            self.schedules[schedule_id]["is_active"] = False
            logger.info(f"Deactivated schedule: {schedule_id}")
            return True
        return False
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete một schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            logger.info(f"Deleted schedule: {schedule_id}")
            return True
        return False
    
    def update_next_execution(self, schedule_id: str) -> Optional[str]:
        """Update next execution time sau khi chạy."""
        if schedule_id not in self.schedules:
            return None
        
        schedule = self.schedules[schedule_id]
        schedule_type = schedule["type"]
        
        now = datetime.utcnow()
        
        if schedule_type == ScheduleType.HOURLY:
            next_time = now + timedelta(hours=1)
        
        elif schedule_type == ScheduleType.DAILY:
            next_time = now + timedelta(days=1)
            next_time = next_time.replace(
                hour=int(schedule["execute_at"].split(":")[0]),
                minute=int(schedule["execute_at"].split(":")[1]),
                second=0
            )
        
        elif schedule_type == ScheduleType.WEEKLY:
            next_time = now + timedelta(weeks=1)
            next_time = next_time.replace(
                hour=int(schedule["execute_at"].split(":")[0]),
                minute=int(schedule["execute_at"].split(":")[1]),
                second=0
            )
        
        elif schedule_type == ScheduleType.CRON:
            # Simplified - in production use proper cron parser
            next_time = now + timedelta(hours=1)
        
        else:
            # One-time schedule - deactivate after execution
            schedule["is_active"] = False
            next_time = None
        
        if next_time:
            schedule["next_execution"] = next_time.isoformat()
            return schedule["next_execution"]
        
        return None
    
    # ============= Helper Methods =============
    
    def _get_next_hourly(self) -> str:
        """Get next hourly execution time."""
        now = datetime.utcnow()
        next_hour = now + timedelta(hours=1)
        next_hour = next_hour.replace(minute=0, second=0, microsecond=0)
        return next_hour.isoformat()
    
    def _get_next_daily(self, start_time: Optional[datetime]) -> str:
        """Get next daily execution time."""
        now = datetime.utcnow()
        
        if start_time:
            next_exec = now.replace(
                hour=start_time.hour,
                minute=start_time.minute,
                second=0,
                microsecond=0
            )
        else:
            next_exec = now.replace(hour=2, minute=0, second=0, microsecond=0)
        
        if next_exec <= now:
            next_exec += timedelta(days=1)
        
        return next_exec.isoformat()
    
    def _get_next_weekly(self, start_time: Optional[datetime]) -> str:
        """Get next weekly execution time."""
        now = datetime.utcnow()
        target_day = start_time.weekday() if start_time else 0  # Monday
        
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_exec = now + timedelta(days=days_ahead)
        
        if start_time:
            next_exec = next_exec.replace(
                hour=start_time.hour,
                minute=start_time.minute,
                second=0
            )
        else:
            next_exec = next_exec.replace(hour=2, minute=0, second=0)
        
        return next_exec.isoformat()
    
    def _get_next_cron(self, cron_expression: str) -> str:
        """Parse cron và get next execution."""
        # Simplified implementation
        # Production should use proper cron library
        now = datetime.utcnow()
        next_exec = now + timedelta(hours=1)
        return next_exec.isoformat()
    
    def get_schedule_summary(self) -> Dict[str, Any]:
        """Get summary của tất cả schedules."""
        total = len(self.schedules)
        active = sum(1 for s in self.schedules.values() if s["is_active"])
        due = len(self.get_due_schedules())
        
        by_city: Dict[str, int] = {}
        for s in self.schedules.values():
            city = s["city"]
            by_city[city] = by_city.get(city, 0) + 1
        
        return {
            "total_schedules": total,
            "active_schedules": active,
            "inactive_schedules": total - active,
            "due_for_execution": due,
            "by_city": by_city,
            "timestamp": datetime.utcnow().isoformat()
        }
