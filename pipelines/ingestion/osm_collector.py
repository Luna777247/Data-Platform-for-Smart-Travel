"""
OSM Collector
=============

OpenStreetMap data collector cho Bronze layer.
Sử dụng Overpass API để query POI data.
"""

import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)


class OSMCollector:
    """
    Collect POI data từ OpenStreetMap.
    
    Uses Overpass API for querying data within geographic bounds.
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 60
        logger.info("OSMCollector initialized")
    
    def collect(
        self,
        city: str,
        category: str,
        lat: float,
        lng: float,
        radius: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Collect POIs from OSM for a given location and category.
        
        Args:
            city: City name
            category: POI category (restaurant, hotel, etc.)
            lat: Center latitude
            lng: Center longitude
            radius: Search radius in meters
            
        Returns:
            List of raw POI records
        """
        # Map category to OSM tags
        osm_tags = self._get_osm_tags(category)
        
        records = []
        
        for tag_key, tag_values in osm_tags.items():
            for tag_value in tag_values:
                try:
                    # Build Overpass query
                    query = self._build_overpass_query(
                        lat, lng, radius, tag_key, tag_value
                    )
                    
                    # Execute query
                    data = self._execute_overpass_query(query)
                    
                    # Parse results
                    pois = self._parse_overpass_results(data, city, category)
                    records.extend(pois)
                    
                    # Rate limiting
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error querying {tag_key}={tag_value}: {e}")
                    continue
        
        logger.info(f"Collected {len(records)} POIs for {city}/{category}")
        return records
    
    def _get_osm_tags(self, category: str) -> Dict[str, List[str]]:
        """Map our category to OSM tags."""
        mappings = {
            "restaurant": {
                "amenity": ["restaurant", "fast_food"],
                "cuisine": ["*"]
            },
            "cafe": {
                "amenity": ["cafe", "coffee_shop"]
            },
            "hotel": {
                "tourism": ["hotel", "hostel", "guest_house", "motel"]
            },
            "attraction": {
                "tourism": ["attraction", "museum", "viewpoint", "zoo"]
            },
            "shop": {
                "shop": ["*"]
            },
            "park": {
                "leisure": ["park", "garden"]
            }
        }
        return mappings.get(category, {"amenity": [category]})
    
    def _build_overpass_query(
        self,
        lat: float,
        lng: float,
        radius: int,
        tag_key: str,
        tag_value: str
    ) -> str:
        """Build Overpass API query."""
        # Simplified query for nodes within radius
        if tag_value == "*":
            tag_filter = f"['{tag_key}']"
        else:
            tag_filter = f"['{tag_key}'='{tag_value}']"
        
        query = f"""
        [out:json][timeout:30];
        (
          node{tag_filter}
            (around:{radius},{lat},{lng});
          way{tag_filter}
            (around:{radius},{lat},{lng});
        );
        out center tags 50;
        """
        return query.strip()
    
    def _execute_overpass_query(self, query: str) -> Dict:
        """Execute Overpass API query."""
        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Overpass API returned {response.status_code}")
                return {"elements": []}
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"elements": []}
    
    def _parse_overpass_results(
        self,
        data: Dict,
        city: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """Parse Overpass API results into our format."""
        records = []
        
        for element in data.get("elements", []):
            if element.get("type") not in ["node", "way"]:
                continue
            
            tags = element.get("tags", {})
            
            # Get coordinates
            if element["type"] == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            else:  # way
                center = element.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")
            
            if lat is None or lon is None:
                continue
            
            record = {
                "poi_id": f"osm_{element.get('id')}",
                "name": tags.get("name", f"Unnamed {category}"),
                "name_en": tags.get("name:en"),
                "category": category,
                "city": city,
                "country": "VN",
                "location": {"lat": lat, "lng": lon},
                "address": self._build_address(tags),
                "osm_tags": tags,
                "osm_id": element.get("id"),
                "osm_type": element.get("type"),
                "raw_data": element
            }
            
            records.append(record)
        
        return records
    
    def _build_address(self, tags: Dict) -> Optional[str]:
        """Build address string from OSM tags."""
        parts = []
        
        if "addr:housenumber" in tags:
            parts.append(tags["addr:housenumber"])
        
        if "addr:street" in tags:
            parts.append(tags["addr:street"])
        
        if "addr:city" in tags:
            parts.append(tags["addr:city"])
        
        return ", ".join(parts) if parts else None
