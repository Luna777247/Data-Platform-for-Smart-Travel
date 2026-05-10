"""
Generate Mock Bronze Data
=========================

Generate mock OSM data cho Bronze layer testing.
"""

import os
import sys
from datetime import datetime
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pymongo import MongoClient


CITIES = {
    "hanoi": {"lat": 21.0278, "lng": 105.8342},
    "hcm": {"lat": 10.8231, "lng": 106.6297},
    "danang": {"lat": 16.0544, "lng": 108.2022}
}

CATEGORIES = {
    "restaurant": {"amenity": "restaurant", "cuisine": "vietnamese"},
    "cafe": {"amenity": "cafe"},
    "hotel": {"tourism": "hotel"},
    "attraction": {"tourism": "attraction"}
}

NAMES = {
    "restaurant": ["Pho Gia Truyen", "Bun Cha Ha Noi", "Com Tam Cali", "Lau De", "Banh Xeo"],
    "cafe": ["Highlands Coffee", "Cong Caphe", "The Coffee House", "Starbucks", "Trung Nguyen"],
    "hotel": ["Melia Hotel", "Pullman Hotel", "Novotel", "InterContinental", "Sofitel"],
    "attraction": ["Hoan Kiem Lake", "Ben Thanh Market", "Dragon Bridge", "Old Quarter", "Beach"]
}


def generate_mock_bronze_data():
    """Generate mock bronze data."""
    print("🚀 Generating Mock Bronze Data...")
    print("=" * 50)
    
    # Connect to MongoDB
    mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Clear existing bronze data
    print("🗑️  Clearing existing bronze records...")
    db.bronze_records.delete_many({"_source": "mock"})
    
    total = 0
    
    for city, coords in CITIES.items():
        print(f"\n📍 Processing {city.upper()}...")
        
        for category, osm_tags in CATEGORIES.items():
            records = []
            
            for i in range(25):  # 25 POIs per category per city
                name = random.choice(NAMES[category])
                unique_name = f"{name} {i+1}"
                
                # Random offset from city center
                lat_offset = random.uniform(-0.03, 0.03)
                lng_offset = random.uniform(-0.03, 0.03)
                
                record = {
                    "poi_id": f"mock_{city}_{category}_{i}",
                    "name": unique_name,
                    "name_en": unique_name,
                    "category": category,
                    "city": city,
                    "country": "VN",
                    "location": {
                        "lat": round(coords["lat"] + lat_offset, 6),
                        "lng": round(coords["lng"] + lng_offset, 6)
                    },
                    "address": f"{random.randint(1, 200)} {random.choice(['Le Loi', 'Nguyen Hue', 'Tran Hung Dao'])}, {city.title()}",
                    "osm_tags": osm_tags,
                    "osm_id": random.randint(1000000, 9999999),
                    "osm_type": "node",
                    "raw_data": {
                        "type": "node",
                        "id": random.randint(1000000, 9999999),
                        "lat": round(coords["lat"] + lat_offset, 6),
                        "lon": round(coords["lng"] + lng_offset, 6),
                        "tags": {**osm_tags, "name": unique_name}
                    },
                    "_ingestion_timestamp": datetime.utcnow().isoformat(),
                    "_city": city,
                    "_category": category,
                    "_source": "mock",
                    "_layer": "bronze"
                }
                
                records.append(record)
            
            # Insert to MongoDB
            if records:
                result = db.bronze_records.insert_many(records)
                total += len(result.inserted_ids)
                print(f"   ✅ {category}: {len(result.inserted_ids)} records")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 MOCK BRONZE DATA COMPLETE")
    print(f"   Total records: {total}")
    
    # Verify
    bronze_count = db.bronze_records.count_documents({"_source": "mock"})
    print(f"   Bronze collection size: {bronze_count}")
    
    # Show breakdown
    for city in CITIES.keys():
        city_count = db.bronze_records.count_documents({"_city": city, "_source": "mock"})
        print(f"   - {city}: {city_count} records")
    
    client.close()
    print("\n✅ Mock bronze data generation finished!")


if __name__ == "__main__":
    generate_mock_bronze_data()
