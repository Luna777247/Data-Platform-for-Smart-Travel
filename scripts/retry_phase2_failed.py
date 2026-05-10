#!/usr/bin/env python
"""
Retry Phase 2 Failed Cities
===========================
Thu thập lại 7 cities có ít/nodata từ Phase 2:
- vungtau (20 POIs)
- tayninh (23 POIs)
- pleiku (26 POIs)
- longan (0 POIs)
- tiengiang (0 POIs)
- bentre (0 POIs)
- buonmathuot (0 POIs)
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


# Cities cần retry với coordinates
RETRY_CITIES = {
    "vungtau": {"lat": 10.3460, "lng": 107.0843},
    "tayninh": {"lat": 11.3081, "lng": 106.0956},
    "pleiku": {"lat": 13.9833, "lng": 108.0000},
    "longan": {"lat": 10.6956, "lng": 106.6451},
    "tiengiang": {"lat": 10.3600, "lng": 106.3600},
    "bentre": {"lat": 10.2373, "lng": 106.3757},
    "buonmathuot": {"lat": 12.6667, "lng": 108.0500},
}

# Core categories
CATEGORIES = [
    "restaurant", "cafe", "hotel", "tourist_attraction",
    "shopping_mall", "supermarket", "bar"
]

SEARCH_RADIUS = 3000  # Tăng radius cho retry
GRID_POINTS = 5  # 5 points per city


def get_keys():
    keys_str = os.getenv("RAPID_API_KEYS", "")
    return [k.strip() for k in keys_str.split(",") if k.strip()]


def create_grid(center, num_points=5):
    """Create grid around center point."""
    points = [
        {"lat": center["lat"], "lng": center["lng"]},  # Center
        {"lat": center["lat"] + 0.009, "lng": center["lng"]},  # North
        {"lat": center["lat"] - 0.009, "lng": center["lng"]},  # South
        {"lat": center["lat"], "lng": center["lng"] + 0.009},  # East
        {"lat": center["lat"], "lng": center["lng"] - 0.009},  # West
    ]
    return points[:num_points]


def collect_for_point(city, category, point, key):
    """Collect POIs for single point."""
    url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
    
    try:
        headers = {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "google-map-places.p.rapidapi.com"
        }
        
        params = {
            "location": f"{point['lat']},{point['lng']}",
            "radius": str(SEARCH_RADIUS),
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
                    "_source": "google_real_p2_retry",
                    "_retry_batch": "p2_retry_20260510",
                    "_collected_at": datetime.now().isoformat()
                }
                records.append(record)
            
            return records
        else:
            return []
            
    except Exception as e:
        return []


def main():
    print("=" * 60)
    print("🔄 RETRY PHASE 2 FAILED CITIES")
    print("=" * 60)
    
    keys = get_keys()
    print(f"✅ Loaded {len(keys)} API keys")
    
    # Connect MongoDB
    client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
    db = client.smart_travel
    
    # Check current counts
    print("\n📊 Current counts before retry:")
    for city in RETRY_CITIES.keys():
        count = db.bronze_records.count_documents({"city": city})
        print(f"  {city}: {count} POIs")
    
    total_new = 0
    key_idx = 0
    
    for city, coords in RETRY_CITIES.items():
        print(f"\n📍 {city.upper()}")
        
        # Check current
        current = db.bronze_records.count_documents({"city": city})
        print(f"   Current: {current} POIs")
        
        new_records = []
        
        # Create grid
        grid = create_grid(coords, GRID_POINTS)
        
        for category in CATEGORIES:
            for point in grid:
                key = keys[key_idx % len(keys)]
                key_idx += 1
                
                records = collect_for_point(city, category, point, key)
                
                if records:
                    new_records.extend(records)
                
                time.sleep(0.5)  # Rate limiting
        
        # Save
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
        new_total = db.bronze_records.count_documents({"city": city})
        print(f"   📊 New total: {new_total} (+{new_total - current})")
    
    # Final stats
    print("\n" + "=" * 60)
    print("✅ RETRY COMPLETE")
    print("=" * 60)
    print(f"Total new POIs added: {total_new}")
    
    # Show all cities after retry
    print("\n📍 All 7 cities after retry:")
    total_all = 0
    for city in RETRY_CITIES.keys():
        count = db.bronze_records.count_documents({"city": city})
        print(f"  {city}: {count} POIs")
        total_all += count
    
    print(f"\n📊 Total from 7 cities: {total_all} POIs")
    
    # Overall total
    total_bronze = db.bronze_records.count_documents({})
    print(f"📊 Overall Bronze total: {total_bronze} POIs")
    
    client.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
