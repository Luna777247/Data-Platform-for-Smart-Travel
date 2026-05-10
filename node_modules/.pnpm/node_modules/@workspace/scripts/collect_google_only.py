#!/usr/bin/env python
"""
Collect Google Places Only - Fast Version
==========================================

Thu thập dữ liệu chỉ từ Google Places API (RapidAPI)
Bỏ qua OSM do rate limiting.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from pymongo import MongoClient
import requests


def get_rapidapi_keys():
    """Get RapidAPI keys."""
    keys_str = os.getenv("RAPID_API_KEYS", "")
    if keys_str:
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    return []


def collect_google_places(city, lat, lng, categories, key_index=0):
    """Collect from Google Places API."""
    keys = get_rapidapi_keys()
    if not keys:
        print("⚠️ No RapidAPI keys found")
        return []
    
    host = "google-map-places.p.rapidapi.com"
    url = f"https://{host}/maps/api/place/nearbysearch/json"
    
    all_records = []
    
    type_mapping = {
        "restaurant": "restaurant",
        "cafe": "cafe", 
        "hotel": "lodging",
        "tourist_attraction": "tourist_attraction"
    }
    
    for category in categories:
        print(f"   🔍 {category}...", end=" ", flush=True)
        
        success = False
        for attempt in range(min(3, len(keys))):
            api_key = keys[(key_index + attempt) % len(keys)]
            
            try:
                params = {
                    "location": f"{lat},{lng}",
                    "radius": "3000",
                    "type": type_mapping.get(category, "establishment"),
                    "language": "vi"
                }
                
                headers = {
                    "x-rapidapi-key": api_key,
                    "x-rapidapi-host": host
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    for place in results:
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
                            "_source": "google_real",
                            "_city": city,
                            "_category": category,
                            "_collected_at": datetime.now().isoformat(),
                            "_batch": "google_fast_v1"
                        }
                        all_records.append(record)
                    
                    print(f"✅ {len(results)}")
                    success = True
                    key_index += 1
                    break
                    
                elif response.status_code == 429:
                    continue  # Try next key
                else:
                    print(f"⚠️ HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                if attempt == 2:
                    print(f"❌ {str(e)[:40]}")
        
        if not success:
            print("⚠️ Failed")
        
        time.sleep(1)  # Rate limiting
    
    return all_records, key_index


def main():
    """Main collection."""
    print("="*60)
    print("🚀 GOOGLE PLACES FAST COLLECTION")
    print("="*60)
    
    # Connect to MongoDB
    mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Cities
    cities = {
        "hanoi": {"lat": 21.0278, "lng": 105.8342},
        "hcm": {"lat": 10.8231, "lng": 106.6297},
        "danang": {"lat": 16.0544, "lng": 108.2022}
    }
    
    categories = ["restaurant", "cafe", "hotel", "tourist_attraction"]
    
    total_records = 0
    key_index = 0
    
    for city_name, coords in cities.items():
        print(f"\n📍 {city_name.upper()}")
        print("-" * 40)
        
        # Collect
        records, key_index = collect_google_places(
            city=city_name,
            lat=coords["lat"],
            lng=coords["lng"],
            categories=categories,
            key_index=key_index
        )
        
        # Save to MongoDB
        if records:
            # Clear old data
            db.bronze_records.delete_many({
                "_city": city_name,
                "_source": "google_real"
            })
            
            # Insert new
            result = db.bronze_records.insert_many(records)
            count = len(result.inserted_ids)
            total_records += count
            print(f"💾 Saved: {count} records")
    
    client.close()
    
    # Summary
    print("\n" + "="*60)
    print("📊 COLLECTION COMPLETE")
    print("="*60)
    print(f"Total Google Places POIs: {total_records}")
    print("="*60)
    print("\n✅ Done! Run Silver/Gold processing next.")


if __name__ == "__main__":
    main()
