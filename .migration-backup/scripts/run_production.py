import asyncio
import os
import sys
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Định tuyến Module chuẩn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'backend'))

from src.collectors.osm_collector import OSMCollector
from src.collectors.google_enrichor import GoogleEnrichor
from app.db.repository import PlaceRepository
from app.db.client import MongoClient
from app.models.place import PipelineStatus
from src.shared.data_utils import make_ukey, find_existing_fuzzy, compute_poi_hash

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
                    collected=0, target=limit_per_job, start_time=datetime.now(timezone.utc)
                ))

                try:
                    raw_pois = self.osm.fetch_data(city, p_type, limit=limit_per_job)
                    if not raw_pois:
                        await self.repo.update_pipeline_status(PipelineStatus(
                            city=city, type=p_type, status="done", collected=0, end_time=datetime.now(timezone.utc)
                        ))
                        continue

                    to_enrich = []
                    for poi in raw_pois:
                        # Use fuzzy matching to skip already enriched places
                        matched_key = find_existing_fuzzy(
                            poi["location"]["lat"], 
                            poi["location"]["lon"], 
                            poi["name"], 
                            self.existing_data,
                            radius_m=30
                        )
                        
                        # SMART CHANGE DETECTION / AGING RULES:
                        existing_poi = self.existing_data.get(matched_key or poi["u_key"])
                        if existing_poi and existing_poi.get("source") == "google":
                            last_updated_str = existing_poi.get("last_enriched")
                            if last_updated_str:
                                try:
                                    last_updated = datetime.fromisoformat(last_updated_str)
                                    if last_updated.tzinfo is None:
                                        last_updated = last_updated.replace(tzinfo=timezone.utc)
                                    days_old = (datetime.now(timezone.utc) - last_updated).days
                                    if days_old < 30: # Only skip if data is fresh (< 30 days)
                                        continue
                                except: pass
                        
                        # Use the matched key if found, otherwise keep original
                        if matched_key: poi["u_key"] = matched_key
                        to_enrich.append(poi)

                    logger.info(f"To Enrich/Refresh: {len(to_enrich)}")
                    if to_enrich:
                        # 2. ENRICHING
                        enriched = await self.enrichor.enrich_batch(to_enrich, city)
                        for p in enriched:
                            # Add enrichment timestamp
                            p["last_enriched"] = datetime.now(timezone.utc).isoformat()
                            # Compute business content hash
                            p["poi_hash"] = compute_poi_hash(p)
                            
                            if self.use_mongodb:
                                await self.repo.upsert_place(p)
                            else:
                                self.existing_data[p["u_key"]] = p
                    
                    # 3. SET STATUS TO DONE
                    collected_count = len([p for p in self.existing_data.values() if p.get("city") == city and p.get("type") == p_type])
                    await self.repo.update_pipeline_status(PipelineStatus(
                        city=city, type=p_type, status="done", 
                        collected=collected_count, target=limit_per_job, end_time=datetime.now(timezone.utc)
                    ))

                except Exception as e:
                    logger.error(f"Failed for {city}-{p_type}: {e}")
                    await self.repo.update_pipeline_status(PipelineStatus(
                        city=city, type=p_type, status="failed", 
                        error_message=str(e), end_time=datetime.now(timezone.utc)
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
