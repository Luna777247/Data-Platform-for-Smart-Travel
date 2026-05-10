"""
Quality Models
==============

MongoDB models cho data quality management.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/db/models/quality.py
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class QualityDimensionScore(BaseModel):
    """Quality score cho một dimension."""
    dimension: str  # completeness, accuracy, consistency, timeliness, uniqueness
    score: float  # 0-1
    weight: float = 0.2
    issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class QualityReport(BaseModel):
    """Data quality report."""
    report_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    city: str
    layer: str  # bronze, silver, gold
    overall_score: float  # 0-1
    
    # Dimension scores
    completeness_score: QualityDimensionScore
    accuracy_score: QualityDimensionScore
    consistency_score: QualityDimensionScore
    timeliness_score: QualityDimensionScore
    uniqueness_score: QualityDimensionScore
    
    # Summary
    total_records: int
    passed_records: int
    failed_records: int
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    
    # Metadata
    generated_by: str = "quality_monitor"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "qr-001",
                "timestamp": "2026-01-01T00:00:00",
                "city": "hanoi",
                "layer": "silver",
                "overall_score": 0.85,
                "total_records": 1000
            }
        }


class QualityRule(BaseModel):
    """Data quality validation rule."""
    rule_id: str
    name: str
    description: str
    layer: str  # bronze, silver, gold
    
    # Rule configuration
    field: str  # Field to validate
    rule_type: str  # required, format, range, regex, custom
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Severity
    severity: str = "error"  # error, warning, info
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "rule-001",
                "name": "Required Place ID",
                "description": "place_id field must be present",
                "layer": "silver",
                "field": "place_id",
                "rule_type": "required"
            }
        }


class QualityIssue(BaseModel):
    """Individual quality issue."""
    issue_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Issue details
    city: str
    layer: str
    rule_id: str
    severity: str
    
    # Record info
    record_id: str  # place_id or other identifier
    field: str
    issue_type: str
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    
    # Resolution
    status: str = "open"  # open, acknowledged, resolved, false_positive
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "issue_id": "issue-001",
                "timestamp": "2026-01-01T00:00:00",
                "city": "hanoi",
                "layer": "silver",
                "rule_id": "rule-001",
                "record_id": "place-123",
                "field": "place_id",
                "issue_type": "missing_required",
                "message": "place_id is required but missing"
            }
        }
