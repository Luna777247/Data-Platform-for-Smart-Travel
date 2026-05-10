"""
Monitoring Models
=================

MongoDB models cho monitoring data.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/db/models/monitoring.py
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SystemMetric(BaseModel):
    """System metric record."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    unit: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-01T00:00:00",
                "metric_name": "cpu_usage",
                "value": 45.5,
                "labels": {"host": "api-1"},
                "unit": "percent"
            }
        }


class HealthCheck(BaseModel):
    """Health check record."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-01T00:00:00",
                "component": "mongodb",
                "status": "healthy",
                "response_time_ms": 50.0
            }
        }


class LogEntry(BaseModel):
    """Application log entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger: str
    message: str
    correlation_id: Optional[str] = None
    source: Dict[str, Any] = Field(default_factory=dict)
    extra: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-01T00:00:00",
                "level": "INFO",
                "logger": "src.api.routes",
                "message": "Request completed",
                "correlation_id": "abc-123"
            }
        }


class Alert(BaseModel):
    """Alert record."""
    alert_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: str  # low, medium, high, critical
    category: str  # pipeline, quality, performance, system
    title: str
    message: str
    source: str
    status: str = "active"  # active, acknowledged, resolved
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert-001",
                "timestamp": "2026-01-01T00:00:00",
                "severity": "high",
                "category": "pipeline",
                "title": "Pipeline failure",
                "message": "Bronze pipeline failed for hanoi",
                "source": "pipeline_orchestrator"
            }
        }
