"""
Geospatial Enrichment
====================

Geospatial enrichment cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/enrichment/geospatial_enrichment.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GeospatialEnricher:
    """
    Enrich POI data với geospatial information.
    
    Enrichments:
    - Region hierarchy
    - Distance calculations
    - Geohash generation
    - Boundary checks
    """
    
    def __init__(self):
        self.region_hierarchy = {}
        logger.info("GeospatialEnricher initialized")
    
    def enrich(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một record với geospatial data.
        
        Args:
            record: POI record
            
        Returns:
            Enriched record
        """
        enriched = record.copy()
        
        location = record.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        
        if lat is not None and lng is not None:
            # Add geohash
            enriched["geohash"] = self._generate_geohash(lat, lng)
            
            # Add region hierarchy
            enriched["region_hierarchy"] = self._get_region_hierarchy(lat, lng)
            
            # Add coordinate precision
            enriched["coordinate_precision"] = self._estimate_precision(location)
            
            # Add bounding box if available
            bbox = self._get_bounding_box(lat, lng)
            if bbox:
                enriched["bounding_box"] = bbox
        
        enriched["geospatial_enriched"] = True
        enriched["geospatial_enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched
    
    def enrich_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich nhiều records."""
        return [self.enrich(r) for r in records]
    
    def _generate_geohash(self, lat: float, lng: float, precision: int = 8) -> str:
        """
        Generate geohash from coordinates.
        
        Simplified implementation - production would use proper geohash library.
        """
        # This is a placeholder - use python-geohash in production
        chars = "0123456789bcdefghjkmnpqrstuvwxyz"
        
        # Simplified encoding
        lat_range = [-90.0, 90.0]
        lng_range = [-180.0, 180.0]
        
        geohash = ""
        bit = 0
        ch = 0
        
        for _ in range(precision):
            if bit % 2 == 0:  # Even bits for longitude
                mid = (lng_range[0] + lng_range[1]) / 2
                if lng >= mid:
                    ch = ch * 2 + 1
                    lng_range[0] = mid
                else:
                    ch = ch * 2
                    lng_range[1] = mid
            else:  # Odd bits for latitude
                mid = (lat_range[0] + lat_range[1]) / 2
                if lat >= mid:
                    ch = ch * 2 + 1
                    lat_range[0] = mid
                else:
                    ch = ch * 2
                    lat_range[1] = mid
            
            bit += 1
            if bit == 5:
                geohash += chars[ch]
                bit = 0
                ch = 0
        
        return geohash
    
    def _get_region_hierarchy(
        self,
        lat: float,
        lng: float
    ) -> Dict[str, str]:
        """
        Get region hierarchy for coordinates.
        
        Returns dict with country, state, city, district if available.
        """
        # Placeholder - would use reverse geocoding in production
        return {
            "country": None,
            "state": None,
            "city": None,
            "district": None,
            "neighborhood": None
        }
    
    def _estimate_precision(self, location: Dict[str, Any]) -> str:
        """Estimate coordinate precision based on decimal places."""
        lat = location.get("lat")
        
        if lat is None:
            return "unknown"
        
        # Count decimal places
        lat_str = str(float(lat))
        if "." in lat_str:
            decimals = len(lat_str.split(".")[1])
            
            if decimals >= 6:
                return "high"  # ~0.1m precision
            elif decimals >= 4:
                return "medium"  # ~10m precision
            else:
                return "low"  # ~100m+ precision
        
        return "low"
    
    def _get_bounding_box(
        self,
        lat: float,
        lng: float,
        radius_meters: float = 100
    ) -> Optional[Dict[str, float]]:
        """
        Get bounding box around a point.
        
        Args:
            lat: Center latitude
            lng: Center longitude
            radius_meters: Radius in meters
            
        Returns:
            Bounding box as dict
        """
        # Approximate conversion
        lat_delta = radius_meters / 111000  # ~111km per degree
        lng_delta = radius_meters / (111000 * abs(lat))
        
        return {
            "min_lat": lat - lat_delta,
            "max_lat": lat + lat_delta,
            "min_lng": lng - lng_delta,
            "max_lng": lng + lng_delta
        }
