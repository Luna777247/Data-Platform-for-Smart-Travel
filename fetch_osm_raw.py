import asyncio
import os
import sys
import logging
import json
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Add paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from collectors.osm_collector import OSMCollector

async def fetch_all_osm_raw():
    osm = OSMCollector()
    
    # Dynamically get from config
    cities = list(osm.city_config.keys())
    types = list(osm.type_query_map.keys())
    
    logger.info(f"Dynamically loaded configuration: {len(cities)} cities, {len(types)} types.")
    
    # CENTRAL STORAGE
    local_file = "storage/data/pois.json"
    existing_data = {}
    
    if os.path.exists(local_file):
        with open(local_file, "r", encoding="utf-8") as f:
            existing_list = json.load(f)
            existing_data = {p["u_key"]: p for p in existing_list}
    
    total_added = 0
    for city in cities:
        for p_type in types:
            logger.info(f"--- Fetching: {city} - {p_type} ---")
            raw_pois = osm.fetch_data(city, p_type, limit=200)
            
            for poi in raw_pois:
                u_key = poi["u_key"]
                if u_key not in existing_data:
                    existing_data[u_key] = poi
                    total_added += 1

    os.makedirs(os.path.dirname(local_file), exist_ok=True)
    with open(local_file, "w", encoding="utf-8") as f:
        json.dump(list(existing_data.values()), f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nCOMPLETED. Total POIs: {len(existing_data)} (New: {total_added})")

if __name__ == "__main__":
    asyncio.run(fetch_all_osm_raw())
