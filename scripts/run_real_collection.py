"""
Run Real Data Collection
==========================

Thu thập dữ liệu thật từ:
1. OSM (OpenStreetMap) - Overpass API
2. Google Places API - RapidAPI

Sử dụng 18 rotating keys để tránh rate limiting.
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_rapidapi_keys():
    """Get RapidAPI keys from environment."""
    keys_str = os.getenv("RAPID_API_KEYS", "")
    if keys_str:
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    return []


def collect_osm_data(city, lat, lng, radius=5000, categories=None):
    """Collect data from OSM Overpass API và lưu vào bronze_pois với osm_raw."""
    print(f"\n🗺️  Collecting OSM data for {city}...")
    
    # Use the fixed OSM collector
    from pipelines.ingestion.osm_collector_real import OSMCollectorReal
    collector = OSMCollectorReal(max_retries=2)
    
    if categories is None:
        categories = ["restaurant", "cafe", "hotel", "attraction"]
    
    all_records = []
    
    for category in categories:
        print(f"   🔍 {category}...", end=" ", flush=True)
        
        try:
            # Use the fixed collector with correct parameters
            api_response = collector.collect_with_raw(
                city=city,
                category=category,
                lat=lat,
                lng=lng,
                radius=radius
            )
            
            # api_response là dict chứa {records, query, endpoint, raw_response}
            records = api_response.get("records", [])
            query = api_response.get("query", "")
            endpoint = api_response.get("endpoint", "")
            raw_response = api_response.get("raw_response", {})
            
            if records:
                # Build bronze_pois documents với osm_raw
                for element in records:
                    bronze_doc = {
                        "u_key": f"{city}_{element.get('type')}_{element.get('id')}",
                        "poi_id": f"osm_{element.get('type')}_{element.get('id')}",
                        
                        # RAW OSM DATA
                        "osm_raw": {
                            "element": element,
                            "query": query,
                            "api_response": raw_response,
                            "endpoint": endpoint,
                            "fetched_at": datetime.utcnow().isoformat()
                        },
                        "google_raw": None,
                        
                        # FLAGS
                        "has_osm_data": True,
                        "has_google_data": False,
                        "data_sources": ["osm"],
                        
                        # BASIC INFO (extracted)
                        "name": element.get("tags", {}).get("name") or element.get("tags", {}).get("name:en"),
                        "city": city,
                        "category": category,
                        "location": {
                            "lat": element.get("lat") or element.get("center", {}).get("lat"),
                            "lon": element.get("lon") or element.get("center", {}).get("lon")
                        },
                        
                        # OSM IDs
                        "osm_id": element.get("id"),
                        "osm_type": element.get("type"),
                        
                        # METADATA
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "_layer": "bronze",
                        "_source": "osm_real"
                    }
                    all_records.append(bronze_doc)
                
                print(f"✅ {len(records)}")
            else:
                print("⚠️  0")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
    
    return all_records


def collect_google_data(city, lat, lng, radius=2000, categories=None):
    """Collect data from Google Places API via RapidAPI."""
    keys = get_rapidapi_keys()
    
    if not keys:
        print("⚠️  No RapidAPI keys found, skipping Google Places")
        return []
    
    print(f"\n🔍 Collecting Google Places data for {city}...")
    print(f"   Using {len(keys)} rotating API keys")
    
    # RapidAPI endpoints
    host = "google-map-places.p.rapidapi.com"
    nearby_url = f"https://{host}/maps/api/place/nearbysearch/json"
    
    import requests
    
    all_records = []
    
    if categories is None:
        categories = ["restaurant", "cafe", "hotel", "tourist_attraction"]
    
    type_mapping = {
        "restaurant": "restaurant",
        "cafe": "cafe",
        "hotel": "lodging",
        "tourist_attraction": "tourist_attraction"
    }
    
    for category in categories:
        print(f"   🔍 {category}...", end=" ", flush=True)
        
        # Rotate through keys
        key_index = 0
        success = False
        
        for attempt in range(min(3, len(keys))):
            api_key = keys[key_index % len(keys)]
            key_index += 1
            
            try:
                params = {
                    "location": f"{lat},{lng}",
                    "radius": str(radius),
                    "type": type_mapping.get(category, "establishment"),
                    "language": "vi"
                }
                
                headers = {
                    "x-rapidapi-key": api_key,
                    "x-rapidapi-host": host
                }
                
                response = requests.get(nearby_url, headers=headers, params=params, timeout=30)
                
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
                            "_collected_at": datetime.utcnow().isoformat(),
                            "_batch": "production_v1"
                        }
                        all_records.append(record)
                    
                    print(f"✅ {len(results)}")
                    success = True
                    break
                    
                elif response.status_code == 429:
                    # Rate limited, try next key
                    continue
                else:
                    print(f"⚠️  HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                if attempt == 2:  # Last attempt
                    print(f"❌ Error: {str(e)[:40]}")
        
        if not success:
            print("⚠️  Failed after retries")
        
        # Rate limiting between categories
        time.sleep(2)
    
    return all_records


def save_to_bronze_pois(records, db_name="smart_travel_platform"):
    """Save records to MongoDB bronze_pois collection với osm_raw schema."""
    if not records:
        print("⚠️  No records to save")
        return 0
    
    try:
        mongo_uri = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Insert records vào bronze_pois (với osm_raw, google_raw fields)
        result = db.bronze_pois.insert_many(records, ordered=False)
        print(f"💾 Saved {len(result.inserted_ids)} records to MongoDB bronze_pois")
        
        # Update stats
        total = db.bronze_pois.count_documents({})
        osm_count = db.bronze_pois.count_documents({"has_osm_data": True})
        google_count = db.bronze_pois.count_documents({"has_google_data": True})
        print(f"   📊 Total: {total} | OSM: {osm_count} | Google: {google_count}")
        
        client.close()
        return len(result.inserted_ids)
        
    except Exception as e:
        print(f"   ❌ MongoDB error: {e}")
        return 0


def main():
    """Main collection function."""
    print("=" * 60)
    print("🚀 REAL DATA COLLECTION - OSM + Google Places")
    print("=" * 60)
    
    # Cities to collect
    cities = {
        "hanoi": {"lat": 21.0278, "lng": 105.8342, "radius": 5000},
        "hcm": {"lat": 10.8231, "lng": 106.6297, "radius": 5000},
        "danang": {"lat": 16.0544, "lng": 108.2022, "radius": 4000}
    }
    
    total_osm = 0
    total_google = 0
    
    for city_name, coords in cities.items():
        print(f"\n{'='*60}")
        print(f"📍 PROCESSING: {city_name.upper()}")
        print(f"{'='*60}")
        
        # Collect OSM (trả về bronze_pois structure)
        osm_data = collect_osm_data(
            city=city_name,
            lat=coords["lat"],
            lng=coords["lng"],
            radius=coords["radius"]
        )
        total_osm += len(osm_data)
        
        # Collect Google (trả về bronze_pois structure với google_raw)
        google_data = collect_google_data(
            city=city_name,
            lat=coords["lat"],
            lng=coords["lng"],
            radius=coords["radius"]
        )
        total_google += len(google_data)
        
        # Combine và save to bronze_pois
        all_data = osm_data + google_data
        if all_data:
            save_to_bronze_pois(all_data)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COLLECTION COMPLETE")
    print("=" * 60)
    print(f"   OSM Total: {total_osm} records")
    print(f"   Google Total: {total_google} records")
    print(f"   Combined: {total_osm + total_google} real POIs")
    print("\n✅ Real data collection finished!")
    
    if total_osm + total_google > 0:
        print("\n📝 Next steps:")
        print("   1. Check raw data: python check_raw_structure.py")
        print("   2. Enrich Google: python enrich_google_raw.py")
        print("   3. Bronze → Silver: python scripts/process_all_bronze_to_gold.py")
        print("   4. Check API: curl http://localhost:8000/api/v1/data/pois")


if __name__ == "__main__":
    main()
