"""
Bronze Ingestion Script
=======================

Chạy OSM ingestion cho 1-2 cities test.
Lưu raw data vào MongoDB bronze_records collection.
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pymongo import MongoClient
from pipelines.bronze.osm_collector import OSMCollector


CITIES = {
    "hanoi": {
        "lat": 21.0278,
        "lng": 105.8342,
        "radius": 15000,  # 15km radius
        "categories": ["restaurant", "cafe", "hotel", "attraction"]
    },
    "hcm": {
        "lat": 10.8231,
        "lng": 106.6297,
        "radius": 15000,
        "categories": ["restaurant", "cafe", "hotel", "attraction"]
    }
}


def run_bronze_ingestion():
    """Run bronze ingestion for test cities."""
    print("🚀 Starting Bronze Ingestion Phase...")
    print("=" * 50)
    
    # Setup MongoDB connection
    mongo_uri = os.getenv(
        "MONGODB_URI", 
        "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    )
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Create bronze collector
    collector = OSMCollector()
    
    total_collected = 0
    
    for city_name, city_config in CITIES.items():
        print(f"\n📍 Processing city: {city_name.upper()}")
        print(f"   Location: ({city_config['lat']}, {city_config['lng']})")
        print(f"   Radius: {city_config['radius']}m")
        
        city_records = 0
        
        for category in city_config["categories"]:
            print(f"\n   🔍 Collecting {category}...", end=" ")
            
            try:
                # Collect from OSM
                records = collector.collect(
                    city=city_name,
                    category=category,
                    lat=city_config["lat"],
                    lng=city_config["lng"],
                    radius=city_config["radius"]
                )
                
                if records:
                    # Add metadata
                    for record in records:
                        record.update({
                            "_ingestion_timestamp": datetime.utcnow().isoformat(),
                            "_city": city_name,
                            "_category": category,
                            "_source": "osm",
                            "_layer": "bronze"
                        })
                    
                    # Insert to MongoDB
                    result = db.bronze_records.insert_many(records)
                    inserted_count = len(result.inserted_ids)
                    city_records += inserted_count
                    
                    print(f"✅ {inserted_count} records")
                else:
                    print(f"⚠️  No records found")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        total_collected += city_records
        print(f"\n   📊 City total: {city_records} records")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 BRONZE INGESTION COMPLETE")
    print(f"   Total records: {total_collected}")
    
    # Verify
    bronze_count = db.bronze_records.count_documents({})
    print(f"   Bronze collection size: {bronze_count}")
    
    # Show breakdown
    for city in CITIES.keys():
        city_count = db.bronze_records.count_documents({"_city": city})
        print(f"   - {city}: {city_count} records")
    
    client.close()
    print("\n✅ Bronze ingestion finished!")


if __name__ == "__main__":
    run_bronze_ingestion()
