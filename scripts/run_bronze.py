import sys
import os
import asyncio
import yaml
import logging
import json
import random
from typing import List
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.path_manager import get_path, DOTENV_PATH
load_dotenv(DOTENV_PATH)
from src.collectors.osm_collector import OSMCollector
from src.ingestion.bronze_writer import BronzeWriter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_bronze")

async def main():
    # 1. LOAD CONFIG
    config_path = get_path("infra/config/config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"❌ Configuration file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # 2. INITIALIZE COMPONENTS
    writer = BronzeWriter(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key']
    )
    
    # 3. LOAD CITIES & CATEGORIES DYNAMICALLY
    cities_env = os.getenv("SMART_TRAVEL_CITIES", "hanoi,hcm,danang")
    cities = [c.strip().lower() for c in cities_env.split(",") if c.strip()]
    
    poi_types_path = get_path("storage/configs/poi_types.json")
    with open(poi_types_path, "r", encoding="utf-8") as f:
        poi_types = json.load(f)
    categories = list(poi_types.keys())
    
    total_new_items = 0
    osm = OSMCollector() # Shared instance to reuse config
    
    for city in cities:
        logger.info(f"🚀 >>> STARTING MASSIVE INGESTION FOR: {city.upper()} <<<")
        for cat in categories:
            logger.info(f"--- FETCHING: {cat.upper()} in {city.upper()} ---")
            
            # Use async version for better performance if possible, but keep simple loop
            raw_osm = await osm.fetch_data_async(city, cat, limit=50000) 
            
            if raw_osm:
                writer.write_raw("osm", city, raw_osm)
                count = len(raw_osm)
                total_new_items += count
                logger.info(f"✅ City: {city} | Cat: {cat} | Items: {count}")
                
                # Brief pause between categories to be nice to Overpass
                await asyncio.sleep(random.uniform(1, 3))
            else:
                logger.warning(f"⚠️ No data for {cat} in {city}")
            
    logger.info(f"🏆 MISSION COMPLETE: Total {total_new_items} real OSM records collected.")

if __name__ == "__main__":
    asyncio.run(main())
