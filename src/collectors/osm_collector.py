# src/collectors/osm_collector.py
import logging
import json
import os
import time
import random
import asyncio
from typing import List, Dict, Any
from datetime import datetime

import httpx
from src.shared.data_utils import make_ukey
from src.shared.path_manager import ROOT_DIR
from src.shared.data_contracts import BronzePlace

logger = logging.getLogger(__name__)

class OSMCollector:
    def __init__(self, city: str = None):
        self.city = city
        self.base_path = ROOT_DIR
        self.load_config()

    def load_config(self):
        """Load cities and types from JSON config files."""
        cities_path = os.path.join(self.base_path, "storage", "configs", "cities.json")
        types_path = os.path.join(self.base_path, "storage", "configs", "poi_types.json")
        settings_path = os.path.join(self.base_path, "storage", "configs", "osm_settings.json")

        try:
            with open(cities_path, "r", encoding="utf-8") as f:
                self.city_config = json.load(f)
            with open(types_path, "r", encoding="utf-8") as f:
                self.type_query_map = json.load(f)
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings = json.load(f)
            
            self.overpass_urls = self.settings.get("overpass_urls", ["https://lz4.overpass-api.de/api/interpreter"])
            
            logger.info(f"Loaded {len(self.city_config)} cities and {len(self.type_query_map)} types from config.")
        except Exception as e:
            logger.error(f"Error loading config files: {e}")
            # Fallbacks
            self.city_config = {
                "hanoi": {"name": "Thành phố Hà Nội"},
                "hcm": {"name": "Thành phố Hồ chí Minh"},
                "danang": {"name": "Thành phố Đà Nẵng"}
            }
            self.type_query_map = {"attraction": 'node["tourism"="attraction"](area.searchArea);'}
            self.overpass_urls = ["https://lz4.overpass-api.de/api/interpreter"]

    async def collect(self, city: str = None) -> List[BronzePlace]:
        """
        Collect all POIs for the configured city using all categories in poi_types.json.
        """
        target_city = city or self.city
        if not target_city or target_city not in self.city_config:
            logger.error(f"City '{target_city}' not found in configuration.")
            return []

        all_places = []
        for category in self.type_query_map.keys():
            raw_data = await self.fetch_data_async(target_city, category)
            for item in raw_data:
                place = BronzePlace(
                    source_id=str(item.get("id") or item.get("osm_id")),
                    raw_data=item,
                    collected_at=datetime.utcnow(),
                    city=target_city,
                    source="osm"
                )
                all_places.append(place)
        
        return all_places

    async def fetch_data_async(self, city: str, category: str, limit: int = 50000) -> List[Dict[str, Any]]:
        """Async version of fetch_data."""
        if city not in self.city_config or category not in self.type_query_map:
            return []

        city_data = self.city_config[city]
        city_name = city_data.get('name', city)
        query_template = self.type_query_map[category]
        
        query = f"""
        [out:json][timeout:60];
        area["name"="{city_name}"]->.searchArea;
        (
          {query_template}
        );
        out center meta;
        """
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0",
            "SmartTourismProject/1.0 (Research; contact@smarttravel.vn)"
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            for url in self.overpass_urls:
                try:
                    headers = {
                        'User-Agent': random.choice(user_agents),
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'Origin': 'https://overpass-turbo.eu',
                        'Referer': 'https://overpass-turbo.eu/'
                    }
                    response = await client.post(url, data={'data': query}, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    elements = data.get('elements', [])
                    logger.info(f"✅ Found {len(elements)} items for {category} in {city}")
                    return elements[:limit]
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch {category} from {url}: {e}")
                    continue
        return []

    def fetch_data(self, city: str, category: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Synchronous wrapper for fetch_data_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.fetch_data_async(city, category, limit))
