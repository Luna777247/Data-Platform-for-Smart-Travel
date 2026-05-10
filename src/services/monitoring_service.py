"""
Monitoring Service
==================

Business logic cho system monitoring.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/services/monitoring_service.py

Responsibilities:
- System metrics collection
- Health checks
- Performance monitoring
- Alert management
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.core.database import mongodb_manager, redis_manager
from src.pipelines.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service cho system monitoring.
    
    Provides:
    - System status monitoring
    - Dependency health checks
    - Metrics collection
    - Performance tracking
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        logger.info("MonitoringService initialized")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Check MongoDB
        try:
            if mongodb_manager.is_connected:
                status["components"]["mongodb"] = {
                    "status": "connected",
                    "healthy": True
                }
            else:
                status["components"]["mongodb"] = {
                    "status": "disconnected",
                    "healthy": False
                }
                status["status"] = "degraded"
        except Exception as e:
            status["components"]["mongodb"] = {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
            status["status"] = "degraded"
        
        # Check Redis
        try:
            if redis_manager.is_connected:
                status["components"]["redis"] = {
                    "status": "connected",
                    "healthy": True
                }
            else:
                status["components"]["redis"] = {
                    "status": "disconnected",
                    "healthy": False
                }
                status["status"] = "degraded"
        except Exception as e:
            status["components"]["redis"] = {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
            status["status"] = "degraded"
        
        return status
    
    async def get_dependencies_status(self) -> Dict[str, Any]:
        """Get dependencies health status."""
        return await self.get_system_status()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return self.metrics.get_summary()
    
    async def get_version_info(self) -> Dict[str, str]:
        """Get API version information."""
        return {
            "version": "1.0.0",
            "name": "Smart Tourism Data Platform API",
            "build": "2026-05-09",
            "environment": "production"
        }
    
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline-specific metrics."""
        return {
            "pipelines_24h": 0,
            "success_rate": 0,
            "average_duration": 0,
            "total_records": 0
        }
