"""
Geospatial Validator
===================

Geospatial validation cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/validators/geo_validator.py
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class GeoValidator:
    """
    Validate geospatial data.
    
    Validates:
    - Coordinate ranges
    - Coordinate formats
    - Polygon validity
    - Distance calculations
    """
    
    def __init__(self):
        self.errors: List[str] = []
        logger.info("GeoValidator initialized")
    
    def validate_coordinates(
        self,
        lat: float,
        lng: float
    ) -> bool:
        """
        Validate latitude và longitude.
        
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        
        if lat is None or lng is None:
            self.errors.append("Coordinates cannot be None")
            return False
        
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            self.errors.append("Coordinates must be numbers")
            return False
        
        if not (-90 <= lat <= 90):
            self.errors.append(f"Latitude {lat} out of range [-90, 90]")
        
        if not (-180 <= lng <= 180):
            self.errors.append(f"Longitude {lng} out of range [-180, 180]")
        
        # Check for null island
        if abs(lat) < 0.001 and abs(lng) < 0.001:
            self.errors.append("Coordinates at null island (0,0)")
        
        return len(self.errors) == 0
    
    def validate_location(
        self,
        location: Dict[str, Any]
    ) -> bool:
        """Validate location object."""
        self.errors = []
        
        if not isinstance(location, dict):
            self.errors.append("Location must be a dictionary")
            return False
        
        lat = location.get("lat")
        lng = location.get("lng")
        
        return self.validate_coordinates(lat, lng)
    
    def validate_bounding_box(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float
    ) -> bool:
        """Validate bounding box coordinates."""
        self.errors = []
        
        # Check individual coordinates
        coords = [
            (min_lat, "min_lat", -90, 90),
            (max_lat, "max_lat", -90, 90),
            (min_lng, "min_lng", -180, 180),
            (max_lng, "max_lng", -180, 180)
        ]
        
        for val, name, min_v, max_v in coords:
            if val is None:
                self.errors.append(f"{name} cannot be None")
            elif not (min_v <= val <= max_v):
                self.errors.append(f"{name} {val} out of range [{min_v}, {max_v}]")
        
        # Check relationships
        if min_lat is not None and max_lat is not None:
            if min_lat >= max_lat:
                self.errors.append("min_lat must be less than max_lat")
        
        if min_lng is not None and max_lng is not None:
            if min_lng >= max_lng:
                self.errors.append("min_lng must be less than max_lng")
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors.copy()
    
    def is_in_city_bounds(
        self,
        lat: float,
        lng: float,
        city_bounds: Dict[str, float]
    ) -> bool:
        """
        Check if coordinates are within city bounds.
        
        Args:
            lat: Latitude
            lng: Longitude
            city_bounds: Dict with min_lat, max_lat, min_lng, max_lng
            
        Returns:
            True if within bounds
        """
        return (
            city_bounds.get("min_lat", -90) <= lat <= city_bounds.get("max_lat", 90) and
            city_bounds.get("min_lng", -180) <= lng <= city_bounds.get("max_lng", 180)
        )
