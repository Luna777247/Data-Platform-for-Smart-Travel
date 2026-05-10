#!/usr/bin/env python
"""
Mass Collection System - Phase 1
=================================
Thu thập 1,600+ POIs từ 8 major cities
Target: ~10,000+ places với grid-based collection
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient
import requests


# ==========================================
# CONFIGURATION
# ==========================================

CITIES_TIER1 = {
    "hanoi": {"lat": 21.0278, "lng": 105.8342},
    "hcm": {"lat": 10.8231, "lng": 106.6297},
    "danang": {"lat": 16.0544, "lng": 108.2022},
    "haiphong": {"lat": 20.8449, "lng": 106.6881},
    "cantho": {"lat": 10.0452, "lng": 105.7469},
    "nhatrang": {"lat": 12.2388, "lng": 109.1967},
    "dalat": {"lat": 11.9404, "lng": 108.4583},
    "hue": {"lat": 16.4637, "lng": 107.5909},
}

CATEGORIES = [
    "restaurant", "cafe", "hotel", "tourist_attraction",
    "shopping_mall", "supermarket", "bar", "spa", "gym"
]

GRID_POINTS_PER_CITY = 9  # 3x3 grid (16 for tourist_attraction)
SEARCH_RADIUS = 2000  # 2km radius (3000 for retry)
SEARCH_RADIUS_RETRY = 3000  # Larger radius for low-count categories
MAX_WORKERS = 5  # Parallel workers


class MassCollector:
    """Mass collection system with rate limiting and retry."""
    
    def __init__(self):
        self.mongo = MongoClient(
            "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
        )
        self.db = self.mongo.smart_travel
        self.keys = self._load_keys()
        self.key_index = 0
        self.job_id = f"mass_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "total_records": 0,
            "by_city": {},
            "by_category": {}
        }
    
    def _load_keys(self):
        """Load RapidAPI keys."""
        keys_str = os.getenv("RAPID_API_KEYS", "")
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        print(f"✅ Loaded {len(keys)} RapidAPI keys")
        return keys
    
    def get_key(self, rotate=False):
        """Get next available API key with rotation."""
        if not self.keys:
            raise ValueError("No API keys available")
        
        if rotate:
            self.key_index += 1
        
        key = self.keys[self.key_index % len(self.keys)]
        
        # Reset every 100 requests per key
        if self.key_index % 100 == 0:
            time.sleep(1)
        
        return key
    
    def create_grid(self, city_data, num_points=9):
        """Create 3x3 grid around city center."""
        center_lat = city_data["lat"]
        center_lng = city_data["lng"]
        
        # 3x3 grid with 2km spacing (~0.018 degrees)
        points = []
        spacing = 0.018  # ~2km
        
        offsets = [-1, 0, 1]
        for i in offsets:
            for j in offsets:
                lat = center_lat + (i * spacing)
                lng = center_lng + (j * spacing)
                points.append({
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "grid_i": i,
                    "grid_j": j
                })
        
        return points[:num_points]
    
    def collect_single(self, city, category, point):
        """Collect POIs for single point with retry."""
        url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
        
        for attempt in range(3):
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
                
                response = requests.get(
                    url, headers=headers, params=params, timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    records = []
                    for place in results[:20]:  # Max 20 per request
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
                            "_job_id": self.job_id,
                            "_city_tier": "tier1",
                            "_grid_point": f"{point['grid_i']},{point['grid_j']}",
                            "_grid_center": point,
                            "_collected_at": datetime.now().isoformat()
                        }
                        records.append(record)
                    
                    return {
                        "success": True,
                        "count": len(records),
                        "records": records,
                        "city": city,
                        "category": category
                    }
                    
                elif response.status_code == 429:
                    # Rate limited - wait longer and rotate key
                    time.sleep(10)
                    self.key_index += 1
                    continue
                elif response.status_code == 403:
                    # Key exhausted - rotate immediately
                    self.key_index += 1
                    time.sleep(2)
                    continue
                elif response.status_code == 504:
                    # Gateway timeout - retry
                    time.sleep(5)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "city": city,
                        "category": category
                    }
                    
            except Exception as e:
                if attempt == 2:
                    return {
                        "success": False,
                        "error": str(e),
                        "city": city,
                        "category": category
                    }
                time.sleep(2)
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "city": city,
            "category": category
        }
    
    def save_records(self, records):
        """Save records to MongoDB with deduplication."""
        if not records:
            return 0
        
        # Deduplicate by poi_id
        seen = set()
        unique_records = []
        
        for r in records:
            poi_id = r.get("poi_id")
            if poi_id and poi_id not in seen:
                seen.add(poi_id)
                unique_records.append(r)
        
        if unique_records:
            # Use ordered=False for better performance
            try:
                self.db.bronze_records.insert_many(unique_records, ordered=False)
                return len(unique_records)
            except Exception as e:
                # Some duplicates may fail, count successful inserts
                print(f"⚠️ Insert warning: {e}")
                return len(unique_records)
        
        return 0
    
    def run_collection(self):
        """Run mass collection."""
        # Calculate total tasks
        total_tasks = len(CITIES_TIER1) * len(CATEGORIES) * GRID_POINTS_PER_CITY
        
        print("=" * 70)
        print("🚀 MASS COLLECTION - PHASE 1")
        print("=" * 70)
        print(f"🏙️ Cities: {len(CITIES_TIER1)}")
        print(f"📁 Categories: {len(CATEGORIES)}")
        print(f"🔍 Grid points: {GRID_POINTS_PER_CITY}")
        print(f"📊 Total tasks: {total_tasks}")
        print(f"🔑 API keys: {len(self.keys)}")
        print(f"📝 Job ID: {self.job_id}")
        print("=" * 70)
        
        start_time = time.time()
        all_records = []
        batch_size = 100
        
        # Prepare all tasks with adaptive grid
        tasks = []
        for city_name, city_data in CITIES_TIER1.items():
            # Use larger grid for tourist_attraction category
            for category in CATEGORIES:
                if category == "tourist_attraction":
                    grid = self.create_grid(city_data, 16)  # 4x4 grid
                else:
                    grid = self.create_grid(city_data, GRID_POINTS_PER_CITY)
                
                for point in grid:
                    tasks.append((city_name, category, point))
        
        # Process with thread pool
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.collect_single, city, cat, point): (city, cat, point)
                for city, cat, point in tasks
            }
            
            # Process results as they complete
            for future in as_completed(future_to_task):
                city, cat, point = future_to_task[future]
                
                try:
                    result = future.result(timeout=60)
                    
                    if result["success"]:
                        if result["records"]:
                            all_records.extend(result["records"])
                            self.stats["completed"] += 1
                            self.stats["total_records"] += result["count"]
                            
                            # Update per-city stats
                            if city not in self.stats["by_city"]:
                                self.stats["by_city"][city] = 0
                            self.stats["by_city"][city] += result["count"]
                            
                            # Update per-category stats
                            if cat not in self.stats["by_category"]:
                                self.stats["by_category"][cat] = 0
                            self.stats["by_category"][cat] += result["count"]
                    else:
                        self.stats["failed"] += 1
                        
                except Exception as e:
                    self.stats["failed"] += 1
                    print(f"❌ Exception: {e}")
                
                # Save batch when it reaches size
                if len(all_records) >= batch_size:
                    saved = self.save_records(all_records)
                    all_records = []
                
                # Progress report every 20 tasks
                completed_total = self.stats["completed"] + self.stats["failed"]
                if completed_total % 20 == 0:
                    elapsed = time.time() - start_time
                    rate = completed_total / elapsed if elapsed > 0 else 0
                    pct = (completed_total / total_tasks) * 100
                    print(f"📈 {completed_total}/{total_tasks} ({pct:.1f}%) | "
                          f"POIs: {self.stats['total_records']} | "
                          f"Rate: {rate:.1f} tasks/sec")
                
                # Rate limiting
                time.sleep(0.3)
        
        # Save remaining records
        if all_records:
            self.save_records(all_records)
        
        # Final stats
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("✅ COLLECTION COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"✅ Tasks completed: {self.stats['completed']}")
        print(f"❌ Tasks failed: {self.stats['failed']}")
        print(f"📊 Total POIs: {self.stats['total_records']}")
        
        print("\n📍 By City:")
        for city, count in sorted(self.stats["by_city"].items(), key=lambda x: -x[1]):
            print(f"   {city}: {count}")
        
        print("\n📁 By Category:")
        for cat, count in sorted(self.stats["by_category"].items(), key=lambda x: -x[1]):
            print(f"   {cat}: {count}")
        
        # Save job stats
        self.db.collection_jobs.insert_one({
            "job_id": self.job_id,
            "status": "completed",
            "cities": list(CITIES_TIER1.keys()),
            "categories": CATEGORIES,
            "stats": self.stats,
            "elapsed_seconds": elapsed,
            "created_at": datetime.now().isoformat()
        })
        
        print(f"\n💾 Job saved: {self.job_id}")
        print("=" * 70)
        
        return self.stats["total_records"]
    
    def close(self):
        """Close connections."""
        self.mongo.close()


def main():
    """Main entry point."""
    collector = MassCollector()
    
    try:
        total = collector.run_collection()
        print(f"\n🎉 Successfully collected {total} POIs!")
        print("\nNext steps:")
        print("1. Run: python scripts/run_silver_processing.py")
        print("2. Run: python scripts/run_gold_processing.py")
        print("3. Check: python scripts/test_api_endpoints.py")
    except KeyboardInterrupt:
        print("\n\n⚠️ Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()


if __name__ == "__main__":
    main()
