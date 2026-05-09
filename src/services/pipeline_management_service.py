"""
Pipeline Management Service - Quản lý toàn bộ pipeline execution lifecycle
================================================================================
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section II
Module chính để điều khiển và giám sát pipeline execution

Mục đích:
- Điều khiển pipeline lifecycle (start, stop, pause, resume, restart)
- Theo dõi real-time status và progress
- Lưu trữ execution history và metrics
- Xử lý errors và retries
- Cung cấp data cho dashboard và monitoring

Kiến trúc:
- MongoDB: Persistent storage cho execution records và history
- Redis: Real-time caching cho status và progress
- BackgroundTasks: Async pipeline execution không block API

Workflow:
1. API gọi start_pipeline() → Tạo execution record
2. Lưu vào MongoDB (persistent) + Redis (real-time cache)
3. Background task chạy pipeline thực tế
4. Cập nhật progress real-time trong Redis
5. Khi hoàn thành, sync toàn bộ data vào MongoDB
6. Cleanup Redis cache sau retention period
"""

# Import asyncio để hỗ trợ async operations
# Cần thiết cho background tasks và concurrent processing
import asyncio

# Import logging để ghi lại operations
import logging

# Import json để serialize/deserialize data
import json

# Import datetime classes để xử lý timestamps
# datetime: Tạo timestamp objects
# timezone: Xử lý timezone-aware timestamps (UTC)
# timedelta: Tính toán thời gian (retention, timeouts)
from datetime import datetime, timezone, timedelta

# Import type hints để định nghĩa function signatures rõ ràng
# Dict: Dictionary type
# List: List type
# Any: Bất kỳ type nào
# Optional: Type có thể None
from typing import Dict, List, Any, Optional

# Import Enum để định nghĩa các enumeration types
from enum import Enum

# Import Motor async MongoDB client
# Motor là async driver cho MongoDB, thay thế pymongo trong async context
from motor.motor_asyncio import AsyncIOMotorClient

# Import redis.asyncio cho async Redis operations
# Redis dùng cho real-time caching và pub/sub
import redis.asyncio as redis

# Import BackgroundTasks từ FastAPI
# Cho phép chạy tasks async sau khi trả về response
from fastapi import BackgroundTasks

# Tạo logger cho module này
# __name__ sẽ là "src.services.pipeline_management_service"
# Logs từ service này sẽ có correlation ID và context
logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    TRANSFORMING = "transforming"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class PipelineExecutionType(str, Enum):
    """Pipeline execution types"""
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    SPECIFIC_CITY = "specific_city"
    SPECIFIC_CATEGORY = "specific_category"
    BACKFILL = "backfill"


