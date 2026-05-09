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
    PipelineDefinition,
    PipelineExecution,
    ExecutionStage,
    PipelineConfiguration,
    ExecutionLog,
    ScheduleConfiguration,
    StageConfiguration,
)
from .poi import (
    POI,
    Location,
    POICategory,
    OperatingHours,
    POIRating,
    POIReview,
    POIContact,
    POIAmenity,
    PriceRange,
    AccessibilityInfo,
    POIImage,
    POIValidation,
    POIMetadata,
)

__all__ = [
    # Pipeline models
    "PipelineDefinition",
    "PipelineExecution",
    "ExecutionStage",
    "PipelineConfiguration",
    "ExecutionLog",
    "ScheduleConfiguration",
    "StageConfiguration",
    # POI models
    "POI",
    "Location",
    "POICategory",
    "OperatingHours",
    "POIRating",
    "POIReview",
    "POIContact",
    "POIAmenity",
    "PriceRange",
    "AccessibilityInfo",
    "POIImage",
    "POIValidation",
    "POIMetadata",
]