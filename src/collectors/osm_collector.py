# src/collectors/osm_collector.py
import requests
import logging
import json
import os
from typing import List, Dict, Any
import time

from src.shared.data_utils import make_ukey
from src.shared.path_manager import ROOT_DIR

logger = logging.getLogger(__name__)

import asyncio
import httpx
from datetime import datetime
from src.shared.data_contracts import BronzePlace

class OSMCollector:
    def __init__(self, city: str):
        self.city = city
        self.overpass_url = "https://lz4.overpass-api.de/api/interpreter"
        self.city_queries = {
            "hanoi": 'area["name"="Thành phố Hà Nội"]->.searchArea;',
            "hcm": 'area["name"="Thành phố Hồ Chí Minh"]->.searchArea;',
            "danang": 'area["name"="Thành phố Đà Nẵng"]->.searchArea;'
        }

    async def collect(self) -> list:
        if self.city not in self.city_queries:
            return []
            
        # Simplified query for testing
        query = f"""
        [out:json][timeout:25];
        {self.city_queries[self.city]}
        node["tourism"="attraction"](area.searchArea);
        out center meta;
        """
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.overpass_url, data={'data': query})
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch OSM data: {e}")
                return []

        places = []
        for element in data.get('elements', [])[:10]: # Limit to 10 for quick testing
            place = BronzePlace(
                source_id=str(element["id"]),
                raw_data=element,
                collected_at=datetime.utcnow(),
                city=self.city,
                source="osm"
            )
            places.append(place)

        return places

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

        if city not in self.city_config:
            logger.error(f"City '{city}' not found in config.")
            return []

        if category not in self.type_query_map:
            logger.error(f"Category '{category}' not found in config.")
            return []

        city_data = self.city_config[city]
        query_template = self.type_query_map[category]

        # Build Overpass query
        query = f"""
        [out:json][timeout:25];
        area["name"="{city_data['name']}"]->.searchArea;
        (
          {query_template}
        );
        out center meta;
        """

        logger.info(f"Fetching OSM data for {city} - {category}")

        for url in self.overpass_urls:
            try:
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'application/json',
                    'Accept-Language': 'en-US,en;q=0.9',
                }

                response = requests.post(url, data={'data': query}, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()
                elements = data.get('elements', [])

                if not elements:
                    logger.warning(f"No data found for {city} - {category} from {url}")
                    continue

                # Process and return data
                processed_data = []
                for element in elements[:limit]:
                    processed_item = self._process_element(element, city, category)
                    if processed_item:
                        processed_data.append(processed_item)

                logger.info(f"Successfully fetched {len(processed_data)} items from {url}")
                return processed_data

            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                time.sleep(1)  # Brief pause before trying next URL
                continue

        logger.error(f"All Overpass URLs failed for {city} - {category}")
        return []

    def _process_element(self, element: Dict[str, Any], city: str, category: str) -> Dict[str, Any]:
        """Process a single OSM element into our data format."""
        try:
            tags = element.get('tags', {})
            center = element.get('center', {})

            # Extract coordinates
            lat = center.get('lat') or element.get('lat')
            lon = center.get('lon') or element.get('lon')

            if not lat or not lon:
                return None

            # Build address from tags
            address_parts = []
            if tags.get('addr:housenumber'):
                address_parts.append(tags['addr:housenumber'])
            if tags.get('addr:street'):
                address_parts.append(tags['addr:street'])
            if tags.get('addr:city'):
                address_parts.append(tags['addr:city'])
            address = ', '.join(address_parts) if address_parts else None

            # Create processed item
            item = {
                'ukey': make_ukey(city, category, str(element['id'])),
                'osm_id': element['id'],
                'name': tags.get('name', f"Unnamed {category}"),
                'category': category,
                'city': city,
                'latitude': float(lat),
                'longitude': float(lon),
                'address': address,
                'tags': tags,
                'source': 'osm',
                'collected_at': time.time()
            }

            return item

        except Exception as e:
            logger.error(f"Error processing element {element.get('id')}: {e}")
            return None

    def save_to_file(self, data: List[Dict[str, Any]], city: str, category: str):
        """Save collected data to bronze storage."""
        if not data:
            logger.warning(f"No data to save for {city} - {category}")
            return

        bronze_dir = os.path.join(self.base_path, "storage", "bronze", "osm")
        os.makedirs(bronze_dir, exist_ok=True)

        filename = f"{city}_{category}_{int(time.time())}.json"
        filepath = os.path.join(bronze_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(data)} items to {filepath}")
        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")
