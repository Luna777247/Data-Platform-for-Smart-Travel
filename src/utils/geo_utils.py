"""
Geospatial Utilities
====================

Geospatial calculation helper functions.
"""

import math
from typing import Tuple, Optional


def calculate_distance(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float
) -> float:
    """
    Calculate distance between two points in kilometers using Haversine formula.
    
    Args:
        lat1: Latitude of point 1
        lng1: Longitude of point 1
        lat2: Latitude of point 2
        lng2: Longitude of point 2
        
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate latitude and longitude values.
    
    Args:
        lat: Latitude (-90 to 90)
        lng: Longitude (-180 to 180)
        
    Returns:
        True if valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= lng <= 180


def get_bounding_box(
    lat: float,
    lng: float,
    radius_km: float
) -> Tuple[float, float, float, float]:
    """
    Get bounding box for a location and radius.
    
    Args:
        lat: Center latitude
        lng: Center longitude
        radius_km: Radius in kilometers
        
    Returns:
        Tuple of (min_lat, max_lat, min_lng, max_lng)
    """
    # Approximate degrees per km
    km_per_degree_lat = 111.0
    km_per_degree_lng = 111.0 * math.cos(math.radians(lat))
    
    lat_delta = radius_km / km_per_degree_lat
    lng_delta = radius_km / km_per_degree_lng
    
    return (
        lat - lat_delta,  # min_lat
        lat + lat_delta,  # max_lat
        lng - lng_delta,  # min_lng
        lng + lng_delta   # max_lng
    )