class PipelineManagementService:
    """Service cho pipeline management và tracking"""
    
    def __init__(self, mongo_client: AsyncIOMotorClient, redis_client: redis.Redis):
        self.mongo_client = mongo_client
        self.redis_client = redis_client
        self.db = mongo_client.smart_travel
        self.pipeline_collection = self.db.pipeline_executions
        self.metrics_collection = self.db.pipeline_metrics
        self.config_collection = self.db.pipeline_config
        self.errors_collection = self.db.pipeline_errors
    
    async def start_pipeline(
        self,
        cities: List[str],
        categories: List[str],
        execution_type: PipelineExecutionType,
        background_tasks: BackgroundTasks,
        user_id: str = "system"
    ) -> str:
        """Khởi động pipeline execution"""
        execution_id = f"pipeline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        try:
            # Create execution record
            execution_record = {
                "_id": execution_id,
                "execution_id": execution_id,
                "pipeline_name": f"{execution_type.value}_{len(cities)}cities_{len(categories)}categories",
                "source": "osm",
                "cities": cities,
                "categories": categories,
                "execution_type": execution_type.value,
                "status": PipelineStatus.PENDING.value,
                "started_at": datetime.now(timezone.utc),
                "started_by": user_id,
                "records_processed": 0,
                "records_failed": 0,
                "current_stage": "initialization",
                "stages": {
                    "ingestion": {"status": "pending", "started_at": None, "completed_at": None},
                    "bronze_processing": {"status": "pending", "started_at": None, "completed_at": None},
                    "silver_processing": {"status": "pending", "started_at": None, "completed_at": None},
                    "gold_processing": {"status": "pending", "started_at": None, "completed_at": None},
                    "database_integration": {"status": "pending", "started_at": None, "completed_at": None}
                },
                "configuration": {
                    "batch_size": 1000,
                    "max_retries": 3,
                    "timeout_seconds": 300,
                    "parallelism": 4
                },
                "metrics": {
                    "total_records": 0,
                    "processed_records": 0,
                    "failed_records": 0,
                    "duplicates_removed": 0,
                    "processing_time_seconds": 0,
                    "throughput_records_per_second": 0
                },
                "error_message": None,
                "retry_count": 0,
                "last_retry_at": None
            }
            
            # Insert into MongoDB
            await self.pipeline_collection.insert_one(execution_record)
            
            # Cache in Redis for real-time tracking
            await self.redis_client.setex(
                f"pipeline:{execution_id}",
                3600,  # 1 hour TTL
                json.dumps({
                    "status": PipelineStatus.PENDING.value,
                    "progress": 0,
                    "current_stage": "initialization"
                })
            )
            
            # Start background execution
            background_tasks.add_task(
                self._execute_pipeline_background,
                execution_id,
                cities,
                categories,
                execution_type,
                user_id
            )
            
            logger.info(f"🚀 Pipeline started: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"❌ Error starting pipeline {execution_id}: {e}")
            await self._log_error(execution_id, "pipeline_start", str(e))
            raise e
    
    async def stop_pipeline(self, execution_id: str, user_id: str = "system") -> bool:
        """Dừng pipeline execution"""
        try:
            # Update execution status
            result = await self.pipeline_collection.update_one(
                {"_id": execution_id, "status": {"$in": [PipelineStatus.RUNNING.value, PipelineStatus.PAUSED.value]}},
                {
                    "$set": {
                        "status": PipelineStatus.CANCELLED.value,
                        "completed_at": datetime.now(timezone.utc),
                        "cancelled_by": user_id
                    }
                }
            )
            
            # Update Redis cache
            await self.redis_client.setex(
                f"pipeline:{execution_id}",
                3600,
                json.dumps({
                    "status": PipelineStatus.CANCELLED.value,
                    "progress": 100,
                    "current_stage": "cancelled"
                })
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"⏹️ Pipeline stopped: {execution_id}")
            else:
                logger.warning(f"⚠️ Pipeline not found or not running: {execution_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error stopping pipeline {execution_id}: {e}")
            await self._log_error(execution_id, "pipeline_stop", str(e))
            return False
    
    async def pause_pipeline(self, execution_id: str, user_id: str = "system") -> bool:
        """Tạm dừng pipeline execution"""
        try:
            result = await self.pipeline_collection.update_one(
                {"_id": execution_id, "status": PipelineStatus.RUNNING.value},
                {
                    "$set": {
                        "status": PipelineStatus.PAUSED.value,
                        "paused_at": datetime.now(timezone.utc),
                        "paused_by": user_id
                    }
                }
            )
            
            # Update Redis cache
            await self.redis_client.setex(
                f"pipeline:{execution_id}",
                3600,
                json.dumps({
                    "status": PipelineStatus.PAUSED.value,
                    "progress": None,
                    "current_stage": "paused"
                })
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"⏸️ Pipeline paused: {execution_id}")
            else:
                logger.warning(f"⚠️ Pipeline not found or not running: {execution_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error pausing pipeline {execution_id}: {e}")
            await self._log_error(execution_id, "pipeline_pause", str(e))
            return False
    
    async def resume_pipeline(self, execution_id: str, user_id: str = "system") -> bool:
        """Tiếp tục pipeline execution đã tạm dừng"""
        try:
            result = await self.pipeline_collection.update_one(
                {"_id": execution_id, "status": PipelineStatus.PAUSED.value},
                {
                    "$set": {
                        "status": PipelineStatus.RUNNING.value,
                        "resumed_at": datetime.now(timezone.utc),
                        "resumed_by": user_id,
                        "$unset": ["paused_at", "paused_by"]
                    }
                }
            )
            
            # Update Redis cache
            await self.redis_client.setex(
                f"pipeline:{execution_id}",
                3600,
                json.dumps({
                    "status": PipelineStatus.RUNNING.value,
                    "progress": None,
                    "current_stage": "resumed"
                })
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"▶️ Pipeline resumed: {execution_id}")
            else:
                logger.warning(f"⚠️ Pipeline not found or not paused: {execution_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error resuming pipeline {execution_id}: {e}")
            await self._log_error(execution_id, "pipeline_resume", str(e))
            return False
    
    async def restart_pipeline(
        self,
        execution_id: str,
        background_tasks: BackgroundTasks,
        user_id: str = "system"
    ) -> Optional[str]:
        """Khởi động lại pipeline execution đã thất bại"""
        try:
            # Get original execution details
            original_execution = await self.pipeline_collection.find_one({"_id": execution_id})
            if not original_execution:
                logger.warning(f"⚠️ Original execution not found: {execution_id}")
                return None
            
            # Create new execution
            new_execution_id = f"pipeline_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{user_id}"
            
            new_execution = original_execution.copy()
            new_execution["_id"] = new_execution_id
            new_execution["execution_id"] = new_execution_id
            new_execution["status"] = PipelineStatus.PENDING.value
            new_execution["started_at"] = datetime.now(timezone.utc)
            new_execution["started_by"] = user_id
            new_execution["original_execution_id"] = execution_id
            new_execution["retry_count"] = original_execution.get("retry_count", 0) + 1
            new_execution["last_retry_at"] = datetime.now(timezone.utc)
            
            # Reset stage and metrics
            new_execution["current_stage"] = "initialization"
            new_execution["records_processed"] = 0
            new_execution["records_failed"] = 0
            new_execution["error_message"] = None
            
            # Reset stages
            for stage in new_execution["stages"]:
                new_execution["stages"][stage] = {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None
                }
            
            # Insert new execution
            await self.pipeline_collection.insert_one(new_execution)
            
            # Start background execution
            background_tasks.add_task(
                self._execute_pipeline_background,
                new_execution_id,
                original_execution["cities"],
                original_execution["categories"],
                PipelineExecutionType(original_execution["execution_type"]),
                user_id
            )
            
            logger.info(f"🔄 Pipeline restarted: {execution_id} -> {new_execution_id}")
            return new_execution_id
            
        except Exception as e:
            logger.error(f"❌ Error restarting pipeline {execution_id}: {e}")
            await self._log_error(execution_id, "pipeline_restart", str(e))
            return None
    
    async def get_pipeline_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Lấy trạng thái chi tiết của pipeline execution"""
        try:
            # Try Redis first for real-time status
            cached_status = await self.redis_client.get(f"pipeline:{execution_id}")
            if cached_status:
                return json.loads(cached_status)
            
            # Fallback to MongoDB
            execution = await self.pipeline_collection.find_one(
                {"_id": execution_id},
                {"status": 1, "started_at": 1, "completed_at": 1, "current_stage": 1, "records_processed": 1, "records_failed": 1}
            )
            
            if execution:
                return {
                    "status": execution["status"],
                    "progress": self._calculate_progress(execution),
                    "current_stage": execution["current_stage"],
                    "stages": execution["stages"],
                    "metrics": execution["metrics"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline status {execution_id}: {e}")
            return None
    
    async def get_active_pipelines(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các pipeline đang chạy"""
        try:
            cursor = self.pipeline_collection.find({
                "status": {"$in": [PipelineStatus.RUNNING.value, PipelineStatus.PAUSED.value]}
            }).sort("started_at", -1)
            
            active_pipelines = []
            async for execution in cursor:
                active_pipelines.append({
                    "execution_id": execution["execution_id"],
                    "pipeline_name": execution["pipeline_name"],
                    "status": execution["status"],
                    "started_at": execution["started_at"],
                    "current_stage": execution["current_stage"],
                    "progress": self._calculate_progress(execution),
                    "cities": execution["cities"],
                    "categories": execution["categories"],
                    "execution_type": execution["execution_type"]
                })
            
            return active_pipelines
            
        except Exception as e:
            logger.error(f"❌ Error getting active pipelines: {e}")
            return []
    
    async def get_pipeline_history(
        self,
        limit: int = 50,
        offset: int = 0,
        city: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lấy lịch sử pipeline execution với filtering và pagination"""
        try:
            # Build query
            query = {}
            if city:
                query["cities"] = city
            if category:
                query["categories"] = category
            if status:
                query["status"] = status
            
            # Get total count
            total_count = await self.pipeline_collection.count_documents(query)
            
            # Get executions with pagination
            cursor = self.pipeline_collection.find(query).sort("started_at", -1).skip(offset).limit(limit)
            
            executions = []
            async for execution in cursor:
                executions.append({
                    "execution_id": execution["execution_id"],
                    "pipeline_name": execution["pipeline_name"],
                    "status": execution["status"],
                    "started_at": execution["started_at"],
                    "completed_at": execution.get("completed_at"),
                    "execution_type": execution["execution_type"],
                    "cities": execution["cities"],
                    "categories": execution["categories"],
                    "records_processed": execution["records_processed"],
                    "records_failed": execution["records_failed"],
                    "progress": self._calculate_progress(execution),
                    "duration_seconds": self._calculate_duration(execution),
                    "error_message": execution.get("error_message")
                })
            
            has_more = (offset + limit) < total_count
            
            return {
                "executions": executions,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline history: {e}")
            return {"executions": [], "total_count": 0, "limit": limit, "offset": offset, "has_more": False}
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Lấy dashboard data cho pipeline monitoring"""
        try:
            # Get active pipelines
            active_pipelines = await self.get_active_pipelines()
            
            # Get recent executions (last 24 hours)
            since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_cursor = self.pipeline_collection.find({
                "started_at": {"$gte": since_24h}
            }).sort("started_at", -1)
            
            recent_executions = []
            failed_count = 0
            completed_count = 0
            
            async for execution in recent_cursor:
                if execution["status"] == PipelineStatus.FAILED.value:
                    failed_count += 1
                elif execution["status"] == PipelineStatus.COMPLETED.value:
                    completed_count += 1
                
                recent_executions.append({
                    "execution_id": execution["execution_id"],
                    "status": execution["status"],
                    "started_at": execution["started_at"],
                    "duration_seconds": self._calculate_duration(execution),
                    "records_processed": execution["records_processed"]
                })
            
            # Get error summary (last 24 hours)
            error_cursor = self.errors_collection.find({
                "timestamp": {"$gte": since_24h}
            }).sort("timestamp", -1).limit(50)
            
            errors = []
            error_categories = {}
            
            async for error in error_cursor:
                error_type = error.get("error_type", "unknown")
                if error_type not in error_categories:
                    error_categories[error_type] = 0
                error_categories[error_type] += 1
                
                errors.append({
                    "execution_id": error["execution_id"],
                    "error_type": error["error_type"],
                    "error_message": error["error_message"],
                    "timestamp": error["timestamp"],
                    "severity": error.get("severity", "error")
                })
            
            return {
                "active_pipelines": active_pipelines,
                "recent_executions": recent_executions,
                "summary": {
                    "total_active_pipelines": len(active_pipelines),
                    "recent_executions_24h": len(recent_executions),
                    "completed_24h": completed_count,
                    "failed_24h": failed_count,
                    "success_rate_24h": (completed_count / len(recent_executions) * 100) if len(recent_executions) > 0 else 0,
                    "total_errors_24h": len(errors),
                    "top_error_categories": dict(sorted(error_categories.items(), key=lambda x: x[1], reverse=True)[:5])
                },
                "errors": errors[:20]  # Limit to last 20 errors
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {e}")
            return {"active_pipelines": [], "recent_executions": [], "summary": {}, "errors": []}
    
    async def get_pipeline_metrics(self, time_range: str = "24h") -> Dict[str, Any]:
        """Lấy pipeline metrics cho monitoring"""
        try:
            # Calculate time range
            time_delta = self._parse_time_range(time_range)
            since_time = datetime.now(timezone.utc) - time_delta
            
            # Get metrics from MongoDB aggregation
            pipeline = [
                {
                    "$match": {
                        "started_at": {"$gte": since_time}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_executions": {"$sum": 1},
                        "completed_executions": {
                            "$sum": {"$cond": [{"$eq": ["$status", PipelineStatus.COMPLETED.value]}, 1, 0]}
                        },
                        "failed_executions": {
                            "$sum": {"$cond": [{"$eq": ["$status", PipelineStatus.FAILED.value]}, 1, 0]}
                        },
                        "total_records_processed": {"$sum": "$records_processed"},
                        "total_records_failed": {"$sum": "$records_failed"},
                        "avg_duration": {"$avg": "$metrics.processing_time_seconds"},
                        "total_processing_time": {"$sum": "$metrics.processing_time_seconds"}
                    }
                }
            ]
            
            result = await self.pipeline_collection.aggregate(pipeline).to_list(None)
            metrics = result[0] if result else {}
            
            # Calculate derived metrics
            total_executions = metrics.get("total_executions", 0)
            completed_executions = metrics.get("completed_executions", 0)
            success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else 0
            
            avg_throughput = 0
            if metrics.get("total_processing_time", 0) > 0:
                avg_throughput = metrics.get("total_records_processed", 0) / metrics.get("total_processing_time", 1)
            
            return {
                "time_range": time_range,
                "period": {
                    "start": since_time.isoformat(),
                    "end": datetime.now(timezone.utc).isoformat()
                },
                "execution_metrics": {
                    "total_executions": total_executions,
                    "completed_executions": completed_executions,
                    "failed_executions": metrics.get("failed_executions", 0),
                    "success_rate": round(success_rate, 2),
                    "avg_duration_seconds": round(metrics.get("avg_duration", 0), 2)
                },
                "data_metrics": {
                    "total_records_processed": metrics.get("total_records_processed", 0),
                    "total_records_failed": metrics.get("total_records_failed", 0),
                    "success_rate": round(
                        ((metrics.get("total_records_processed", 0) - metrics.get("total_records_failed", 0)) / 
                         max(metrics.get("total_records_processed", 1), 1)) * 100, 
                        2
                    ),
                    "avg_throughput_records_per_second": round(avg_throughput, 2)
                },
                "performance_metrics": {
                    "avg_processing_time_seconds": round(metrics.get("avg_duration", 0), 2),
                    "total_processing_time_hours": round(metrics.get("total_processing_time", 0) / 3600, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline metrics: {e}")
            return {"time_range": time_range, "error": str(e)}
    
    async def get_pipeline_errors(
        self,
        limit: int = 50,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lấy danh sách errors từ pipeline executions"""
        try:
            query = {}
            if severity:
                query["severity"] = severity
            
            cursor = self.errors_collection.find(query).sort("timestamp", -1).limit(limit)
            
            errors = []
            async for error in cursor:
                errors.append({
                    "error_id": str(error["_id"]),
                    "execution_id": error["execution_id"],
                    "error_type": error["error_type"],
                    "error_message": error["error_message"],
                    "severity": error.get("severity", "error"),
                    "timestamp": error["timestamp"],
                    "stack_trace": error.get("stack_trace"),
                    "context": error.get("context", {})
                })
            
            return errors
            
        except Exception as e:
            logger.error(f"❌ Error getting pipeline errors: {e}")
            return []
    
    async def get_data_quality_report(self, time_range: str = "24h") -> Dict[str, Any]:
        """Lấy data quality report"""
        try:
            # Calculate time range
            time_delta = self._parse_time_range(time_range)
            since_time = datetime.now(timezone.utc) - time_delta
            
            # Get quality metrics from completed executions
            pipeline = [
                {
                    "$match": {
                        "started_at": {"$gte": since_time},
                        "status": PipelineStatus.COMPLETED.value
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_executions": {"$sum": 1},
                        "total_records_processed": {"$sum": "$records_processed"},
                        "total_duplicates_removed": {"$sum": "$metrics.duplicates_removed"},
                        "avg_quality_score": {"$avg": "$metrics.quality_score"}
                    }
                }
            ]
            
            result = await self.pipeline_collection.aggregate(pipeline).to_list(None)
            quality_metrics = result[0] if result else {}
            
            return {
                "time_range": time_range,
                "period": {
                    "start": since_time.isoformat(),
                    "end": datetime.now(timezone.utc).isoformat()
                },
                "quality_summary": {
                    "total_executions": quality_metrics.get("total_executions", 0),
                    "total_records_processed": quality_metrics.get("total_records_processed", 0),
                    "total_duplicates_removed": quality_metrics.get("total_duplicates_removed", 0),
                    "avg_quality_score": round(quality_metrics.get("avg_quality_score", 0), 2),
                    "duplicate_rate": round(
                        (quality_metrics.get("total_duplicates_removed", 0) / 
                         max(quality_metrics.get("total_records_processed", 1), 1)) * 100, 
                        2
                    )
                },
                "quality_trends": {
                    "data_completeness": "stable",  # Would need actual trend calculation
                    "data_accuracy": "improving",
                    "duplicate_detection": "effective"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting data quality report: {e}")
            return {"time_range": time_range, "error": str(e)}
    
    async def cleanup_resources(self, older_than_days: int = 30, user_id: str = "system") -> Dict[str, Any]:
        """Dọn dẹp pipeline resources cũ"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            # Cleanup old executions
            executions_result = await self.pipeline_collection.delete_many({
                "started_at": {"$lt": cutoff_date},
                "status": {"$in": [PipelineStatus.COMPLETED.value, PipelineStatus.FAILED.value]}
            })
            
            # Cleanup old errors
            errors_result = await self.errors_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            # Cleanup Redis cache
            redis_pattern = "pipeline:*"
            cursor = 0
            deleted_keys = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor, match=redis_pattern, count=100)
                if keys:
                    deleted_keys += await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            
            cleanup_result = {
                "executions_deleted": executions_result.deleted_count,
                "errors_deleted": errors_result.deleted_count,
                "redis_keys_deleted": deleted_keys,
                "cutoff_date": cutoff_date.isoformat(),
                "cleanup_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"🧹 Pipeline cleanup completed: {cleanup_result}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"❌ Error during pipeline cleanup: {e}")
            return {"error": str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Health check cho pipeline management system"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {}
            }
            
            # Check MongoDB connection
            try:
                await self.db.command("ping")
                health_status["checks"]["mongodb"] = {
                    "status": "healthy",
                    "response_time_ms": 0  # Would need actual timing
                }
            except Exception as e:
                health_status["checks"]["mongodb"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                health_status["checks"]["redis"] = {
                    "status": "healthy",
                    "response_time_ms": 0  # Would need actual timing
                }
            except Exception as e:
                health_status["checks"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
            
            # Check pipeline execution health
            try:
                recent_failed = await self.pipeline_collection.count_documents({
                    "started_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)},
                    "status": PipelineStatus.FAILED.value
                })
                
                if recent_failed > 5:  # More than 5 failures in last hour
                    health_status["checks"]["pipeline_health"] = {
                        "status": "degraded",
                        "recent_failures": recent_failed
                    }
                    if health_status["status"] == "healthy":
                        health_status["status"] = "degraded"
                else:
                    health_status["checks"]["pipeline_health"] = {
                        "status": "healthy",
                        "recent_failures": recent_failed
                    }
            except Exception as e:
                health_status["checks"]["pipeline_health"] = {
                    "status": "unknown",
                    "error": str(e)
                }
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _execute_pipeline_background(
        self,
        execution_id: str,
        cities: List[str],
        categories: List[str],
        execution_type: PipelineExecutionType,
        user_id: str
    ):
        """Execute pipeline in background"""
        try:
            # Update status to running
            await self._update_pipeline_status(execution_id, PipelineStatus.RUNNING, "ingestion")
            
            # Import and run pipeline
            from pipelines.orchestration.pipeline_orchestrator import PipelineOrchestrator
            
            orchestrator = PipelineOrchestrator()
            results = await orchestrator.run_full_pipeline()
            
            # Update final status
            if results.get("overall_status") == "completed":
                await self._update_pipeline_status(execution_id, PipelineStatus.COMPLETED, "completed")
            else:
                await self._update_pipeline_status(execution_id, PipelineStatus.FAILED, "completed")
                await self._log_error(execution_id, "pipeline_execution", f"Pipeline failed: {results.get('overall_status')}")
            
        except Exception as e:
            await self._update_pipeline_status(execution_id, PipelineStatus.FAILED, "completed")
            await self._log_error(execution_id, "pipeline_execution", str(e))
    
    async def _update_pipeline_status(
        self,
        execution_id: str,
        status: PipelineStatus,
        current_stage: str,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Update pipeline status và progress"""
        try:
            update_data = {
                "status": status.value,
                "current_stage": current_stage,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if status == PipelineStatus.COMPLETED:
                update_data["completed_at"] = datetime.now(timezone.utc)
            elif status == PipelineStatus.FAILED:
                update_data["completed_at"] = datetime.now(timezone.utc)
            
            if metrics:
                update_data["metrics"] = metrics
            
            await self.pipeline_collection.update_one(
                {"_id": execution_id},
                {"$set": update_data}
            )
            
            # Update Redis cache
            await self.redis_client.setex(
                f"pipeline:{execution_id}",
                3600,
                json.dumps({
                    "status": status.value,
                    "current_stage": current_stage,
                    "progress": self._calculate_progress_from_status(status)
                })
            )
            
        except Exception as e:
            logger.error(f"❌ Error updating pipeline status {execution_id}: {e}")
    
    async def _log_error(self, execution_id: str, error_type: str, error_message: str, stack_trace: Optional[str] = None):
        """Log error to errors collection"""
        try:
            error_record = {
                "execution_id": execution_id,
                "error_type": error_type,
                "error_message": error_message,
                "severity": "error",
                "timestamp": datetime.now(timezone.utc),
                "stack_trace": stack_trace,
                "context": {
                    "service": "pipeline_management",
                    "environment": "production"
                }
            }
            
            await self.errors_collection.insert_one(error_record)
            
        except Exception as e:
            logger.error(f"❌ Error logging error: {e}")
    
    def _calculate_progress(self, execution: Dict[str, Any]) -> float:
        """Calculate pipeline progress percentage"""
        try:
            stages = execution.get("stages", {})
            completed_stages = sum(1 for stage in stages.values() if stage.get("status") == "completed")
            total_stages = len(stages)
            
            if total_stages == 0:
                return 0.0
            
            return (completed_stages / total_stages) * 100
            
        except Exception:
            return 0.0
    
    def _calculate_progress_from_status(self, status: PipelineStatus) -> float:
        """Calculate progress from status"""
        progress_map = {
            PipelineStatus.PENDING: 0,
            PipelineStatus.RUNNING: 50,
            PipelineStatus.VALIDATING: 25,
            PipelineStatus.TRANSFORMING: 50,
            PipelineStatus.ENRICHING: 75,
            PipelineStatus.COMPLETED: 100,
            PipelineStatus.FAILED: 0,
            PipelineStatus.CANCELLED: 0,
            PipelineStatus.PAUSED: None
        }
        return progress_map.get(status, 0)
    
    def _calculate_duration(self, execution: Dict[str, Any]) -> Optional[float]:
        """Calculate pipeline duration in seconds"""
        try:
            started_at = execution.get("started_at")
            completed_at = execution.get("completed_at")
            
            if started_at and completed_at:
                if isinstance(started_at, str):
                    started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                if isinstance(completed_at, str):
                    completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                
                return (completed_at - started_at).total_seconds()
            
            return None
            
        except Exception:
            return None
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string thành timedelta"""
        time_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        return time_map.get(time_range, timedelta(hours=24))


# ============================================
# UTILITY FUNCTIONS
# ============================================
def calculate_pipeline_progress(
    records_processed: int, 
    total_records: int
) -> float:
    """
    Calculate pipeline progress percentage
    
    Args:
        records_processed: Số records đã xử lý
        total_records: Tổng số records cần xử lý
        
    Returns:
        Progress percentage từ 0.0 đến 100.0
        
    Example:
        >>> calculate_pipeline_progress(500, 1000)
        50.0
    """
    # Kiểm tra division by zero
    if total_records == 0:
        return 0.0
    
    # Calculate percentage
    percentage = (records_processed / total_records) * 100
    
    # Clamp to 0-100 range
    return min(max(percentage, 0.0), 100.0)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds thành human-readable string
    
    Args:
        seconds: Thời gian tính bằng giây
        
    Returns:
        Formatted string như "2h 15m 30s" hoặc "45s"
        
    Example:
        >>> format_duration(7500)
        '2h 5m 0s'
        
        >>> format_duration(45)
        '45s'
    """
    # Kiểm tra invalid input
    if seconds is None or seconds < 0:
        return "N/A"
    
    # Calculate hours, minutes, seconds
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    # Build result string
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


# ============================================
# MODULE EXPORTS
# ============================================
# Export các components chính của module
__all__ = [
    "PipelineManagementService",
    "PipelineStatus",
    "PipelineExecutionType",
    "calculate_pipeline_progress",
    "format_duration",
]
