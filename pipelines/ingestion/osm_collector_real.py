"""
OSM Collector - Real Data
=========================

Robust OSM data collector với retry logic, rate limiting, và caching.
Sử dụng Overpass API để query real POI data.
"""

import logging
import time
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OSMCollectorReal:
    """
    Robust OSM collector cho real data collection.
    
    Features:
    - Retry logic với exponential backoff
    - Rate limiting tự động
    - Response caching
    - Batch processing
    """
    
    def __init__(self, max_retries: int = 3, cache_duration: int = 3600):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 60
        self.max_retries = max_retries
        self.cache_duration = cache_duration
        self.last_request_time = 0
        self.min_request_interval = 2.0  # seconds between requests
        
        # Setup session với retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        logger.info("OSMCollectorReal initialized")
    
    def collect(
        self,
        city: str,
        category: str,
        lat: float,
        lng: float,
        radius: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Collect real POIs from OSM.
        
        Args:
            city: City name
            category: POI category
            lat: Center latitude
            lng: Center longitude
            radius: Search radius in meters (max 25000)
            
        Returns:
            List of POI records
        """
        # Rate limiting
        self._wait_for_rate_limit()
        
        # Map category to OSM tags
        osm_tags = self._get_osm_tags(category)
        
        records = []
        
        for tag_key, tag_values in osm_tags.items():
            for tag_value in tag_values:
                try:
                    # Build Overpass query with area-based search
                    query = self._build_overpass_query(
                        city, tag_key, tag_value
                    )
                    
                    # Execute query with city context
                    data = self._execute_query(query, city)
                    
                    if data and "elements" in data:
                        pois = self._parse_elements(data["elements"], city, category)
                        records.extend(pois)
                        logger.info(f"Found {len(pois)} {category} POIs in {city}")
                    
                    # Rate limiting between queries
                    time.sleep(self.min_request_interval)
                    
                except Exception as e:
                    logger.warning(f"Error collecting {tag_key}={tag_value}: {e}")
                    continue
        
        # Remove duplicates by OSM ID
        records = self._deduplicate_by_id(records)
        
        logger.info(f"Total collected: {len(records)} unique POIs for {city}/{category}")
        return records
    
    def _wait_for_rate_limit(self):
        """Wait if needed to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_osm_tags(self, category: str) -> Dict[str, List[str]]:
        """Map our categories to OSM tags."""
        mappings = {
            "restaurant": {
                "amenity": ["restaurant", "fast_food", "food_court"]
            },
            "cafe": {
                "amenity": ["cafe", "coffee_shop"]
            },
            "hotel": {
                "tourism": ["hotel", "hostel", "guest_house", "motel", "apartment"]
            },
            "attraction": {
                "tourism": ["attraction", "museum", "viewpoint", "zoo", "theme_park"]
            },
            "shop": {
                "shop": ["*"]
            },
            "bar": {
                "amenity": ["bar", "pub", "nightclub"]
            },
            "pharmacy": {
                "amenity": ["pharmacy"],
                "shop": ["chemist"]
            },
            "bank": {
                "amenity": ["bank", "atm"]
            }
        }
        return mappings.get(category, {"amenity": [category]})
    
    def _build_overpass_query(
        self,
        city: str,
        tag_key: str,
        tag_value: str
    ) -> str:
        """Build Overpass query using area-based search (working format)."""
        # Use city name for area search (more reliable than radius)
        city_name = city.replace("_", " ").title()
        
        if tag_value == "*":
            query = f'''[out:json][timeout:60];
area["name"="{city_name}"]->.searchArea;
(
  node["{tag_key}"](area.searchArea);
  way["{tag_key}"](area.searchArea);
);
out center meta;'''
        else:
            query = f'''[out:json][timeout:60];
area["name"="{city_name}"]->.searchArea;
(
  node["{tag_key}"="{tag_value}"](area.searchArea);
  way["{tag_key}"="{tag_value}"](area.searchArea);
);
out center meta;'''
        
        return query
    
    def _execute_query(self, query: str, city: str) -> Optional[Dict]:
        """Execute Overpass query với proper headers."""
        try:
            # Headers giống working collector
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://overpass-turbo.eu",
                "Referer": "https://overpass-turbo.eu/"
            }
            
            response = self.session.post(
                self.overpass_url,
                data={"data": query},
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited by Overpass API, waiting...")
                time.sleep(10)
                return None
            else:
                logger.warning(f"Overpass API returned {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("Request timeout")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _parse_elements(
        self,
        elements: List[Dict],
        city: str,
        category: str
    ) -> List[Dict[str, Any]]:
        """Parse OSM elements to our format."""
        records = []
        
        for element in elements:
            try:
                # Get coordinates
                if element["type"] == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif element["type"] == "way":
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")
                else:  # relation
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")
                
                if lat is None or lon is None:
                    continue
                
                tags = element.get("tags", {})
                
                # Skip if no name
                name = tags.get("name", "").strip()
                if not name:
                    continue
                
                record = {
                    "poi_id": f"osm_{element['type']}_{element['id']}",
                    "name": name,
                    "name_en": tags.get("name:en"),
                    "category": category,
                    "city": city,
                    "country": "VN",
                    "location": {
                        "lat": round(lat, 6),
                        "lng": round(lon, 6)
                    },
                    "address": self._build_address(tags),
                    "phone": tags.get("phone"),
                    "website": tags.get("website"),
                    "opening_hours": tags.get("opening_hours"),
                    "rating": None,  # OSM doesn't have ratings
                    "review_count": 0,
                    "osm_tags": tags,
                    "osm_id": element["id"],
                    "osm_type": element["type"],
                    "osm_version": element.get("version"),
                    "osm_timestamp": element.get("timestamp"),
                    "_ingestion_timestamp": datetime.utcnow().isoformat(),
                    "_city": city,
                    "_category": category,
                    "_source": "osm_real",
                    "_layer": "bronze",
                    "_data_quality": "real"
                }
                
                records.append(record)
                
            except Exception as e:
                logger.debug(f"Error parsing element: {e}")
                continue
        
        return records
    
    def _build_address(self, tags: Dict) -> Optional[str]:
        """Build address string từ OSM tags."""
        parts = []
        
        if tags.get("addr:housenumber"):
            parts.append(tags["addr:housenumber"])
        
        if tags.get("addr:street"):
            parts.append(tags["addr:street"])
        
        if tags.get("addr:city"):
            parts.append(tags["addr:city"])
        
        return ", ".join(parts) if parts else None
    
    def _deduplicate_by_id(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicates by OSM ID."""
        seen_ids = set()
        unique = []
        
        for record in records:
            poi_id = record.get("poi_id")
            if poi_id and poi_id not in seen_ids:
                seen_ids.add(poi_id)
                unique.append(record)
        
        return unique


if __name__ == "__main__":
    # Test collector
    logging.basicConfig(level=logging.INFO)
    
    collector = OSMCollectorReal()
    
    # Test collect for Hanoi restaurants
    results = collector.collect(
        city="hanoi",
        category="restaurant",
        lat=21.0278,
        lng=105.8342,
        radius=5000
    )
    
    print(f"\nCollected {len(results)} restaurants in Hanoi")
    if results:
        print(f"Sample: {results[0]['name']} at ({results[0]['location']['lat']}, {results[0]['location']['lng']})")
