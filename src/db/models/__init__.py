"""
Database Models Package
=======================
MongoDB models cho Smart Tourism Data Platform

Models:
- pipeline: Pipeline execution, configuration models
- poi: Point of Interest models (raw, cleaned, master)
- monitoring: Metrics, alerts models
- quality: Data quality, validation models

All models sử dụng Beanie ODM cho MongoDB async operations.
"""

from .pipeline import (
    PyObjectId,
    PipelineStatus,
    PipelineExecutionType,
    SeverityLevel,
    MongoBaseModel,
    PipelineRegistry,
    PipelineExecution,
    PipelineStageExecution,
    PipelineError,
)
from .poi import (
    POICategory,
    POISource,
    PriceLevel,
    GeoLocation,
    Address,
    Rating,
    OpeningHours,
    ContactInfo,
    MasterPOI,
    POIReview,
    POICategoryInfo,
    POIListResponse,
    POINearbyRequest,
)
from .monitoring import (
    SystemMetric,
    HealthCheck,
    LogEntry,
    Alert,
)
from .quality import (
    QualityDimensionScore,
    QualityReport,
    QualityRule,
    QualityIssue,
)

__all__ = [
    # Pipeline models
    "PyObjectId",
    "PipelineStatus",
    "PipelineExecutionType",
    "SeverityLevel",
    "MongoBaseModel",
    "PipelineRegistry",
    "PipelineExecution",
    "PipelineStageExecution",
    "PipelineError",
    # POI models
    "POICategory",
    "POISource",
    "PriceLevel",
    "GeoLocation",
    "Address",
    "Rating",
    "OpeningHours",
    "ContactInfo",
    "MasterPOI",
    "POIReview",
    "POICategoryInfo",
    "POIListResponse",
    "POINearbyRequest",
    # Monitoring models
    "SystemMetric",
    "HealthCheck",
    "LogEntry",
    "Alert",
    # Quality models
    "QualityDimensionScore",
    "QualityReport",
    "QualityRule",
    "QualityIssue",
]