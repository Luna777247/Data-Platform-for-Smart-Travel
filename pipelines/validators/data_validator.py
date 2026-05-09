"""
Data Validation Module - Quality Assurance cho Data Pipeline
===========================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/validators/ section
Part of: Data Quality Management Framework

Mục đích:
- Validate data quality cho tất cả layers (Bronze, Silver, Gold)
- Detect data anomalies, inconsistencies, và quality issues
- Generate quality reports cho monitoring
- Enforce data contracts và validation rules

Validation Layers:
- Bronze: Raw data completeness, schema validation
- Silver: Data cleaning, coordinate validation, name normalization
- Gold: Business metrics, duplicate detection, consistency checks

Validation Rules:
- Required fields: Kiểm tra mandatory fields có tồn tại
- Coordinate ranges: Lat [-90, 90], Lon [-180, 180]
- Name patterns: Length, forbidden chars, language support
- Category validation: Canonical category compliance
- Duplicate detection: Location + name similarity
- Encoding check: UTF-8 validation

Usage:
    >>> validator = DataValidator()
    >>> errors = validator.validate_bronze_record(bronze_record)
    >>> if errors:
    ...     logger.warning(f"Validation errors: {errors}")
    
    >>> report = validator.validate_dataset(silver_places, layer="silver")
    >>> print(f"Quality Score: {report.quality_score}/100")
"""

# Import logging để ghi lại validation results
import logging

# Import datetime classes cho timestamps
from datetime import datetime, timezone

# Import type hints cho type checking
from typing import List, Dict, Any, Optional, Set

# Import re cho regex pattern matching (name validation)
import re

# Import data schemas từ pipelines.shared
# BronzeRecord: Raw data validation
# SilverPlace: Cleaned data validation
# GoldPlace: Enriched data validation
# POICategory: Category validation
# DataQualityReport: Quality report model
from pipelines.shared.schemas import (
    BronzeRecord, SilverPlace, GoldPlace, POICategory, DataQualityReport
)

# Import utility functions
# setup_logging: Cấu hình structured logging
# normalize_coordinates: Chuẩn hóa coordinates
from pipelines.shared.utils import setup_logging, normalize_coordinates

# ============================================
# LOGGER SETUP
# ============================================
# Khởi tạo logger cho module này
logger = setup_logging(__name__)


