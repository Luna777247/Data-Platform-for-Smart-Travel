import asyncio
import os
import sys
import logging
import json
from datetime import datetime
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from collectors.osm_collector import OSMCollector
from collectors.google_enrichor import GoogleEnrichor
from app.db.repository import PlaceRepository
from app.db.client import MongoClient
from app.models.place import PipelineStatus

class IncrementalPipeline:
    def __init__(self, use_mongodb: bool):
        self.use_mongodb = use_mongodb
        self.repo = PlaceRepository()
        self.osm = OSMCollector()
        self.enrichor = GoogleEnrichor()
        # CENTRAL STORAGE
        self.local_file = "storage/data/pois.json"
        self.existing_data = {}

    async def load_existing_data(self):
        if self.use_mongodb:
            all_places = await self.repo.get_all(limit=100000)
            self.existing_data = {p["u_key"]: p for p in all_places if "u_key" in p}
        else:
            if os.path.exists(self.local_file):
                with open(self.local_file, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        self.existing_data = {p["u_key"]: p for p in data if "u_key" in p}
                    except: pass

    async def run(self, limit_per_job: int = 50):
        await self.load_existing_data()
        
        cities = list(self.osm.city_config.keys())
        types = list(self.osm.type_query_map.keys())
        
        for city in cities:
            for p_type in types:
                logger.info(f"\n>>> PIPELINE: {city.upper()} - {p_type.upper()} <<<")
                
                # 1. SET STATUS TO RUNNING
                await self.repo.update_pipeline_status(PipelineStatus(
                    city=city, type=p_type, status="running", 
                    collected=0, target=limit_per_job, start_time=datetime.utcnow()
                ))

                try:
                    raw_pois = self.osm.fetch_data(city, p_type, limit=limit_per_job)
                    if not raw_pois:
                        await self.repo.update_pipeline_status(PipelineStatus(
                            city=city, type=p_type, status="done", collected=0, end_time=datetime.utcnow()
                        ))
                        continue

                    to_enrich = []
                    for poi in raw_pois:
                        if self.existing_data.get(poi["u_key"], {}).get("source") == "google":
                            continue
                        to_enrich.append(poi)

                    logger.info(f"To Enrich: {len(to_enrich)}")
                    if to_enrich:
                        # 2. ENRICHING
                        enriched = await self.enrichor.enrich_batch(to_enrich, city)
                        for p in enriched:
                            if self.use_mongodb:
                                await self.repo.upsert_place(p)
                            else:
                                self.existing_data[p["u_key"]] = p
                    
                    # 3. SET STATUS TO DONE
                    collected_count = len([p for p in self.existing_data.values() if p.get("city") == city and p.get("type") == p_type])
                    await self.repo.update_pipeline_status(PipelineStatus(
                        city=city, type=p_type, status="done", 
                        collected=collected_count, target=limit_per_job, end_time=datetime.utcnow()
                    ))

                except Exception as e:
                    logger.error(f"Failed for {city}-{p_type}: {e}")
                    await self.repo.update_pipeline_status(PipelineStatus(
                        city=city, type=p_type, status="failed", 
                        error_message=str(e), end_time=datetime.utcnow()
                    ))

        if not self.use_mongodb:
            with open(self.local_file, "w", encoding="utf-8") as f:
                json.dump(list(self.existing_data.values()), f, ensure_ascii=False, indent=2)

async def main():
    use_mongodb = False
    try:
        await MongoClient.connect()
        await MongoClient.get_db().command("ping")
        use_mongodb = True
        logger.info("Connected to MongoDB")
    except: 
        logger.info("Running in Offline mode")

    pipeline = IncrementalPipeline(use_mongodb=use_mongodb)
    await pipeline.run(limit_per_job=100)
    if use_mongodb: await MongoClient.disconnect()

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    asyncio.run(main())
