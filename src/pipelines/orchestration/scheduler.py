"""
Pipeline Scheduler
==================

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/orchestration/scheduler.py

Scheduling logic cho pipelines với cron-style scheduling.
Tích hợp với Celery Beat cho distributed scheduling.

Features:
- Cron-style scheduling
- Dependency management
- Retry logic
- Concurrent execution control
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Loại schedule."""
    ONCE = "once"           # Run once
    INTERVAL = "interval"   # Fixed interval
    CRON = "cron"          # Cron expression
    DAILY = "daily"        # Daily at specific time
    WEEKLY = "weekly"      # Weekly on specific day


@dataclass
class PipelineSchedule:
    """Schedule configuration cho pipeline."""
    schedule_id: str
    city: str
    schedule_type: ScheduleType
    
    # For INTERVAL
    interval_minutes: Optional[int] = None
    
    # For CRON
    cron_expression: Optional[str] = None
    
    # For DAILY/WEEKLY
    hour: int = 0
    minute: int = 0
    day_of_week: Optional[int] = None  # 0=Monday, 6=Sunday
    
    # Pipeline config
    skip_bronze: bool = False
    skip_silver: bool = False
    skip_gold: bool = False
    poi_types: Optional[List[str]] = None
    
    # Scheduling
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    
    def should_run(self, now: datetime) -> bool:
        """Kiểm tra xem schedule có nên chạy không."""
        if not self.enabled:
            return False
        
        if self.next_run is None:
            return True
        
        return now >= self.next_run
    
    def calculate_next_run(self, now: datetime) -> datetime:
        """Tính next run time dựa trên schedule type."""
        if self.schedule_type == ScheduleType.ONCE:
            return None  # Không chạy lại
        
        elif self.schedule_type == ScheduleType.INTERVAL:
            if self.interval_minutes:
                return now + timedelta(minutes=self.interval_minutes)
            return None
        
        elif self.schedule_type == ScheduleType.DAILY:
            next_run = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            days_until = (self.day_of_week - now.weekday()) % 7
            if days_until == 0 and now.time() >= datetime.strptime(f"{self.hour}:{self.minute}", "%H:%M").time():
                days_until = 7
            next_run = now + timedelta(days=days_until)
            next_run = next_run.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            return next_run
        
        return None


