"""
Data Quality Monitor
====================

Quality monitoring cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/monitoring/quality_monitor.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityDimension:
    """Quality dimension score."""
    name: str
    score: float  # 0-1
    weight: float
    details: Dict[str, Any]


class QualityMonitor:
    """
    Monitor và report data quality cho pipeline outputs.
    
    Quality Dimensions:
    1. Completeness - Missing data ratio
    2. Accuracy - Data validation results
    3. Consistency - Cross-field consistency
    4. Timeliness - Data freshness
    5. Uniqueness - Duplicate ratio
    """
    
    def __init__(self):
        self.quality_reports: List[Dict[str, Any]] = []
        self.dimension_weights = {
            "completeness": 0.25,
            "accuracy": 0.25,
            "consistency": 0.2,
            "timeliness": 0.15,
            "uniqueness": 0.15
        }
        logger.info("QualityMonitor initialized")
    
    def assess_quality(
        self,
        records: List[Dict[str, Any]],
        stage: str,
        city: str
    ) -> Dict[str, Any]:
        """
        Assess quality của một dataset.
        
        Returns:
            Quality report with scores cho tất cả dimensions
        """
        total_records = len(records)
        
        if total_records == 0:
            return self._create_empty_report(stage, city)
        
        # Calculate each dimension
        completeness = self._assess_completeness(records)
        accuracy = self._assess_accuracy(records)
        consistency = self._assess_consistency(records)
        timeliness = self._assess_timeliness(records)
        uniqueness = self._assess_uniqueness(records)
        
        # Calculate overall score
        dimensions = [
            QualityDimension("completeness", completeness, 0.25, {}),
            QualityDimension("accuracy", accuracy, 0.25, {}),
            QualityDimension("consistency", consistency, 0.2, {}),
            QualityDimension("timeliness", timeliness, 0.15, {}),
            QualityDimension("uniqueness", uniqueness, 0.15, {})
        ]
        
        overall_score = sum(
            d.score * d.weight for d in dimensions
        )
        
        # Create report
        report = {
            "report_id": f"quality_{stage}_{city}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "stage": stage,
            "city": city,
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": total_records,
            "overall_score": round(overall_score, 3),
            "dimensions": {
                d.name: {
                    "score": round(d.score, 3),
                    "weight": d.weight,
                    "details": d.details
                }
                for d in dimensions
            },
            "grade": self._get_grade(overall_score),
            "recommendations": self._generate_recommendations(dimensions)
        }
        
        self.quality_reports.append(report)
        
        logger.info(
            f"Quality report: {stage}/{city} = {overall_score:.3f} "
            f"({report['grade']})"
        )
        
        return report
    
    def _assess_completeness(self, records: List[Dict[str, Any]]) -> float:
        """Assess data completeness."""
        required_fields = [
            "name", "location", "categories", "city"
        ]
        
        total_fields = len(records) * len(required_fields)
        present_fields = 0
        
        for record in records:
            for field in required_fields:
                if record.get(field):
                    present_fields += 1
        
        return present_fields / total_fields if total_fields > 0 else 1.0
    
    def _assess_accuracy(self, records: List[Dict[str, Any]]) -> float:
        """Assess data accuracy."""
        valid_records = 0
        
        for record in records:
            is_valid = True
            
            # Check coordinates
            location = record.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            
            if lat is None or lng is None:
                is_valid = False
            elif not (-90 <= lat <= 90 and -180 <= lng <= 180):
                is_valid = False
            
            # Check rating range
            rating = record.get("rating", 0)
            if rating and not (0 <= rating <= 5):
                is_valid = False
            
            if is_valid:
                valid_records += 1
        
        return valid_records / len(records) if records else 1.0
    
    def _assess_consistency(self, records: List[Dict[str, Any]]) -> float:
        """Assess data consistency."""
        consistent_records = 0
        
        for record in records:
            is_consistent = True
            
            # Check city matches
            record_city = record.get("city", "").lower()
            
            # Check category consistency
            categories = record.get("categories", [])
            if isinstance(categories, str):
                categories = [categories]
            
            if not categories:
                is_consistent = False
            
            if is_consistent:
                consistent_records += 1
        
        return consistent_records / len(records) if records else 1.0
    
    def _assess_timeliness(self, records: List[Dict[str, Any]]) -> float:
        """Assess data timeliness."""
        from datetime import timedelta
        
        now = datetime.utcnow()
        fresh_records = 0
        
        for record in records:
            ingested_at = record.get("ingested_at")
            if ingested_at:
                try:
                    ingested_time = datetime.fromisoformat(
                        ingested_at.replace('Z', '+00:00')
                    )
                    age = now - ingested_time
                    
                    # Data less than 7 days old is fresh
                    if age <= timedelta(days=7):
                        fresh_records += 1
                except:
                    pass
        
        return fresh_records / len(records) if records else 1.0
    
    def _assess_uniqueness(self, records: List[Dict[str, Any]]) -> float:
        """Assess data uniqueness."""
        if not records:
            return 1.0
        
        # Check for duplicates based on name + coordinates
        seen = set()
        unique_records = 0
        
        for record in records:
            name = record.get("name", "").lower().strip()
            location = record.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            
            if lat and lng:
                # Round to 3 decimal places for comparison
                key = (name, round(lat, 3), round(lng, 3))
            else:
                key = name
            
            if key not in seen:
                seen.add(key)
                unique_records += 1
        
        return unique_records / len(records)
    
    def _get_grade(self, score: float) -> str:
        """Get letter grade from score."""
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "B+"
        elif score >= 0.80:
            return "B"
        elif score >= 0.75:
            return "C+"
        elif score >= 0.70:
            return "C"
        else:
            return "F"
    
    def _generate_recommendations(
        self,
        dimensions: List[QualityDimension]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        for dim in dimensions:
            if dim.score < 0.7:
                recommendations.append(
                    f"Improve {dim.name}: current score {dim.score:.2f}"
                )
            elif dim.score < 0.8:
                recommendations.append(
                    f"Consider improving {dim.name}"
                )
        
        return recommendations
    
    def _create_empty_report(
        self,
        stage: str,
        city: str
    ) -> Dict[str, Any]:
        """Create report cho empty dataset."""
        return {
            "report_id": f"quality_{stage}_{city}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "stage": stage,
            "city": city,
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": 0,
            "overall_score": 0.0,
            "dimensions": {},
            "grade": "N/A",
            "recommendations": ["No data available for quality assessment"]
        }
    
    def get_quality_trend(
        self,
        stage: str,
        city: str,
        last_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get quality trend cho stage/city."""
        reports = [
            r for r in self.quality_reports
            if r["stage"] == stage and r["city"] == city
        ]
        
        return sorted(
            reports,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:last_n]
    
    def get_latest_report(
        self,
        stage: str,
        city: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest quality report."""
        reports = self.get_quality_trend(stage, city, 1)
        return reports[0] if reports else None
    
    def get_average_quality(
        self,
        stage: Optional[str] = None,
        city: Optional[str] = None
    ) -> float:
        """Get average quality score."""
        reports = self.quality_reports
        
        if stage:
            reports = [r for r in reports if r["stage"] == stage]
        
        if city:
            reports = [r for r in reports if r["city"] == city]
        
        if not reports:
            return 0.0
        
        return sum(r["overall_score"] for r in reports) / len(reports)
