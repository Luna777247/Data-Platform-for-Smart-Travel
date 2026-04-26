# collectors/osm_collector.py
import requests
import logging
import json
import os
from typing import List, Dict, Any
import time

# Workaround to import utils if running from different dirs
from src.shared.data_utils import make_ukey
from src.shared.path_manager import ROOT_DIR

logger = logging.getLogger(__name__)

class OSMCollector:
    def __init__(self):
        self.overpass_urls = [
            "https://lz4.overpass-api.de/api/interpreter", 
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass.osm.ch/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.nchc.org.tw/api/interpreter"
        ]
        self.base_path = ROOT_DIR
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
        import random
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "SmartTourismProject/1.0 (Research Purpose; contact@smarttravel.vn)"
        ]

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
                # 1. ADAPTIVE JITTER (Nghỉ ngẫu nhiên để tránh pattern cố định)
                sleep_time = random.uniform(1.5, 3.5)
                time.sleep(sleep_time)

                logger.info(f"[INFO] Fetching {category} for {city} from {url} (Wait: {sleep_time:.2f}s)")
                
                # 2. ROTATE USER-AGENT
                headers = {"User-Agent": random.choice(user_agents)}
                response = requests.post(url, data={"data": query}, headers=headers, timeout=60)
                
                if response.status_code == 429:
                    logger.warning(f"[WARN] Rate limited by {url}. Backing off for 10s...")
                    time.sleep(10)
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
                        "u_key": make_ukey(name, lat, lon),
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
