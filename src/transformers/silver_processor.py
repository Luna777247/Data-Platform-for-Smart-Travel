from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from src.shared.data_contracts import SilverPlace
import re


import pandas as pd
import json
import os
import logging
import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class SilverProcessor:
    def __init__(self, mongo_client: Optional[AsyncIOMotorClient] = None):
        if not mongo_client:
            from app.api.dependencies.database import mongo_client as default_client
            self.mongo_client = default_client
        else:
            self.mongo_client = mongo_client
            
        self.bronze_collection = self.mongo_client.smart_travel.places_bronze
        self.silver_collection = self.mongo_client.smart_travel.places_silver

    def process_city(self, city: str):
        """Orchestrates the silver processing steps for a city."""
        logger.info(f"✨ >>> STARTING SILVER PROCESSING FOR: {city.upper()} <<<")
        
        # 1. OSM to Silver
        self._process_osm(city)
        
        # 2. Google to Silver
        self._process_google(city)
        
        # 3. Merge and Save
        self._merge_and_save(city)
        
        logger.info(f"✅ >>> SILVER PROCESSING COMPLETE FOR: {city.upper()} <<<")

    def _process_osm(self, city: str):
        from src.shared.path_manager import get_path
        from src.shared.data_utils import make_ukey
        
        osm_dir = get_path(f"storage/bronze/osm/{city}")
        if not os.path.exists(osm_dir):
            return

        all_data = []
        for file in [f for f in os.listdir(osm_dir) if f.endswith(".json")]:
            with open(os.path.join(osm_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data if isinstance(data, list) else [data])
        
        df = pd.DataFrame(all_data)
        if df.empty: return
        
        # Map OSM tags to silver schema
        df['name'] = df['raw_data'].apply(lambda x: x.get('tags', {}).get('name', '').strip())
        df['address'] = df['raw_data'].apply(self._build_osm_address)
        df['latitude'] = df['raw_data'].apply(lambda x: x.get('center', {}).get('lat', 0.0))
        df['longitude'] = df['raw_data'].apply(lambda x: x.get('center', {}).get('lon', 0.0))
        df['u_key'] = df.apply(lambda x: make_ukey(x['name'], x['latitude'], x['longitude']), axis=1)
        
        output_path = get_path(f"storage/silver/pois_osm/{city}/data.parquet")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)

    def _process_google(self, city: str):
        from src.shared.path_manager import get_path
        from src.shared.data_utils import make_ukey
        
        google_dir = get_path(f"storage/bronze/google/{city}")
        if not os.path.exists(google_dir):
            return

        all_data = []
        for file in [f for f in os.listdir(google_dir) if f.endswith(".json")]:
            with open(os.path.join(google_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data if isinstance(data, list) else [data])
        
        df = pd.DataFrame(all_data)
        if df.empty: return
        
        df['name'] = df['raw_data'].apply(lambda x: x.get('name', '').strip())
        df['latitude'] = df['raw_data'].apply(lambda x: x.get('geometry', {}).get('location', {}).get('lat', 0.0))
        df['longitude'] = df['raw_data'].apply(lambda x: x.get('geometry', {}).get('location', {}).get('lng', 0.0))
        df['u_key'] = df.apply(lambda x: make_ukey(x['name'], x['latitude'], x['longitude']), axis=1)
        
        output_path = get_path(f"storage/silver/pois_google/{city}/data.parquet")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)

    def _merge_and_save(self, city: str):
        from src.shared.path_manager import get_path
        
        osm_path = get_path(f"storage/silver/pois_osm/{city}/data.parquet")
        google_path = get_path(f"storage/silver/pois_google/{city}/data.parquet")
        
        if not os.path.exists(osm_path): return
        
        df_osm = pd.read_parquet(osm_path)
        if os.path.exists(google_path):
            df_google = pd.read_parquet(google_path)
            df_final = pd.merge(df_osm, df_google, on="u_key", how="outer", suffixes=('', '_google'))
            # Combine logic...
            df_final['name'] = df_final['name'].fillna(df_final['name_google'])
        else:
            df_final = df_osm

        final_path = get_path(f"storage/silver/pois_cleaned/{city}.parquet")
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        df_final.to_parquet(final_path, index=False)
        
        # Save to MongoDB
        asyncio.run(self._save_to_mongo(df_final.to_dict('records')))

    async def _save_to_mongo(self, records: List[Dict]):
        if not records: return
        await self.silver_collection.delete_many({"u_key": {"$in": [r["u_key"] for r in records]}})
        await self.silver_collection.insert_many(records)

    def _build_osm_address(self, raw_data: dict) -> str:
        tags = raw_data.get('tags', {})
        parts = [tags.get(f"addr:{k}") for k in ["housenumber", "street", "city"] if tags.get(f"addr:{k}")]
        return ", ".join(parts)
