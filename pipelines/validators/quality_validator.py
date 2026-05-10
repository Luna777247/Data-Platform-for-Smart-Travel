"""
Quality Validator
=================

Quality validation cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/validators/quality_validator.py
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class QualityValidator:
    """
    Validate data quality based on rules.
    
    Checks:
    - Field presence
    - Data type correctness
    - Range validation
    - Format validation
    """
    
    def __init__(self, quality_threshold: float = 0.8):
        self.quality_threshold = quality_threshold
        self.rules: List[Dict[str, Any]] = []
        self._load_default_rules()
        logger.info("QualityValidator initialized")
    
    def _load_default_rules(self):
        """Load default quality rules."""
        self.rules = [
            {
                "name": "required_fields",
                "check": self._check_required_fields,
                "weight": 0.3
            },
            {
                "name": "coordinate_validity",
                "check": self._check_coordinates,
                "weight": 0.3
            },
            {
                "name": "rating_range",
                "check": self._check_rating_range,
                "weight": 0.2
            },
            {
                "name": "category_validity",
                "check": self._check_category,
                "weight": 0.2
            }
        ]
    
    def validate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate một record.
        
        Returns:
            Validation result with score and issues
        """
        issues = []
        total_weight = 0
        passed_weight = 0
        
        for rule in self.rules:
            weight = rule["weight"]
            total_weight += weight
            
            is_valid, rule_issues = rule["check"](record)
            
            if is_valid:
                passed_weight += weight
            else:
                issues.extend(rule_issues)
        
        score = passed_weight / total_weight if total_weight > 0 else 0
        
        return {
            "is_valid": score >= self.quality_threshold,
            "score": round(score, 3),
            "issues": issues,
            "passed_rules": sum(1 for r in self.rules if r["check"](record)[0]),
            "total_rules": len(self.rules)
        }
    
    def validate_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate batch of records."""
        results = [self.validate(r) for r in records]
        
        valid_count = sum(1 for r in results if r["is_valid"])
        total_score = sum(r["score"] for r in results)
        
        return {
            "total_records": len(records),
            "valid_records": valid_count,
            "invalid_records": len(records) - valid_count,
            "average_score": round(total_score / len(records), 3) if records else 0,
            "pass_rate": valid_count / len(records) if records else 0,
            "results": results
        }
    
    def _check_required_fields(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check required fields."""
        required = ["name", "location", "categories"]
        missing = [f for f in required if not record.get(f)]
        return len(missing) == 0, [f"Missing required field: {f}" for f in missing]
    
    def _check_coordinates(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check coordinate validity."""
        location = record.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        
        issues = []
        
        if lat is None or lng is None:
            issues.append("Missing coordinates")
        else:
            if not (-90 <= lat <= 90):
                issues.append(f"Invalid latitude: {lat}")
            if not (-180 <= lng <= 180):
                issues.append(f"Invalid longitude: {lng}")
        
        return len(issues) == 0, issues
    
    def _check_rating_range(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check rating is in valid range."""
        rating = record.get("rating")
        
        if rating is None:
            return True, []  # Rating is optional
        
        if not isinstance(rating, (int, float)):
            return False, ["Rating must be a number"]
        
        if not (0 <= rating <= 5):
            return False, [f"Rating {rating} out of range [0, 5]"]
        
        return True, []
    
    def _check_category(self, record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check category validity."""
        categories = record.get("categories", [])
        
        if not categories:
            return False, ["No categories specified"]
        
        return True, []
