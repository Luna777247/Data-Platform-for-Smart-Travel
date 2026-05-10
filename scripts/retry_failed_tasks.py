#!/usr/bin/env python
"""
Retry Failed Tasks
==================
Collect missing data for low-count city/category combinations.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient
import requests


# Cities with low counts that need retry
RETRY_TARGETS = [
    {"city": "cantho", "lat": 10.0452, "lng": 105.7469, "category": "tourist_attraction"},
    {"city": "dalat", "lat": 11.9404, "lng": 108.4583, "category": "tourist_attraction"},
    {"city": "hue", "lat": 16.4637, "lng": 107.5909, "category": "tourist_attraction"},
]

# Additional grid points for retry (finer grid)
GRID_OFFSETS = [
    {"lat": 0, "lng": 0},
    {"lat": 0.009, "lng": 0},      # ~1km north
    {"lat": -0.009, "lng": 0},     # ~1km south
    {"lat": 0, "lng": 0.009},      # ~1km east
    {"lat": 0, "lng": -0.009},     # ~1km west
]


def get_keys():
    keys_str = os.getenv("RAPID_API_KEYS", "")
    return [k.strip() for k in keys_str.split(",") if k.strip()]


def collect_for_point(city, category, lat, lng, key):
    """Collect POIs for single point."""
    url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
    
    try:
        headers = {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "google-map-places.p.rapidapi.com"
        }
        
        params = {
            "location": f"{lat},{lng}",
            "radius": "3000",  # Increased radius for retry
            "type": category,
            "language": "vi"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            records = []
            for place in results[:20]:
                record = {
                    "poi_id": f"google_{place.get('place_id', '')}",
                    "name": place.get("name", ""),
                    "category": category,
                    "city": city,
                    "country": "VN",
                    "location": {
                        "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                        "lng": place.get("geometry", {}).get("location", {}).get("lng")
                    },
                    "address": place.get("vicinity", ""),
                    "rating": place.get("rating"),
                    "review_count": place.get("user_ratings_total", 0),
                    "google_place_id": place.get("place_id"),
                    "types": place.get("types", []),
                    "_source": "google_real_retry",
                    "_retry_batch": "retry_20260510",
                    "_collected_at": datetime.now().isoformat()
                }
                records.append(record)
            
            return records
        else:
            print(f"  ⚠️ HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []


def main():
    print("=" * 60)
    print("🔄 RETRY FAILED TASKS")
    print("=" * 60)
    
    keys = get_keys()
    print(f"✅ Loaded {len(keys)} API keys")
    
    # Connect MongoDB
    client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
    db = client.smart_travel
    
    total_new = 0
    key_idx = 0
    
    for target in RETRY_TARGETS:
        city = target["city"]
        category = target["category"]
        base_lat = target["lat"]
        base_lng = target["lng"]
        
        print(f"\n📍 {city}/{category}")
        
        # Check current count
        current = db.bronze_records.count_documents({
            "city": city,
            "category": category
        })
        print(f"   Current: {current} POIs")
        
        new_records = []
        
        # Try multiple grid points
        for offset in GRID_OFFSETS:
            lat = base_lat + offset["lat"]
            lng = base_lng + offset["lng"]
            
            print(f"   🔍 Grid ({offset['lat']:+0.3f}, {offset['lng']:+0.3f})...", end=" ")
            
            key = keys[key_idx % len(keys)]
            key_idx += 1
            
            records = collect_for_point(city, category, lat, lng, key)
            
            if records:
                print(f"✅ {len(records)}")
                new_records.extend(records)
            else:
                print("⚠️ 0")
            
            time.sleep(1)
        
        # Save new records
        if new_records:
            # Deduplicate
            seen = set()
            unique = []
            for r in new_records:
                pid = r.get("poi_id")
                if pid and pid not in seen:
                    seen.add(pid)
                    unique.append(r)
            
            if unique:
                try:
                    db.bronze_records.insert_many(unique, ordered=False)
                    total_new += len(unique)
                    print(f"   💾 Saved: {len(unique)} new POIs")
                except Exception as e:
                    print(f"   ⚠️ Save error: {e}")
        
        # Check new total
        new_total = db.bronze_records.count_documents({
            "city": city,
            "category": category
        })
        print(f"   📊 New total: {new_total} (+{new_total - current})")
    
    client.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Retry complete: {total_new} new POIs added")
    print("=" * 60)


if __name__ == "__main__":
    main()
