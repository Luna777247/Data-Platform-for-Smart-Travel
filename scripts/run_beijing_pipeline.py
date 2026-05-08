
import asyncio
import os
import sys
from pathlib import Path

# Thêm đường dẫn project vào sys.path
sys.path.append(os.getcwd())

from src.ingestion.bronze_writer import BronzeWriter
from src.ingestion.silver_processor import SilverProcessor
from src.serving.gold_server import GoldServer
from app.db.client import MongoClient

async def run_beijing_pipeline():
    city = "beijing"
    print(f"🌆 Khởi động Pipeline cho thành phố: {city.upper()}...")

    # 1. BRONZE LAYER: Ingestion
    writer = BronzeWriter()
    
    # Dữ liệu mẫu thực tế cho Bắc Kinh (Beijing)
    beijing_osm_data = [
        {"id": "node/1", "name": "The Palace Museum", "lat": 39.9163, "lon": 116.3972, "type": "tourism", "amenity": "museum"},
        {"id": "node/2", "name": "Temple of Heaven", "lat": 39.8822, "lon": 116.4066, "type": "tourism", "amenity": "place_of_worship"},
        {"id": "node/3", "name": "Summer Palace", "lat": 40.0000, "lon": 116.2733, "type": "tourism", "amenity": "park"}
    ]
    
    beijing_google_data = [
        {"place_id": "g1", "name": "Palace Museum", "lat": 39.9163, "lng": 116.3972, "rating": 4.8, "user_ratings_total": 45000},
        {"place_id": "g2", "name": "Great Wall at Badaling", "lat": 40.3597, "lng": 116.0200, "rating": 4.7, "user_ratings_total": 32000}
    ]

    print("  [Bronze] Đang ghi dữ liệu thô vào hạ tầng lưu trữ...")
    writer.write_raw("osm", city, beijing_osm_data)
    writer.write_raw("google", city, beijing_google_data)

    # 2. SILVER LAYER: Processing
    print("  [Silver] Đang thực hiện Clean & Merry (Merge + Deduplicate)...")
    processor = SilverProcessor()
    processor.process_osm_to_silver(city)
    processor.merge_and_finalize(city)

    # 3. GOLD LAYER: Loading to MongoDB
    print("  [Gold] Đang nạp dữ liệu Tinh hoa vào MongoDB...")
    await MongoClient.connect()
    server = GoldServer()
    await server.load_city_to_gold(city)
    await MongoClient.disconnect()

    print(f"✅ Pipeline cho {city.upper()} đã hoàn thành thành công!")

if __name__ == "__main__":
    asyncio.run(run_beijing_pipeline())
