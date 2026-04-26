import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import yaml
import logging
from src.collectors.osm_collector import OSMCollector
from src.ingestion.bronze_writer import BronzeWriter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_bronze")

async def main():
    # 1. LOAD CONFIG
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # 2. INITIALIZE COMPONENTS
    writer = BronzeWriter(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key']
    )
    
    # THU THẬP DIỆN RỘNG (9 Thành phố x Toàn bộ Loại hình)
    cities = ["hanoi", "hcm", "danang", "cantho", "haiphong", "hue", "dalat", "vungtau", "nhatrang"]
    categories = ["attraction", "restaurant", "hotel", "cafe", "mall", "park", "museum", "viewpoint", "gallery", "hostel", "bar"]
    
    total_new_items = 0
    
    for city in cities:
        logger.info(f"🚀 >>> STARTING MASSIVE INGESTION FOR: {city.upper()} <<<")
        for cat in categories:
            logger.info(f"--- FETCHING: {cat.upper()} in {city.upper()} ---")
            
            osm = OSMCollector()
            # Lấy tối đa 500 bản ghi mỗi loại hình
            raw_osm = osm.fetch_data(city, cat, limit=500) 
            
            if raw_osm:
                writer.write_raw("osm", city, raw_osm)
                count = len(raw_osm)
                total_new_items += count
                logger.info(f"✅ City: {city} | Cat: {cat} | Items: {count}")
            
            # Nghỉ lâu hơn một chút để tránh bị Overpass block IP khi lấy diện rộng
            import random
            await asyncio.sleep(random.uniform(3, 7))
            
    logger.info(f"🏆 MISSION COMPLETE: Total {total_new_items} real OSM records collected.")

if __name__ == "__main__":
    asyncio.run(main())