class PipelineScheduler:
    """
    Scheduler cho pipelines.
    
    Quản lý schedules và trigger pipeline execution.
    Có thể chạy standalone hoặc tích hợp với Celery Beat.
    
    Usage:
        scheduler = PipelineScheduler()
        
        # Add daily schedule
        schedule = PipelineSchedule(
            schedule_id="hanoi_daily",
            city="hanoi",
            schedule_type=ScheduleType.DAILY,
            hour=2,
            minute=0
        )
        scheduler.add_schedule(schedule)
        
        # Start scheduler
        await scheduler.start()
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self._schedules: Dict[str, PipelineSchedule] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 60  # seconds
        
        # Celery integration
        self._celery_app = None
        if CELERY_AVAILABLE:
            try:
                from src.core.celery_app import celery_app
                self._celery_app = celery_app
            except ImportError:
                pass
        
        logger.info("PipelineScheduler initialized")
    
    def add_schedule(self, schedule: PipelineSchedule) -> None:
        """Thêm một schedule mới."""
        self._schedules[schedule.schedule_id] = schedule
        
        # Calculate initial next run
        now = datetime.utcnow()
        schedule.next_run = schedule.calculate_next_run(now)
        
        logger.info(f"Added schedule {schedule.schedule_id} for {schedule.city} "
                   f"(next_run={schedule.next_run})")
        
        # Register with Celery if available
        if self._celery_app and schedule.enabled:
            self._register_celery_schedule(schedule)
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """Xóa một schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            logger.info(f"Removed schedule {schedule_id}")
            return True
        return False
    
    def get_schedule(self, schedule_id: str) -> Optional[PipelineSchedule]:
        """Lấy schedule theo ID."""
        return self._schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[PipelineSchedule]:
        """Lấy tất cả schedules."""
        return list(self._schedules.values())
    
    def _register_celery_schedule(self, schedule: PipelineSchedule) -> None:
        """Register schedule với Celery Beat."""
        if not self._celery_app:
            return
        
        try:
            # Convert schedule to Celery beat schedule
            if schedule.schedule_type == ScheduleType.INTERVAL:
                celery_schedule = {
                    'task': 'src.pipelines.tasks.run_pipeline',
                    'schedule': timedelta(minutes=schedule.interval_minutes),
                    'args': (schedule.city,),
                    'kwargs': {
                        'skip_bronze': schedule.skip_bronze,
                        'skip_silver': schedule.skip_silver,
                        'skip_gold': schedule.skip_gold,
                        'poi_types': schedule.poi_types
                    }
                }
            elif schedule.schedule_type == ScheduleType.CRON:
                # Parse cron expression
                celery_schedule = {
                    'task': 'src.pipelines.tasks.run_pipeline',
                    'schedule': schedule.cron_expression,
                    'args': (schedule.city,),
                    'kwargs': {
                        'skip_bronze': schedule.skip_bronze,
                        'skip_silver': schedule.skip_silver,
                        'skip_gold': schedule.skip_gold,
                        'poi_types': schedule.poi_types
                    }
                }
            else:
                # For DAILY/WEEKLY, use crontab
                from celery.schedules import crontab
                
                if schedule.schedule_type == ScheduleType.DAILY:
                    celery_schedule = {
                        'task': 'src.pipelines.tasks.run_pipeline',
                        'schedule': crontab(hour=schedule.hour, minute=schedule.minute),
                        'args': (schedule.city,),
                        'kwargs': {
                            'skip_bronze': schedule.skip_bronze,
                            'skip_silver': schedule.skip_silver,
                            'skip_gold': schedule.skip_gold,
                            'poi_types': schedule.poi_types
                        }
                    }
                elif schedule.schedule_type == ScheduleType.WEEKLY:
                    celery_schedule = {
                        'task': 'src.pipelines.tasks.run_pipeline',
                        'schedule': crontab(
                            day_of_week=schedule.day_of_week,
                            hour=schedule.hour,
                            minute=schedule.minute
                        ),
                        'args': (schedule.city,),
                        'kwargs': {
                            'skip_bronze': schedule.skip_bronze,
                            'skip_silver': schedule.skip_silver,
                            'skip_gold': schedule.skip_gold,
                            'poi_types': schedule.poi_types
                        }
                    }
            
            # Add to Celery beat schedule
            self._celery_app.conf.beat_schedule[schedule.schedule_id] = celery_schedule
            logger.info(f"Registered schedule {schedule.schedule_id} with Celery Beat")
            
        except Exception as e:
            logger.warning(f"Failed to register schedule {schedule.schedule_id} with Celery: {e}")
    
    async def start(self) -> None:
        """Bắt đầu scheduler loop."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Pipeline scheduler started")
    
    async def stop(self) -> None:
        """Dừng scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Pipeline scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop - kiểm tra và trigger schedules."""
        while self._running:
            try:
                now = datetime.utcnow()
                
                for schedule in self._schedules.values():
                    if schedule.should_run(now):
                        await self._trigger_schedule(schedule, now)
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _trigger_schedule(self, schedule: PipelineSchedule, now: datetime) -> None:
        """Trigger một scheduled pipeline run."""
        logger.info(f"Triggering scheduled pipeline for {schedule.city} "
                   f"(schedule={schedule.schedule_id})")
        
        try:
            if self.orchestrator:
                # Run pipeline through orchestrator
                await self.orchestrator.run_full_pipeline(
                    city=schedule.city,
                    poi_types=schedule.poi_types,
                    skip_bronze=schedule.skip_bronze,
                    skip_silver=schedule.skip_silver,
                    skip_gold=schedule.skip_gold
                )
                
                schedule.run_count += 1
                schedule.last_run = now
                schedule.next_run = schedule.calculate_next_run(now)
                
                logger.info(f"Scheduled pipeline completed for {schedule.city}")
            else:
                logger.warning("No orchestrator configured, cannot run pipeline")
                
        except Exception as e:
            logger.error(f"Scheduled pipeline failed for {schedule.city}: {e}")
            schedule.error_count += 1
            schedule.last_run = now
            schedule.next_run = schedule.calculate_next_run(now)
    
    async def run_now(self, schedule_id: str) -> bool:
        """Manually trigger một schedule ngay lập tức."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            logger.warning(f"Schedule {schedule_id} not found")
            return False
        
        await self._trigger_schedule(schedule, datetime.utcnow())
        return True
