"""
Schema Validator
===============

Schema validation cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/validators/schema_validator.py
"""

import logging
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError

from pipelines.shared.schemas import BronzeRecord, SilverRecord, GoldRecord

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validate data against Pydantic schemas.
    
    Validates:
    - Bronze records
    - Silver records
    - Gold records
    """
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        logger.info("SchemaValidator initialized")
    
    def validate_bronze(
        self,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[BronzeRecord]]:
        """
        Validate Bronze layer data.
        
        Args:
            data: Raw data dictionary
            
        Returns:
            (is_valid, record) tuple
        """
        try:
            record = BronzeRecord(**data)
            return True, record
        except ValidationError as e:
            self.errors.append({
                "layer": "bronze",
                "error": str(e),
                "data": data
            })
            return False, None
    
    def validate_silver(
        self,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[SilverRecord]]:
        """Validate Silver layer data."""
        try:
            record = SilverRecord(**data)
            return True, record
        except ValidationError as e:
            self.errors.append({
                "layer": "silver",
                "error": str(e),
                "data": data
            })
            return False, None
    
    def validate_gold(
        self,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[GoldRecord]]:
        """Validate Gold layer data."""
        try:
            record = GoldRecord(**data)
            return True, record
        except ValidationError as e:
            self.errors.append({
                "layer": "gold",
                "error": str(e),
                "data": data
            })
            return False, None
    
    def validate_records(
        self,
        records: List[Dict[str, Any]],
        schema_class: Type[BaseModel]
    ) -> tuple[List[BaseModel], List[Dict[str, Any]]]:
        """
        Validate nhiều records.
        
        Returns:
            (valid_records, invalid_records) tuple
        """
        valid = []
        invalid = []
        
        for record in records:
            try:
                validated = schema_class(**record)
                valid.append(validated)
            except ValidationError as e:
                invalid.append({
                    "record": record,
                    "error": str(e)
                })
        
        return valid, invalid
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get all validation errors."""
        return self.errors.copy()
    
    def clear_errors(self):
        """Clear validation errors."""
        self.errors = []
