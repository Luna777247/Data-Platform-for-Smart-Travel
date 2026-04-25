# collectors/osm_collector.py
import requests
import logging
import json
import os
from typing import List, Dict, Any
import time

# Workaround to import utils if running from different dirs
try:
    from shared.data_utils import generate_unique_key
except ImportError:
    # Handle cases where shared is not in path yet
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shared.data_utils import generate_unique_key

logger = logging.getLogger(__name__)

class OSMCollector:
    def __init__(self):
        self.overpass_urls = ["https://lz4.overpass-api.de/api/interpreter", "https://z.overpass-api.de/api/interpreter"]
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.load_config()

    def load_config(self):
        """Load cities and types from JSON config files."""
        cities_path = os.path.join(self.base_path, "storage", "configs", "cities.json")
        types_path = os.path.join(self.base_path, "storage", "configs", "poi_types.json")

        try:
            with open(cities_path, "r", encoding="utf-8") as f:
                self.city_config = json.load(f)
            with open(types_path, "r", encoding="utf-8") as f:
                self.type_query_map = json.load(f)
            logger.info(f"Loaded {len(self.city_config)} cities and {len(self.type_query_map)} types from config.")
        except Exception as e:
            logger.error(f"Error loading config files: {e}")
            # Fallbacks
            self.city_config = {"hanoi": {"name": "Thành phố Hà Nội"}}
            self.type_query_map = {"attraction": 'node["tourism"="attraction"](area.searchArea);'}

    def fetch_data(self, city: str, category: str, limit: int = 150) -> List[Dict[str, Any]]:
        city_info = self.city_config.get(city.lower())
        if not city_info: 
            logger.warning(f"City '{city}' not found in config.")
            return []

        query_type = self.type_query_map.get(category.lower())
        if not query_type:
            logger.warning(f"Type '{category}' not found in config.")
            return []

        query = f'[out:json][timeout:90]; area["name"="{city_info["name"]}"]->.searchArea; ({query_type}); out center {limit};'

        for url in self.overpass_urls:
            try:
                logger.info(f"[INFO] Fetching {category} for {city} from {url}")
                headers = {"User-Agent": "SmartTourismProject/1.0"}
                response = requests.post(url, data={"data": query}, headers=headers, timeout=60)
                if response.status_code == 429:
                    logger.warning(f"[WARN] Rate limited by {url}. Retrying...")
                    time.sleep(5)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                results = []
                for el in data.get("elements", []):
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en") or "Unnamed"
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    
                    if not lat or not lon: continue
                    
                    results.append({
                        "u_key": generate_unique_key(name, lat, lon),
                        "name": name,
                        "type": category,
                        "city": city,
                        "address": tags.get("addr:full") or tags.get("addr:street") or "",
                        "location": {"lat": lat, "lon": lon},
                        "source": "osm"
                    })
                
                logger.info(f"[INFO] Successfully collected {len(results)} items for {city}-{category}")
                return results
            except Exception as e:
                logger.error(f"[ERROR] OSM Error: {e}")
                continue
        return []
