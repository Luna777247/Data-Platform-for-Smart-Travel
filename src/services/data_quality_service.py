"""
Data Quality Service
====================

Business logic cho data quality management.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/services/data_quality_service.py

Responsibilities:
- Quality score calculation
- Quality report generation
- Data validation
- Anomaly detection
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.pipelines.monitoring import QualityMonitor

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Service cho data quality management.
    
    Provides:
    - Quality checking cho data layers
    - Quality report generation
    - Data validation
    - Quality trend analysis
    """
    
    def __init__(self):
        self.quality_monitor = QualityMonitor()
        logger.info("DataQualityService initialized")
    
    async def check_silver_quality(
        self,
        city: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check quality của silver layer data."""
        score = await self.quality_monitor.check_silver_quality(city, data)
        report = self.quality_monitor.get_latest_report(city, "silver")
        
        return {
            "city": city,
            "layer": "silver",
            "overall_score": score,
            "is_acceptable": score >= self.quality_monitor.min_quality_threshold,
            "dimension_scores": {
                k: {"score": v.score, "issues": len(v.issues)}
                for k, v in report.dimension_scores.items()
            } if report else {},
            "recommendations": report.recommendations if report else [],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_quality_report(
        self,
        city: str,
        layer: str = "silver"
    ) -> Optional[Dict[str, Any]]:
        """Lấy quality report cho city/layer."""
        report = self.quality_monitor.get_latest_report(city, layer)
        
        if not report:
            return None
        
        return {
            "city": report.city,
            "layer": report.layer,
            "overall_score": report.overall_score,
            "record_count": report.record_count,
            "dimension_scores": {
                k: {
                    "score": v.score,
                    "issues": v.issues,
                    "details": v.details
                }
                for k, v in report.dimension_scores.items()
            },
            "recommendations": report.recommendations,
            "timestamp": report.timestamp.isoformat()
        }
    
    async def get_quality_trends(
        self,
        city: str,
        layer: str = "silver",
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Lấy quality trends cho city."""
        reports = self.quality_monitor.get_all_reports(
            city=city,
            stage=layer,
            limit=days * 10  # Assume multiple reports per day
        )
        
        # Group by day
        trends = []
        for report in reports:
            trends.append({
                "timestamp": report.timestamp.isoformat(),
                "overall_score": report.overall_score,
                "record_count": report.record_count
            })
        
        return trends
    
    async def validate_data(
        self,
        data: List[Dict[str, Any]],
        validation_rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate data against rules."""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["place_id", "name", "location"]
        
        for i, record in enumerate(data):
            # Check required fields
            for field in required_fields:
                if not record.get(field):
                    errors.append({
                        "record_index": i,
                        "field": field,
                        "error": f"Missing required field: {field}"
                    })
            
            # Check coordinates
            location = record.get("location", {})
            if not (location.get("lat") and location.get("lng")):
                errors.append({
                    "record_index": i,
                    "field": "location",
                    "error": "Invalid coordinates"
                })
            
            # Check rating range
            rating = record.get("rating")
            if rating is not None and (rating < 0 or rating > 5):
                errors.append({
                    "record_index": i,
                    "field": "rating",
                    "error": f"Rating {rating} out of range [0, 5]"
                })
        
        return {
            "total_records": len(data),
            "valid_records": len(data) - len(set(e["record_index"] for e in errors)),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:100],  # Limit errors
            "warnings": warnings[:100]
        }
