#!/usr/bin/env python
"""
Mass Collection System - Phase 2
==================================
Thu thập thêm 15 Tier-2 cities
Target: +5,000-8,000 POIs
Total sau Phase 2: ~15,000-18,000 POIs
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient
import requests


# ==========================================
# CONFIGURATION - PHASE 2
# ==========================================

CITIES_TIER2 = {
    # Northern Vietnam
    "vinh": {"lat": 18.6796, "lng": 105.6813},           # Nghệ An
    "quangninh": {"lat": 20.9516, "lng": 107.0815},      # Hạ Long
    "langson": {"lat": 21.8533, "lng": 106.7629},        # Lạng Sơn
    "thainguyen": {"lat": 21.5942, "lng": 105.8482},     # Thái Nguyên
    
    # Central Vietnam  
    "quynhon": {"lat": 13.7820, "lng": 109.2197},         # Bình Định
    "tuyhoa": {"lat": 13.0958, "lng": 109.3089},         # Phú Yên
    "camranh": {"lat": 11.9214, "lng": 109.1591},        # Khánh Hòa
    "phanthiet": {"lat": 10.9805, "lng": 108.2615},       # Bình Thuận
    
    # Southern Vietnam
    "vungtau": {"lat": 10.3460, "lng": 107.0843},        # Bà Rịa-Vũng Tàu
    "tayninh": {"lat": 11.3081, "lng": 106.0956},        # Tây Ninh
    "longan": {"lat": 10.6956, "lng": 106.6451},         # Long An
    "tiengiang": {"lat": 10.3600, "lng": 106.3600},      # Tiền Giang
    "bentre": {"lat": 10.2373, "lng": 106.3757},         # Bến Tre
    
    # Highlands
    "buonmathuot": {"lat": 12.6667, "lng": 108.0500},     # Đắk Lắk
    "pleiku": {"lat": 13.9833, "lng": 108.0000},         # Gia Lai
}

# Extended categories
CATEGORIES = [
    "restaurant", "cafe", "hotel", "tourist_attraction",
    "shopping_mall", "supermarket", "bar", "spa", 
    "convenience_store", "bakery"  # Added 2 more
]

GRID_POINTS = 9  # 3x3 grid
SEARCH_RADIUS = 2000
MAX_WORKERS = 5


class MassCollectorPhase2:
    """Phase 2 collector for Tier-2 cities."""
    
    def __init__(self):
        self.mongo = MongoClient(
            "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
        )
        self.db = self.mongo.smart_travel
        self.keys = self._load_keys()
        self.key_index = 0
        self.job_id = f"mass_p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "total_records": 0,
        }
    
    def _load_keys(self):
        keys_str = os.getenv("RAPID_API_KEYS", "")
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        print(f"✅ Loaded {len(keys)} RapidAPI keys")
        return keys
    
    def get_key(self):
        if not self.keys:
            raise ValueError("No API keys available")
        key = self.keys[self.key_index % len(self.keys)]
        self.key_index += 1
        if self.key_index % 100 == 0:
            time.sleep(1)
        return key
    
    def create_grid(self, city_data, num_points=9):
        center_lat = city_data["lat"]
        center_lng = city_data["lng"]
        
        points = []
        spacing = 0.018
        
        offsets = [-1, 0, 1]
        for i in offsets:
            for j in offsets:
                lat = center_lat + (i * spacing)
                lng = center_lng + (j * spacing)
                points.append({
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                })
        
        return points[:num_points]
    
    def collect_single(self, city, category, point):
        url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
        
        for attempt in range(5):
            try:
                headers = {
                    "x-rapidapi-key": self.get_key(),
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
                            "_source": "google_real_phase2",
                            "_job_id": self.job_id,
                            "_city_tier": "tier2",
                            "_collected_at": datetime.now().isoformat()
                        }
                        records.append(record)
                    
                    return {"success": True, "count": len(records), "records": records}
                    
                elif response.status_code in [429, 403]:
                    time.sleep(5 if response.status_code == 429 else 2)
                    self.key_index += 1
                    continue
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                if attempt == 4:
                    return {"success": False, "error": str(e)}
                time.sleep(2)
        
        return {"success": False, "error": "Max retries"}
    
    def save_records(self, records):
        if not records:
            return 0
        
        seen = set()
        unique_records = []
        
        for r in records:
            poi_id = r.get("poi_id")
            if poi_id and poi_id not in seen:
                seen.add(poi_id)
                unique_records.append(r)
        
        if unique_records:
            try:
                self.db.bronze_records.insert_many(unique_records, ordered=False)
                return len(unique_records)
            except:
                return len(unique_records)
        
        return 0
    
    def run_collection(self):
        total_tasks = len(CITIES_TIER2) * len(CATEGORIES) * GRID_POINTS
        
        print("=" * 70)
        print("🚀 MASS COLLECTION - PHASE 2")
        print("=" * 70)
        print(f"🏙️ Tier-2 Cities: {len(CITIES_TIER2)}")
        print(f"📁 Categories: {len(CATEGORIES)}")
        print(f"🔍 Grid points: {GRID_POINTS}")
        print(f"📊 Total tasks: {total_tasks}")
        print(f"📝 Job ID: {self.job_id}")
        print("=" * 70)
        
        start_time = time.time()
        all_records = []
        batch_size = 100
        
        tasks = []
        for city_name, city_data in CITIES_TIER2.items():
            grid = self.create_grid(city_data, GRID_POINTS)
            for category in CATEGORIES:
                for point in grid:
                    tasks.append((city_name, category, point))
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_task = {
                executor.submit(self.collect_single, city, cat, point): (city, cat, point)
                for city, cat, point in tasks
            }
            
            for future in as_completed(future_to_task):
                try:
                    result = future.result(timeout=60)
                    
                    if result["success"]:
                        if result["records"]:
                            all_records.extend(result["records"])
                            self.stats["completed"] += 1
                            self.stats["total_records"] += result["count"]
                    else:
                        self.stats["failed"] += 1
                        
                except Exception as e:
                    self.stats["failed"] += 1
                
                if len(all_records) >= batch_size:
                    saved = self.save_records(all_records)
                    all_records = []
                
                completed_total = self.stats["completed"] + self.stats["failed"]
                if completed_total % 30 == 0:
                    elapsed = time.time() - start_time
                    rate = completed_total / elapsed if elapsed > 0 else 0
                    pct = (completed_total / total_tasks) * 100
                    print(f"📈 {completed_total}/{total_tasks} ({pct:.1f}%) | "
                          f"POIs: {self.stats['total_records']} | "
                          f"Rate: {rate:.1f}/sec")
                
                time.sleep(0.3)
        
        if all_records:
            self.save_records(all_records)
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("✅ PHASE 2 COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"✅ Tasks: {self.stats['completed']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"📊 New POIs: {self.stats['total_records']}")
        
        # Show by city
        print("\n📍 By City:")
        for city in CITIES_TIER2.keys():
            count = self.db.bronze_records.count_documents({
                "city": city,
                "_job_id": self.job_id
            })
            if count > 0:
                print(f"   {city}: {count}")
        
        self.db.collection_jobs.insert_one({
            "job_id": self.job_id,
            "phase": "phase2",
            "status": "completed",
            "cities": list(CITIES_TIER2.keys()),
            "stats": self.stats,
            "elapsed_seconds": elapsed,
            "created_at": datetime.now().isoformat()
        })
        
        print(f"\n💾 Job saved: {self.job_id}")
        print("=" * 70)
        
        return self.stats["total_records"]
    
    def close(self):
        self.mongo.close()


def main():
    collector = MassCollectorPhase2()
    
    try:
        new_pois = collector.run_collection()
        
        # Check total
        total = collector.db.bronze_records.count_documents({})
        print(f"\n🎉 Phase 2 added: {new_pois} POIs")
        print(f"📊 Total Bronze: {total} POIs")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()


if __name__ == "__main__":
    main()
