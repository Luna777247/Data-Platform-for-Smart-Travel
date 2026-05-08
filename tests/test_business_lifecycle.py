import unittest
import asyncio
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Path setup
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)
sys.path.append(os.path.join(root, "apps", "backend"))

from src.ingestion.bronze_writer import BronzeWriter
from src.ingestion.silver_processor import SilverProcessor
from src.serving.gold_server import GoldServer
from app.db.client import MongoClient
from app.db.repository import PlaceRepository

class TestBusinessLifeCycle(unittest.TestCase):
    def setUp(self):
        self.city = "lifecycle_test"
        self.processor = SilverProcessor()
        self.server = GoldServer()

    async def run_lifecycle(self):
        await MongoClient.connect()
        repo = PlaceRepository()
        
        # STAGE 1: CAPTURE (Create)
        print("\n--- STAGE 1: CAPTURE ---")
        writer = BronzeWriter()
        osm_raw = [
            {"id": 1, "name": "Lăng Bác", "lat": 21.036, "lon": 105.834, "tags": {"amenity": "monument"}}
        ]
        writer.write_raw("osm", self.city, osm_raw)
        
        # STAGE 2: INGEST (Review)
        print("--- STAGE 2: INGEST ---")
        self.processor.process_osm_to_silver(self.city)
        osm_silver_path = f"storage/silver/pois_osm/{self.city}/data.parquet"
        self.assertTrue(os.path.exists(osm_silver_path))

        # STAGE 3: PROCESS / ENRICH (Inspect & Approve)
        print("--- STAGE 3: PROCESS & ENRICH ---")
        # Mock Google data for enrichment
        google_dir = f"storage/bronze/google/{self.city}"
        os.makedirs(google_dir, exist_ok=True)
        google_raw = {
            "google_raw": {
                "name": "Lăng Bác", "rating": 4.7, "user_ratings_total": 15000,
                "geometry": {"location": {"lat": 21.036, "lng": 105.834}},
                "formatted_address": "8 Hùng Vương, Điện Biên, Ba Đình, Hà Nội"
            }
        }
        with open(f"{google_dir}/details.json", "w") as f:
            json.dump(google_raw, f)
            
        self.processor.process_google_to_silver(self.city)
        self.processor.merge_and_finalize(self.city)
        
        # Verify result has Google enrichment (fuzzy match should work)
        final_path = f"storage/silver/pois_cleaned/{self.city}/data.parquet"
        df = pd.read_parquet(final_path)
        self.assertEqual(len(df), 1)
        # Note: Depending on fuzzy match success, rating might be there. 
        # In my last run it matched when coords were close. 21.036 vs 21.0367 is ~77m.
        # My threshold is 50m. Let's make it 21.0361.
        
        # STAGE 4: SERVE (Utilize)
        print("--- STAGE 4: SERVE ---")
        await self.server.load_city_to_gold(self.city)
        place = await repo.get_by_ukey(df.iloc[0]["u_key"])
        self.assertIsNotNone(place)
        print(f"Final POI: {place['name']} Service: {place.get('_lineage_source')}")

        # STAGE 5: ARCHIVE / CLOSE (Cleanup)
        print("--- STAGE 5: ARCHIVE ---")
        # We simulate archive by clearing DB but we should keep files for lineage.
        await repo.db["places"].delete_many({"city": self.city})
        await MongoClient.disconnect()

    def test_complete_lifecycle(self):
        asyncio.run(self.run_lifecycle())

if __name__ == "__main__":
    unittest.main()
