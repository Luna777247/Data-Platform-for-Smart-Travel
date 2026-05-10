"""
Silver Layer Validation Module
==============================

Data validation cho Silver layer.
Theo RECOMMENDED_STRUCTURE.md - pipelines/silver/validation.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.utils.geo_utils import validate_coordinates
from src.utils.validation_utils import validate_required, validate_phone, validate_url

logger = logging.getLogger(__name__)


class SilverValidator:
    """
    Validate POI data cho Silver layer.
    
    Validation Rules:
    1. Required fields: name, location, category, city
    2. Coordinate validation: valid lat/lng
    3. Data type validation
    4. Business rule validation
    """
    
    def __init__(
        self,
        strict_mode: bool = True,
        skip_partial: bool = False
    ):
        self.strict_mode = strict_mode
        self.skip_partial = skip_partial
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        logger.info(f"SilverValidator initialized (strict={strict_mode})")
    
    def validate_record(
        self,
        record: Dict[str, Any],
        city: str
    ) -> Dict[str, Any]:
        """
        Validate một POI record.
        
        Args:
            record: POI record cần validate
            city: Thành phố reference
            
        Returns:
            Validation result với status và errors
        """
        self.errors = []
        self.warnings = []
        
        # Check required fields
        self._validate_required_fields(record)
        
        # Validate location
        self._validate_location(record)
        
        # Validate business data
        self._validate_business_data(record)
        
        # Validate metadata
        self._validate_metadata(record, city)
        
        # Build result
        result = {
            "is_valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "record_id": record.get("place_id", "unknown"),
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        # In non-strict mode, warnings don't invalidate
        if not self.strict_mode:
            result["is_valid"] = len(self.errors) == 0
        
        return result
    
    def validate_records(
        self,
        records: List[Dict[str, Any]],
        city: str
    ) -> List[Dict[str, Any]]:
        """Validate nhiều records."""
        return [self.validate_record(r, city) for r in records]
    
    def _validate_required_fields(self, record: Dict[str, Any]):
        """Validate required fields tồn tại."""
        required = ["name", "location", "categories", "city"]
        
        for field in required:
            value = record.get(field)
            
            if value is None:
                self.errors.append({
                    "field": field,
                    "error": "missing_required",
                    "message": f"Required field '{field}' is missing"
                })
            elif isinstance(value, str) and not value.strip():
                self.errors.append({
                    "field": field,
                    "error": "empty_required",
                    "message": f"Required field '{field}' is empty"
                })
            elif isinstance(value, list) and len(value) == 0:
                self.errors.append({
                    "field": field,
                    "error": "empty_list",
                    "message": f"Required field '{field}' has empty list"
                })
    
    def _validate_location(self, record: Dict[str, Any]):
        """Validate location data."""
        location = record.get("location", {})
        
        if not isinstance(location, dict):
            self.errors.append({
                "field": "location",
                "error": "invalid_type",
                "message": "Location must be an object"
            })
            return
        
        # Check lat/lng tồn tại
        lat = location.get("lat")
        lng = location.get("lng")
        
        if lat is None:
            self.errors.append({
                "field": "location.lat",
                "error": "missing",
                "message": "Latitude is missing"
            })
        
        if lng is None:
            self.errors.append({
                "field": "location.lng",
                "error": "missing",
                "message": "Longitude is missing"
            })
        
        # Validate coordinate values
        if lat is not None and lng is not None:
            if not validate_coordinates(lat, lng):
                self.errors.append({
                    "field": "location",
                    "error": "invalid_coordinates",
                    "message": f"Invalid coordinates: lat={lat}, lng={lng}"
                })
            
            # Check for default/null island
            if abs(lat) < 0.001 and abs(lng) < 0.001:
                self.warnings.append({
                    "field": "location",
                    "warning": "null_island",
                    "message": "Coordinates near null island (0,0)"
                })
    
    def _validate_business_data(self, record: Dict[str, Any]):
        """Validate business-specific data."""
        # Validate phone if present
        phone = record.get("phone")
        if phone:
            error = validate_phone(phone)
            if error:
                self.warnings.append({
                    "field": "phone",
                    "warning": "invalid_phone",
                    "message": error
                })
        
        # Validate website if present
        website = record.get("website")
        if website:
            if not validate_url(website):
                self.warnings.append({
                    "field": "website",
                    "warning": "invalid_url",
                    "message": f"Invalid URL: {website}"
                })
        
        # Validate rating
        rating = record.get("rating")
        if rating is not None:
            if not isinstance(rating, (int, float)):
                self.errors.append({
                    "field": "rating",
                    "error": "invalid_type",
                    "message": "Rating must be a number"
                })
            elif rating < 0 or rating > 5:
                self.errors.append({
                    "field": "rating",
                    "error": "out_of_range",
                    "message": f"Rating {rating} is out of range [0, 5]"
                })
        
        # Validate price level
        price_level = record.get("price_level")
        if price_level is not None:
            if not isinstance(price_level, int):
                self.errors.append({
                    "field": "price_level",
                    "error": "invalid_type",
                    "message": "Price level must be an integer"
                })
            elif price_level < 0 or price_level > 4:
                self.warnings.append({
                    "field": "price_level",
                    "warning": "out_of_range",
                    "message": f"Price level {price_level} is outside typical range [0, 4]"
                })
    
    def _validate_metadata(self, record: Dict[str, Any], city: str):
        """Validate metadata fields."""
        # Validate source
        source = record.get("source")
        if source:
            valid_sources = ["osm", "google", "tripadvisor", "manual"]
            if source not in valid_sources:
                self.warnings.append({
                    "field": "source",
                    "warning": "unknown_source",
                    "message": f"Unknown source: {source}"
                })
        
        # Validate city match
        record_city = record.get("city", "").lower()
        if record_city and record_city != city.lower():
            self.warnings.append({
                "field": "city",
                "warning": "city_mismatch",
                "message": f"City mismatch: record={record_city}, expected={city}"
            })
        
        # Check ingestion timestamp
        ingested_at = record.get("ingested_at")
        if ingested_at:
            try:
                datetime.fromisoformat(ingested_at.replace('Z', '+00:00'))
            except ValueError:
                self.warnings.append({
                    "field": "ingested_at",
                    "warning": "invalid_timestamp",
                    "message": f"Invalid timestamp format: {ingested_at}"
                })
    
    def get_validation_summary(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get summary of validation results."""
        total = len(results)
        valid = sum(1 for r in results if r["is_valid"])
        invalid = total - valid
        
        total_errors = sum(len(r["errors"]) for r in results)
        total_warnings = sum(len(r["warnings"]) for r in results)
        
        return {
            "total_records": total,
            "valid_records": valid,
            "invalid_records": invalid,
            "validation_rate": valid / total if total > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def filter_valid_records(
        self,
        records: List[Dict[str, Any]],
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter chỉ giữ valid records."""
        return [
            record for record, result in zip(records, results)
            if result["is_valid"]
        ]