class DataValidator:
    """Validator cho data quality và consistency"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.errors = []
        self.warnings = []
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules"""
        return {
            "required_fields": {
                "bronze": ["metadata", "source", "ingestion_at", "raw_response"],
                "silver": ["u_key", "source_id", "name", "category", "city", "country", "location"],
                "gold": ["id", "u_key", "source_id", "name", "category", "city", "country", "location", "business_metrics"]
            },
            "coordinate_ranges": {
                "lat": (-90, 90),
                "lon": (-180, 180)
            },
            "name_patterns": {
                "min_length": 2,
                "max_length": 200,
                "forbidden_chars": ["<", ">", "|", "\x00"],
                "required_languages": ["vi", "en"]
            },
            "category_validation": True,
            "duplicate_detection": True,
            "encoding_check": True
        }
    
    def validate_bronze_record(self, record: BronzeRecord) -> List[str]:
        """Validate Bronze record"""
        errors = []
        
        try:
            # Check required fields
            required_fields = self.validation_rules["required_fields"]["bronze"]
            for field in required_fields:
                if not hasattr(record, field) or getattr(record, field) is None:
                    errors.append(f"Missing required field: {field}")
            
            # Validate metadata
            if hasattr(record, 'metadata') and record.metadata:
                metadata = record.metadata
                if not metadata.get("city"):
                    errors.append("Missing city in metadata")
                if not metadata.get("category"):
                    errors.append("Missing category in metadata")
                if not metadata.get("source"):
                    errors.append("Missing source in metadata")
            
            # Validate ingestion timestamp
            if hasattr(record, 'ingestion_at'):
                if not isinstance(record.ingestion_at, datetime):
                    errors.append("ingestion_at must be datetime")
                elif record.ingestion_at > datetime.now(timezone.utc):
                    errors.append("ingestion_at cannot be in future")
            
            # Validate raw_response
            if hasattr(record, 'raw_response'):
                if not isinstance(record.raw_response, dict):
                    errors.append("raw_response must be a dictionary")
                elif not record.raw_response:
                    errors.append("raw_response cannot be empty")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def validate_silver_place(self, place: SilverPlace) -> List[str]:
        """Validate Silver place"""
        errors = []
        
        try:
            # Check required fields
            required_fields = self.validation_rules["required_fields"]["silver"]
            for field in required_fields:
                if not hasattr(place, field) or getattr(place, field) is None:
                    errors.append(f"Missing required field: {field}")
            
            # Validate name
            if hasattr(place, 'name'):
                name_errors = self._validate_name(place.name)
                errors.extend(name_errors)
            
            # Validate coordinates
            if hasattr(place, 'location'):
                coord_errors = self._validate_coordinates(place.location)
                errors.extend(coord_errors)
            
            # Validate category
            if hasattr(place, 'category'):
                if not isinstance(place.category, POICategory):
                    errors.append(f"Invalid category: {place.category}")
            
            # Validate country
            if hasattr(place, 'country'):
                if not place.country or len(place.country.strip()) < 2:
                    errors.append("Country must be at least 2 characters")
            
            # Validate address format
            if hasattr(place, 'address') and place.address:
                if len(place.address) > 500:
                    errors.append("Address too long (max 500 characters)")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def validate_gold_place(self, place: GoldPlace) -> List[str]:
        """Validate Gold place"""
        errors = []
        
        try:
            # Inherit Silver validation
            silver_errors = self.validate_silver_place(place)
            errors.extend(silver_errors)
            
            # Gold-specific validations
            if hasattr(place, 'id'):
                if not place.id or not place.id.startswith("gold_"):
                    errors.append("Gold place ID must start with 'gold_'")
            
            if hasattr(place, 'rating'):
                if place.rating is not None:
                    if not isinstance(place.rating, (int, float)):
                        errors.append("Rating must be numeric")
                    elif not (0 <= place.rating <= 5):
                        errors.append("Rating must be between 0 and 5")
            
            if hasattr(place, 'review_count'):
                if place.review_count is not None:
                    if not isinstance(place.review_count, int):
                        errors.append("Review count must be integer")
                    elif place.review_count < 0:
                        errors.append("Review count cannot be negative")
            
            if hasattr(place, 'business_metrics'):
                if not place.business_metrics:
                    errors.append("Business metrics cannot be empty")
                else:
                    # Validate business metrics scores
                    for score_field in ["popularity_score", "quality_score", "trust_score", "completeness_score", "category_confidence"]:
                        if hasattr(place.business_metrics, score_field):
                            score = getattr(place.business_metrics, score_field)
                            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                                errors.append(f"{score_field} must be between 0 and 1")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _validate_name(self, name: str) -> List[str]:
        """Validate name field"""
        errors = []
        rules = self.validation_rules["name_patterns"]
        
        if not name or not isinstance(name, str):
            errors.append("Name must be a non-empty string")
            return errors
        
        # Length validation
        if len(name) < rules["min_length"]:
            errors.append(f"Name too short (min {rules['min_length']} characters)")
        elif len(name) > rules["max_length"]:
            errors.append(f"Name too long (max {rules['max_length']} characters)")
        
        # Forbidden characters
        for char in rules["forbidden_chars"]:
            if char in name:
                errors.append(f"Name contains forbidden character: {char}")
        
        # Encoding check
        try:
            name.encode('utf-8')
        except UnicodeEncodeError:
            errors.append("Name contains invalid UTF-8 characters")
        
        return errors
    
    def _validate_coordinates(self, location: Dict[str, Any]) -> List[str]:
        """Validate coordinates"""
        errors = []
        ranges = self.validation_rules["coordinate_ranges"]
        
        if not isinstance(location, dict):
            errors.append("Location must be a dictionary")
            return errors
        
        # Check required fields
        if 'lat' not in location:
            errors.append("Missing latitude in location")
        if 'lon' not in location:
            errors.append("Missing longitude in location")
        
        if 'lat' in location and 'lon' in location:
            lat = location['lat']
            lon = location['lon']
            
            # Type validation
            try:
                lat_float = float(lat)
                lon_float = float(lon)
            except (ValueError, TypeError):
                errors.append("Coordinates must be numeric")
                return errors
            
            # Range validation
            if not (ranges["lat"][0] <= lat_float <= ranges["lat"][1]):
                errors.append(f"Latitude out of range ({ranges['lat'][0]} to {ranges['lat'][1]})")
            if not (ranges["lon"][0] <= lon_float <= ranges["lon"][1]):
                errors.append(f"Longitude out of range ({ranges['lon'][0]} to {ranges['lon'][1]})")
        
        return errors
    
    def detect_duplicates(self, places: List[Dict[str, Any]], key_fields: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Detect duplicate records"""
        if key_fields is None:
            key_fields = ["name", "city", "category"]
        
        duplicates = {}
        seen_keys = set()
        
        for i, place in enumerate(places):
            # Create deduplication key
            key_parts = []
            for field in key_fields:
                if field in place:
                    value = str(place[field]).lower().strip()
                    if value:
                        key_parts.append(value)
            
            dedup_key = "|".join(key_parts)
            
            if dedup_key in seen_keys:
                if dedup_key not in duplicates:
                    duplicates[dedup_key] = []
                duplicates[dedup_key].append({"index": i, "place": place})
            else:
                seen_keys.add(dedup_key)
        
        return duplicates
    
    def validate_dataset(self, data: List[Any], layer: str) -> DataQualityReport:
        """Validate entire dataset và generate report"""
        start_time = datetime.now(timezone.utc)
        
        total_records = len(data)
        valid_records = 0
        invalid_records = 0
        duplicate_records = 0
        missing_coordinates = 0
        missing_names = 0
        invalid_categories = 0
        invalid_timestamps = 0
        encoding_errors = 0
        
        all_errors = []
        
        # Validate each record
        for i, record in enumerate(data):
            try:
                if layer == "bronze":
                    errors = self.validate_bronze_record(record)
                elif layer == "silver":
                    errors = self.validate_silver_place(record)
                elif layer == "gold":
                    errors = self.validate_gold_place(record)
                else:
                    errors = [f"Unknown layer: {layer}"]
                
                if errors:
                    invalid_records += 1
                    all_errors.extend([f"Record {i}: {error}" for error in errors])
                else:
                    valid_records += 1
                
                # Check specific issues
                if layer in ["silver", "gold"]:
                    # Missing coordinates
                    if hasattr(record, 'location'):
                        if not record.location or 'lat' not in record.location or 'lon' not in record.location:
                            missing_coordinates += 1
                    
                    # Missing names
                    if hasattr(record, 'name'):
                        if not record.name or not record.name.strip():
                            missing_names += 1
                    
                    # Invalid categories
                    if hasattr(record, 'category'):
                        if not isinstance(record.category, POICategory):
                            invalid_categories += 1
                    
                    # Invalid timestamps
                    if hasattr(record, 'ingestion_at'):
                        if not isinstance(record.ingestion_at, datetime):
                            invalid_timestamps += 1
                
                # Encoding check
                try:
                    if hasattr(record, 'name') and record.name:
                        record.name.encode('utf-8')
                except UnicodeEncodeError:
                    encoding_errors += 1
                
            except Exception as e:
                invalid_records += 1
                all_errors.append(f"Record {i}: Validation exception - {str(e)}")
        
        # Detect duplicates
        if layer in ["silver", "gold"]:
            duplicates = self.detect_duplicates(data)
            duplicate_records = sum(len(dup_group) for dup_group in duplicates.values())
        
        # Calculate quality score
        quality_score = 0.0
        if total_records > 0:
            quality_score = (valid_records / total_records) * 0.7
            quality_score += ((total_records - missing_coordinates) / total_records) * 0.1
            quality_score += ((total_records - missing_names) / total_records) * 0.1
            quality_score += ((total_records - invalid_categories) / total_records) * 0.1
        
        processing_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        return DataQualityReport(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            duplicate_records=duplicate_records,
            missing_coordinates=missing_coordinates,
            missing_names=missing_names,
            invalid_categories=invalid_categories,
            quality_score=min(quality_score, 1.0),
            processing_time_ms=processing_time,
            errors=all_errors[:100]  # Limit to first 100 errors
        )
    
    def generate_validation_summary(self, reports: Dict[str, DataQualityReport]) -> Dict[str, Any]:
        """Generate summary cho multiple validation reports"""
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_layers": len(reports),
            "layer_summaries": {},
            "overall_quality": 0.0,
            "total_records": 0,
            "total_valid": 0,
            "total_invalid": 0,
            "total_duplicates": 0,
            "critical_issues": []
        }
        
        total_quality = 0.0
        total_weight = 0
        
        for layer, report in reports.items():
            layer_summary = {
                "total_records": report.total_records,
                "valid_records": report.valid_records,
                "invalid_records": report.invalid_records,
                "duplicate_records": report.duplicate_records,
                "quality_score": report.quality_score,
                "processing_time_ms": report.processing_time_ms,
                "error_count": len(report.errors)
            }
            
            summary["layer_summaries"][layer] = layer_summary
            summary["total_records"] += report.total_records
            summary["total_valid"] += report.valid_records
            summary["total_invalid"] += report.invalid_records
            summary["total_duplicates"] += report.duplicate_records
            
            # Weight quality score by record count
            total_quality += report.quality_score * report.total_records
            total_weight += report.total_records
            
            # Check for critical issues
            if report.quality_score < 0.8:
                summary["critical_issues"].append(f"{layer}: Low quality score ({report.quality_score:.2f})")
            if report.invalid_records > report.total_records * 0.1:
                summary["critical_issues"].append(f"{layer}: High invalid rate ({report.invalid_records/report.total_records:.1%})")
        
        if total_weight > 0:
            summary["overall_quality"] = total_quality / total_weight
        
        return summary


def main():
    """Test validation module"""
    validator = DataValidator()
    
    # Test with sample data
    from pipelines.shared.schemas import SilverPlace, POICategory, SourceType
    from datetime import datetime
    
    sample_places = [
        SilverPlace(
            u_key="test_1",
            source_id="123",
            name="Test Place",
            category=POICategory.RESTAURANT,
            city="hanoi",
            country="Vietnam",
            address="123 Test St",
            location={"lat": 21.0, "lon": 105.0},
            tags={"cuisine": "vietnamese"},
            source=SourceType.OSM,
            ingestion_at=datetime.now()
        ),
        SilverPlace(
            u_key="test_2",
            source_id="456",
            name="",  # Invalid: empty name
            category=POICategory.RESTAURANT,
            city="hanoi",
            country="Vietnam",
            address="123 Test St",
            location={"lat": 91.0, "lon": 105.0},  # Invalid: lat out of range
            tags={"cuisine": "vietnamese"},
            source=SourceType.OSM,
            ingestion_at=datetime.now()
        )
    ]
    
    report = validator.validate_dataset(sample_places, "silver")
    
    logger.info("=" * 50)
    logger.info("DATA VALIDATION REPORT")
    logger.info("=" * 50)
    logger.info(f"Total records: {report.total_records}")
    logger.info(f"Valid records: {report.valid_records}")
    logger.info(f"Invalid records: {report.invalid_records}")
    logger.info(f"Quality score: {report.quality_score:.2f}")
    logger.info(f"Processing time: {report.processing_time_ms}ms")
    
    if report.errors:
        logger.error("Validation errors:")
        for error in report.errors[:10]:
            logger.error(f"  - {error}")
    
    return report


if __name__ == "__main__":
    main()
