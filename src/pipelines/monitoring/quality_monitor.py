"""
Quality Monitor
===============

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/monitoring/quality_monitor.py

Monitor data quality cho pipeline outputs.
Tính toán quality scores và detect data quality issues.

Quality dimensions:
- Completeness: Missing values
- Accuracy: Data validity
- Consistency: Cross-field consistency
- Timeliness: Data freshness
- Uniqueness: Duplicate detection
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Data quality dimensions."""
    COMPLETENESS = "completeness"    # Missing values
    ACCURACY = "accuracy"            # Data validity
    CONSISTENCY = "consistency"      # Cross-field consistency
    TIMELINESS = "timeliness"        # Data freshness
    UNIQUENESS = "uniqueness"        # Duplicate detection


@dataclass
class QualityScore:
    """Quality score cho một dimension."""
    dimension: QualityDimension
    score: float  # 0-1
    issues: List[str]
    details: Dict[str, Any]


@dataclass
class QualityReport:
    """Full quality report."""
    city: str
    stage: str
    overall_score: float
    dimension_scores: Dict[str, QualityScore]
    timestamp: datetime
    record_count: int
    recommendations: List[str]


class QualityMonitor:
    """
    Monitor data quality cho pipeline outputs.
    
    Tính toán quality scores theo 5 dimensions:
    - Completeness: % fields có giá trị
    - Accuracy: % giá trị hợp lệ
    - Consistency: % records nhất quán
    - Timeliness: % data up-to-date
    - Uniqueness: % records unique
    
    Usage:
        monitor = QualityMonitor()
        
        # Check silver layer quality
        score = await monitor.check_silver_quality(city="hanoi", data=pois)
        
        # Get full report
        report = monitor.generate_report(city="hanoi", stage="silver")
    """
    
    # Critical fields that must have values
    CRITICAL_FIELDS = [
        "place_id",
        "name",
        "location.lat",
        "location.lng",
        "category"
    ]
    
    # Valid coordinates range for Vietnam
    VN_LAT_RANGE = (8.0, 23.5)
    VN_LNG_RANGE = (102.0, 110.0)
    
    def __init__(self, min_quality_threshold: float = 0.7):
        self.min_quality_threshold = min_quality_threshold
        self._reports: List[QualityReport] = []
        
        logger.info(f"QualityMonitor initialized (threshold={min_quality_threshold})")
    
    async def check_silver_quality(
        self,
        city: str,
        data: List[Dict[str, Any]]
    ) -> float:
        """
        Check quality của silver layer data.
        
        Args:
            city: Tên thành phố
            data: List POI data
            
        Returns:
            Overall quality score (0-1)
        """
        if not data:
            logger.warning(f"No data to check quality for {city}")
            return 0.0
        
        record_count = len(data)
        
        # Check each dimension
        completeness = self._check_completeness(data)
        accuracy = self._check_accuracy(data)
        consistency = self._check_consistency(data)
        uniqueness = self._check_uniqueness(data)
        timeliness = self._check_timeliness(data)
        
        # Calculate overall score (weighted average)
        weights = {
            QualityDimension.COMPLETENESS: 0.3,
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.CONSISTENCY: 0.2,
            QualityDimension.UNIQUENESS: 0.15,
            QualityDimension.TIMELINESS: 0.1
        }
        
        overall_score = sum(
            score.score * weights[dimension]
            for dimension, score in [
                (QualityDimension.COMPLETENESS, completeness),
                (QualityDimension.ACCURACY, accuracy),
                (QualityDimension.CONSISTENCY, consistency),
                (QualityDimension.UNIQUENESS, uniqueness),
                (QualityDimension.TIMELINESS, timeliness)
            ]
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            completeness, accuracy, consistency, uniqueness, timeliness
        )
        
        # Create report
        report = QualityReport(
            city=city,
            stage="silver",
            overall_score=overall_score,
            dimension_scores={
                d.value: s for d, s in [
                    (QualityDimension.COMPLETENESS, completeness),
                    (QualityDimension.ACCURACY, accuracy),
                    (QualityDimension.CONSISTENCY, consistency),
                    (QualityDimension.UNIQUENESS, uniqueness),
                    (QualityDimension.TIMELINESS, timeliness)
                ]
            },
            timestamp=datetime.utcnow(),
            record_count=record_count,
            recommendations=recommendations
        )
        
        self._reports.append(report)
        
        # Log quality status
        status = "PASS" if overall_score >= self.min_quality_threshold else "FAIL"
        logger.info(f"Quality check {status} for {city}: {overall_score:.2f} "
                   f"({record_count} records)")
        
        return overall_score
    
    def _check_completeness(self, data: List[Dict]) -> QualityScore:
        """Check completeness - % fields có giá trị."""
        issues = []
        total_fields = 0
        filled_fields = 0
        
        for record in data:
            for field in self.CRITICAL_FIELDS:
                total_fields += 1
                value = self._get_nested_value(record, field)
                if value is not None and value != "":
                    filled_fields += 1
                else:
                    if len(issues) < 10:  # Limit issues
                        issues.append(f"Missing {field} in record {record.get('place_id', 'unknown')}")
        
        score = filled_fields / total_fields if total_fields > 0 else 0
        
        return QualityScore(
            dimension=QualityDimension.COMPLETENESS,
            score=score,
            issues=issues,
            details={
                "total_fields": total_fields,
                "filled_fields": filled_fields,
                "missing_percentage": (1 - score) * 100
            }
        )
    
    def _check_accuracy(self, data: List[Dict]) -> QualityScore:
        """Check accuracy - % giá trị hợp lệ."""
        issues = []
        valid_count = 0
        total_count = len(data)
        
        for record in data:
            is_valid = True
            
            # Check coordinates
            lat = self._get_nested_value(record, "location.lat")
            lng = self._get_nested_value(record, "location.lng")
            
            if lat is not None and lng is not None:
                if not (self.VN_LAT_RANGE[0] <= lat <= self.VN_LAT_RANGE[1]):
                    is_valid = False
                    if len(issues) < 10:
                        issues.append(f"Invalid latitude {lat} for {record.get('place_id')}")
                
                if not (self.VN_LNG_RANGE[0] <= lng <= self.VN_LNG_RANGE[1]):
                    is_valid = False
                    if len(issues) < 10:
                        issues.append(f"Invalid longitude {lng} for {record.get('place_id')}")
            
            # Check rating range
            rating = record.get("rating")
            if rating is not None and (rating < 0 or rating > 5):
                is_valid = False
                if len(issues) < 10:
                    issues.append(f"Invalid rating {rating} for {record.get('place_id')}")
            
            if is_valid:
                valid_count += 1
        
        score = valid_count / total_count if total_count > 0 else 0
        
        return QualityScore(
            dimension=QualityDimension.ACCURACY,
            score=score,
            issues=issues,
            details={
                "valid_records": valid_count,
                "total_records": total_count,
                "invalid_percentage": (1 - score) * 100
            }
        )
    
    def _check_consistency(self, data: List[Dict]) -> QualityScore:
        """Check consistency - cross-field consistency."""
        issues = []
        consistent_count = 0
        total_count = len(data)
        
        for record in data:
            is_consistent = True
            
            # Check: Nếu có user_ratings_total thì phải có rating
            if record.get("user_ratings_total", 0) > 0 and record.get("rating") is None:
                is_consistent = False
                if len(issues) < 10:
                    issues.append(f"Inconsistent: has reviews but no rating for {record.get('place_id')}")
            
            # Check: Opening hours consistency
            if record.get("opening_hours") and not record.get("business_status"):
                is_consistent = False
                if len(issues) < 10:
                    issues.append(f"Inconsistent: has hours but no business_status for {record.get('place_id')}")
            
            if is_consistent:
                consistent_count += 1
        
        score = consistent_count / total_count if total_count > 0 else 0
        
        return QualityScore(
            dimension=QualityDimension.CONSISTENCY,
            score=score,
            issues=issues,
            details={
                "consistent_records": consistent_count,
                "total_records": total_count
            }
        )
    
    def _check_uniqueness(self, data: List[Dict]) -> QualityScore:
        """Check uniqueness - duplicate detection."""
        issues = []
        seen_ids = set()
        duplicates = []
        
        for record in data:
            place_id = record.get("place_id")
            if place_id:
                if place_id in seen_ids:
                    duplicates.append(place_id)
                else:
                    seen_ids.add(place_id)
        
        unique_count = len(seen_ids)
        total_count = len(data)
        duplicate_count = len(duplicates)
        
        score = unique_count / total_count if total_count > 0 else 0
        
        if duplicates:
            issues = [f"Duplicate place_ids: {list(set(duplicates))[:5]}"]
        
        return QualityScore(
            dimension=QualityDimension.UNIQUENESS,
            score=score,
            issues=issues,
            details={
                "unique_records": unique_count,
                "total_records": total_count,
                "duplicates": duplicate_count
            }
        )
    
    def _check_timeliness(self, data: List[Dict]) -> QualityScore:
        """Check timeliness - data freshness."""
        issues = []
        current_time = datetime.utcnow()
        
        # Assume data should be updated within 30 days
        max_age_days = 30
        
        fresh_count = 0
        total_count = len(data)
        
        for record in data:
            # Check updated_at timestamp
            updated_at = record.get("updated_at")
            if updated_at:
                try:
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    
                    age_days = (current_time - updated_at).days
                    if age_days <= max_age_days:
                        fresh_count += 1
                    elif len(issues) < 10:
                        issues.append(f"Stale data: {record.get('place_id')} updated {age_days} days ago")
                except Exception:
                    # If we can't parse date, count as fresh
                    fresh_count += 1
            else:
                # No timestamp, assume fresh
                fresh_count += 1
        
        score = fresh_count / total_count if total_count > 0 else 0
        
        return QualityScore(
            dimension=QualityDimension.TIMELINESS,
            score=score,
            issues=issues,
            details={
                "fresh_records": fresh_count,
                "total_records": total_count,
                "max_age_days": max_age_days
            }
        )
    
    def _get_nested_value(self, obj: Dict, path: str) -> Any:
        """Get nested value từ dict bằng dot notation."""
        keys = path.split(".")
        value = obj
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _generate_recommendations(
        self,
        completeness: QualityScore,
        accuracy: QualityScore,
        consistency: QualityScore,
        uniqueness: QualityScore,
        timeliness: QualityScore
    ) -> List[str]:
        """Generate recommendations based on quality scores."""
        recommendations = []
        
        if completeness.score < 0.8:
            recommendations.append(
                f"Improve data completeness: {completeness.details.get('missing_percentage', 0):.1f}% fields missing"
            )
        
        if accuracy.score < 0.9:
            recommendations.append(
                f"Validate data accuracy: {accuracy.details.get('invalid_percentage', 0):.1f}% records invalid"
            )
        
        if consistency.score < 0.9:
            recommendations.append("Review data consistency rules")
        
        if uniqueness.score < 0.95:
            dup_count = uniqueness.details.get("duplicates", 0)
            recommendations.append(f"Remove {dup_count} duplicate records")
        
        if timeliness.score < 0.8:
            recommendations.append("Schedule data refresh to improve freshness")
        
        return recommendations
    
    def get_latest_report(self, city: str, stage: str) -> Optional[QualityReport]:
        """Lấy latest quality report cho city/stage."""
        matching = [
            r for r in self._reports
            if r.city == city and r.stage == stage
        ]
        
        if not matching:
            return None
        
        # Return most recent
        return max(matching, key=lambda r: r.timestamp)
    
    def get_all_reports(
        self,
        city: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 100
    ) -> List[QualityReport]:
        """Lấy all quality reports."""
        reports = self._reports
        
        if city:
            reports = [r for r in reports if r.city == city]
        if stage:
            reports = [r for r in reports if r.stage == stage]
        
        # Sort by timestamp descending
        reports.sort(key=lambda r: r.timestamp, reverse=True)
        
        return reports[:limit]
    
    def is_quality_acceptable(self, city: str, stage: str) -> bool:
        """Check if quality is acceptable for city/stage."""
        report = self.get_latest_report(city, stage)
        
        if not report:
            return False
        
        return report.overall_score >= self.min_quality_threshold
    
    def cleanup_old_reports(self, max_age_days: int = 7) -> int:
        """Xóa old quality reports."""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(days=max_age_days)
        
        old_count = len(self._reports)
        self._reports = [r for r in self._reports if r.timestamp >= cutoff]
        removed = old_count - len(self._reports)
        
        logger.info(f"Cleaned up {removed} old quality reports")
        return removed
