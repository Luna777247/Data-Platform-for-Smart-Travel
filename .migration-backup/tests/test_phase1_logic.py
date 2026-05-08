import unittest
import pandas as pd
import json
import os
from src.shared.data_utils import make_ukey, compute_poi_hash

class TestPhase1Logic(unittest.TestCase):
    def setUp(self):
        self.sample_data = [
            {"name": "Hồ Gươm", "location": {"lat": 21.0285123, "lon": 105.8542456}, "rating": 4.8}, # Source OSM
            {"name": "Ho Guom", "location": {"lat": 21.0285, "lon": 105.8542}, "rating": 4.9}        # Source Google
        ]

    def test_ukey_consistency(self):
        """Kiểm tra xem 2 nguồn có tọa độ lệch nhẹ có sinh ra cùng u_key không."""
        key1 = make_ukey(self.sample_data[0]["name"], 
                         self.sample_data[0]["location"]["lat"], 
                         self.sample_data[0]["location"]["lon"])
        
        key2 = make_ukey(self.sample_data[1]["name"], 
                         self.sample_data[1]["location"]["lat"], 
                         self.sample_data[1]["location"]["lon"])
        
        print(f"Key 1 (OSM): {key1}")
        print(f"Key 2 (Google): {key2}")
        self.assertEqual(key1, key2, "U-Key must match for same location with minor coordinate precision difference")

    def test_deduplication_logic(self):
        """Mô phỏng logic của SilverProcessor: gộp dữ liệu."""
        processed = []
        for item in self.sample_data:
            item["u_key"] = make_ukey(item["name"], item["location"]["lat"], item["location"]["lon"])
            item["ingestion_at"] = "2026-04-25T10:00:00"
            processed.append(item)
            
        df = pd.DataFrame(processed)
        df_silver = df.drop_duplicates(subset=["u_key"], keep="first")
        
        self.assertEqual(len(df_silver), 1, "Deduplication should result in 1 record")

    def test_poi_hash(self):
        """Kiểm tra logic Change Detection."""
        poi = {"rating": 4.5, "reviews": 100, "status": "operational"}
        hash1 = compute_poi_hash(poi)
        
        # Thay đổi không quan trọng (ví dụ description) không làm đổi hash
        poi["description"] = "New description"
        hash2 = compute_poi_hash(poi)
        self.assertEqual(hash1, hash2)
        
        # Thay đổi rating phải làm đổi hash
        poi["rating"] = 4.6
        hash3 = compute_poi_hash(poi)
        self.assertNotEqual(hash1, hash3)

if __name__ == "__main__":
    unittest.main()
