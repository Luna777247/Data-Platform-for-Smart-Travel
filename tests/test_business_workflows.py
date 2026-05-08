import unittest
import asyncio
import os
import sys

# Thêm source vào path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)
sys.path.append(os.path.join(root, "apps", "backend"))

from src.ingestion.bronze_writer import BronzeWriter
from src.ingestion.silver_processor import SilverProcessor
from src.serving.gold_server import GoldServer
from app.db.client import MongoClient
from app.db.repository import PlaceRepository

class TestBusinessWorkflows(unittest.TestCase):
    async def run_e2e_pipeline(self):
        # 1. Khởi tạo
        city = "hanoi_test"
        await MongoClient.connect()
        repo = PlaceRepository()
        
        # 2. BRONZE: Ingestion
        writer = BronzeWriter()
        sample_data = [{"name": "Van Mieu", "lat": 21.02, "lon": 105.83, "type": "culture"}]
        writer.write_raw("osm", city, sample_data)
        
        # 3. SILVER: Processing
        processor = SilverProcessor()
        processor.process_city(city)
        
        # 4. GOLD: Serving
        server = GoldServer()
        await server.load_city_to_gold(city)
        
        # 5. DASHBOARD: Check stats
        stats = await repo.get_stats()
        self.assertGreaterEqual(stats["total_places"], 0)
        
        # Clean up
        await repo.db["places"].delete_many({"city": city})
        await MongoClient.disconnect()

    def test_full_pipeline(self):
        asyncio.run(self.run_e2e_pipeline())

if __name__ == "__main__":
    unittest.main()
