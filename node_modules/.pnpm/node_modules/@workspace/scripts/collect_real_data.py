"""
Collect Real OSM Data - Production Version
==========================================

Collect real POI data từ OpenStreetMap cho các thành phố chính.
Xử lý rate limiting và có thể resume.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from pipelines.ingestion.osm_collector_real import OSMCollectorReal


# Configuration
CITIES = {
    "hanoi": {
        "lat": 21.0278,
        "lng": 105.8342,
        "radius": 8000,  # ~8km radius
        "categories": ["restaurant", "cafe", "hotel", "attraction", "bar", "pharmacy"]
    },
    "hcm": {
        "lat": 10.8231,
        "lng": 106.6297,
        "radius": 8000,
        "categories": ["restaurant", "cafe", "hotel", "attraction", "bar", "pharmacy"]
    },
    "danang": {
        "lat": 16.0544,
        "lng": 108.2022,
        "radius": 6000,
        "categories": ["restaurant", "cafe", "hotel", "attraction"]
    }
}

PROGRESS_FILE = Path(__file__).parent / "collection_progress.json"


def load_progress():
    """Load collection progress."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    """Save collection progress."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def collect_real_data():
    """Main collection function."""
    print("🚀 Collecting Real OSM Data - Production")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_uri = os.getenv(
        "MONGODB_URI",
        "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    )
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Initialize collector
    collector = OSMCollectorReal(max_retries=3)
    
    # Load progress
    progress = load_progress()
    
    total_collected = 0
    city_totals = {}
    
    for city_name, config in CITIES.items():
        print(f"\n📍 Processing {city_name.upper()}")
        print(f"   Center: ({config['lat']}, {config['lng']})")
        print(f"   Radius: {config['radius']}m")
        
        city_records = []
        
        for category in config["categories"]:
            # Check if already collected
            progress_key = f"{city_name}_{category}"
            if progress.get(progress_key):
                print(f"   ⏭️  {category}: Already collected (skipped)")
                continue
            
            print(f"   🔍 Collecting {category}...", end=" ", flush=True)
            
            try:
                records = collector.collect(
                    city=city_name,
                    category=category,
                    lat=config["lat"],
                    lng=config["lng"],
                    radius=config["radius"]
                )
                
                if records:
                    # Add metadata
                    for record in records:
                        record.update({
                            "_ingestion_timestamp": datetime.utcnow().isoformat(),
                            "_collection_batch": "real_v1"
                        })
                    
                    city_records.extend(records)
                    print(f"✅ {len(records)} records")
                    
                    # Mark as collected
                    progress[progress_key] = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "count": len(records)
                    }
                    save_progress(progress)
                else:
                    print("⚠️  No records")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:40]}")
                continue
        
        # Save to MongoDB
        if city_records:
            try:
                # Clear old real data for this city
                db.bronze_records.delete_many({
                    "_city": city_name,
                    "_source": "osm_real"
                })
                
                # Insert new records
                result = db.bronze_records.insert_many(city_records)
                inserted_count = len(result.inserted_ids)
                total_collected += inserted_count
                city_totals[city_name] = inserted_count
                
                print(f"   💾 Saved {inserted_count} records to MongoDB")
                
            except Exception as e:
                print(f"   ❌ MongoDB error: {e}")
                city_totals[city_name] = 0
        else:
            city_totals[city_name] = 0
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 REAL OSM DATA COLLECTION COMPLETE")
    print(f"   Total records collected: {total_collected}")
    print()
    print("   By City:")
    for city, count in city_totals.items():
        print(f"     - {city}: {count} POIs")
    
    # Verify in MongoDB
    print("\n   Verification:")
    for city in CITIES.keys():
        count = db.bronze_records.count_documents({
            "_city": city,
            "_source": "osm_real"
        })
        print(f"     - {city}: {count} records in DB")
    
    client.close()
    
    # Clean up progress file
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    
    print("\n✅ Collection complete!")
    print("\n📝 Next steps:")
    print("   1. Run: python scripts/run_silver_processing.py")
    print("   2. Run: python scripts/run_gold_processing.py")
    print("   3. Test API with real data!")


if __name__ == "__main__":
    collect_real_data()
