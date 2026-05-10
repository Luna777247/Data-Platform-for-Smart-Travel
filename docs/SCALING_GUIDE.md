# Hướng dẫn Mở rộng Hệ thống - 10,000+ Places

## Mục tiêu
- Thu thập **10,000+ real POIs**
- Hỗ trợ **unlimited cities** (toàn Việt Nam + khu vực lân cận)
- Tự động hóa 100%
- Quản lý rate limiting thông minh

---

## Phase 1: Mở rộng Danh sách Thành phố (20+ cities)

### Danh sách đề xuất:

#### Tier 1 - Major Cities (8 cities):
```python
CITIES_TIER1 = {
    "hanoi": {"lat": 21.0278, "lng": 105.8342, "population": 8_000_000},
    "hcm": {"lat": 10.8231, "lng": 106.6297, "population": 9_000_000},
    "danang": {"lat": 16.0544, "lng": 108.2022, "population": 1_200_000},
    "haiphong": {"lat": 20.8449, "lng": 106.6881, "population": 2_000_000},
    "cantho": {"lat": 10.0452, "lng": 105.7469, "population": 1_600_000},
    "nhatrang": {"lat": 12.2388, "lng": 109.1967, "population": 500_000},
    "dalat": {"lat": 11.9404, "lng": 108.4583, "population": 400_000},
    "hue": {"lat": 16.4637, "lng": 107.5909, "population": 450_000},
}
```

#### Tier 2 - Secondary Cities (15+ cities):
```python
CITIES_TIER2 = {
    "vinh": {"lat": 18.6796, "lng": 105.6813},
    "quangninh": {"lat": 20.9516, "lng": 107.0815},
    "quynhon": {"lat": 13.7820, "lng": 109.2197},
    "phanthiet": {"lat": 10.9805, "lng": 108.2615},
    "vungtau": {"lat": 10.3460, "lng": 107.0843},
    "buonmathuot": {"lat": 12.6667, "lng": 108.0500},
    "pleiku": {"lat": 13.9833, "lng": 108.0000},
    "tuyhoa": {"lat": 13.0958, "lng": 109.3089},
    "camranh": {"lat": 11.9214, "lng": 109.1591},
    "hagiang": {"lat": 22.8026, "lng": 104.9734},
    "sonla": {"lat": 21.3259, "lng": 103.9188},
    "dienbien": {"lat": 21.3860, "lng": 103.0230},
    "langson": {"lat": 21.8533, "lng": 106.7629},
    "caobang": {"lat": 22.6663, "lng": 106.2640},
    "laichau": {"lat": 22.3856, "lng": 103.4735},
}
```

#### Tier 3 - Tourist Destinations (15+ cities):
```python
CITIES_TIER3 = {
    "sapa": {"lat": 22.3364, "lng": 103.8436},
    "halong": {"lat": 20.9516, "lng": 107.0815},
    "hoian": {"lat": 15.8801, "lng": 108.3380},
    "phuquoc": {"lat": 10.2899, "lng": 103.9840},
    "condao": {"lat": 8.6939, "lng": 106.6098},
    "muine": {"lat": 10.9333, "lng": 108.1000},
    "tamcoc": {"lat": 20.2469, "lng": 105.9269},
    "phongnha": {"lat": 17.5500, "lng": 106.3000},
    "banahills": {"lat": 15.9978, "lng": 107.9978},
    "fansipan": {"lat": 22.3033, "lng": 103.7706},
    "cucphuong": {"lat": 20.2833, "lng": 105.7333},
    "baidinh": {"lat": 20.2893, "lng": 105.8978},
    "trangan": {"lat": 20.2500, "lng": 105.9200},
    "catba": {"lat": 20.7167, "lng": 107.0500},
    "chaudoc": {"lat": 10.7083, "lng": 105.1167},
}
```

**Total: ~38 cities**

---

## Phase 2: Mở rộng Categories (15+ types)

```python
CATEGORIES = [
    # Food & Drink
    "restaurant", "cafe", "bar", "bakery", "food_court",
    
    # Accommodation
    "hotel", "hostel", "resort", "guest_house", "homestay",
    
    # Tourism
    "tourist_attraction", "museum", "temple", "park", "beach",
    
    # Shopping
    "shopping_mall", "market", "convenience_store", "supermarket",
    
    # Services
    "atm", "bank", "pharmacy", "hospital", "gas_station",
    
    # Transportation
    "airport", "bus_station", "train_station", "taxi_stand",
    
    # Entertainment
    "movie_theater", "night_club", "casino", "spa", "gym",
]
```

---

## Phase 3: Chiến lược Thu thập Grid-based

### Grid System (chia nhỏ thành phố):
```python
GRID_SIZE_KM = 2  # Mỗi ô 2km x 2km
SEARCH_RADIUS = 1000  # 1km mỗi điểm

class GridCollector:
    def create_grid(self, city_center, radius_km=10):
        """
        Tạo lưới các điểm thu thập trong bán kính 10km
        Grid 2km = ~25 điểm mỗi city
        """
        points = []
        steps = int(radius_km / (GRID_SIZE_KM / 2))
        
        for i in range(-steps, steps + 1):
            for j in range(-steps, steps + 1):
                lat = city_center["lat"] + (i * 0.018)  # ~2km
                lng = city_center["lng"] + (j * 0.018)  # ~2km
                points.append({"lat": lat, "lng": lng})
        
        return points
```

### Estimate:
- 38 cities × 25 grid points = **950 locations**
- 15 categories × 20 results = **300 results/category**
- **950 × 300 = ~285,000 potential POIs**

---

## Phase 4: Rate Limiting Strategy

### Google Places (RapidAPI):
```python
class RateLimitManager:
    def __init__(self, keys):
        self.keys = keys
        self.key_usage = {k: {"count": 0, "reset_time": time.time()} for k in keys}
        self.max_per_key = 100  # requests per minute
        
    def get_available_key(self):
        """Luân phiên key dựa trên usage"""
        now = time.time()
        for key, usage in self.key_usage.items():
            if now - usage["reset_time"] > 60:
                usage["count"] = 0
                usage["reset_time"] = now
            
            if usage["count"] < self.max_per_key:
                usage["count"] += 1
                return key
        
        # All keys exhausted, wait
        time.sleep(10)
        return self.get_available_key()
```

### Tính toán:
- 18 keys × 100 req/min = **1,800 req/min**
- 285,000 POIs ÷ 1,800 = **~158 minutes** (2.6 hours)

---

## Phase 5: Distributed Collection Architecture

### 1. Queue-based System:
```python
from celery import Celery
import redis

# Redis as message broker
app = Celery('data_collection', broker='redis://localhost:6379')

@app.task
def collect_city_category(city, category, grid_point):
    """Task để thu thập cho 1 city + category + grid point"""
    collector = GooglePlacesCollector()
    return collector.collect(
        lat=grid_point["lat"],
        lng=grid_point["lng"],
        category=category
    )

# Schedule tasks
for city in CITIES:
    for category in CATEGORIES:
        grid = create_grid(city)
        for point in grid:
            collect_city_category.delay(city, category, point)
```

### 2. Database Structure for Scale:
```python
# bronze_records collection schema
{
    "poi_id": "google_xxx",
    "name": "Place Name",
    "category": "restaurant",
    "city": "hanoi",
    "location": {"lat": 21.0, "lng": 105.0},
    "_source": "google_real",
    "_grid_point": {"i": 5, "j": 3},  # Grid position
    "_collected_at": "2026-05-10T00:00:00",
    "_batch": "batch_001",
    "_collection_job_id": "job_20260510_001"
}

# collection_jobs collection
{
    "job_id": "job_20260510_001",
    "status": "running",
    "cities": ["hanoi", "hcm", ...],
    "categories": ["restaurant", "cafe", ...],
    "total_tasks": 10000,
    "completed_tasks": 4500,
    "failed_tasks": 23,
    "started_at": "2026-05-10T00:00:00",
    "estimated_completion": "2026-05-10T03:00:00"
}
```

---

## Phase 6: Implementation Script

```python
#!/usr/bin/env python
"""
Mass Collection System - 10K+ POIs
=================================
Thu thập dữ liệu quy mô lớn với quản lý job.
"""

import os
import sys
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
import requests

class MassCollector:
    def __init__(self):
        self.mongo = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.mongo.smart_travel
        self.keys = self._load_keys()
        self.key_index = 0
        self.job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def _load_keys(self):
        keys_str = os.getenv("RAPID_API_KEYS", "")
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    
    def get_key(self):
        key = self.keys[self.key_index % len(self.keys)]
        self.key_index += 1
        return key
    
    def collect_single(self, city, category, lat, lng, radius=2000):
        """Collect for single point with retry."""
        url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
        
        for attempt in range(3):
            try:
                headers = {
                    "x-rapidapi-key": self.get_key(),
                    "x-rapidapi-host": "google-map-places.p.rapidapi.com"
                }
                
                params = {
                    "location": f"{lat},{lng}",
                    "radius": str(radius),
                    "type": category,
                    "language": "vi"
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    records = []
                    for place in results:
                        record = {
                            "poi_id": f"google_{place.get('place_id', '')}",
                            "name": place.get("name", ""),
                            "category": category,
                            "city": city,
                            "location": {
                                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                                "lng": place.get("geometry", {}).get("location", {}).get("lng")
                            },
                            "rating": place.get("rating"),
                            "_source": "google_real",
                            "_job_id": self.job_id,
                            "_grid_center": {"lat": lat, "lng": lng},
                            "_collected_at": datetime.now().isoformat()
                        }
                        records.append(record)
                    
                    return {"success": True, "count": len(records), "records": records}
                    
                elif response.status_code == 429:
                    time.sleep(5)
                    continue
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
            except Exception as e:
                if attempt == 2:
                    return {"success": False, "error": str(e)}
                time.sleep(2)
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def run_collection(self, cities, categories, grid_points_per_city=25):
        """Run mass collection."""
        total_tasks = len(cities) * len(categories) * grid_points_per_city
        completed = 0
        failed = 0
        total_records = 0
        
        print(f"🚀 Starting collection job: {self.job_id}")
        print(f"📊 Total tasks: {total_tasks}")
        print(f"🏙️ Cities: {len(cities)}")
        print(f"📁 Categories: {len(categories)}")
        print(f"🔍 Grid points per city: {grid_points_per_city}")
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for city_name, city_data in cities.items():
                # Create grid
                grid = self.create_grid(city_data, radius_km=10)
                
                for category in categories:
                    for point in grid[:grid_points_per_city]:
                        future = executor.submit(
                            self.collect_single,
                            city_name, category,
                            point["lat"], point["lng"]
                        )
                        futures.append((future, city_name, category))
            
            # Process results
            for future, city, category in futures:
                try:
                    result = future.result(timeout=60)
                    
                    if result["success"]:
                        if result["records"]:
                            self.db.bronze_records.insert_many(result["records"])
                            total_records += result["count"]
                        completed += 1
                    else:
                        failed += 1
                    
                    # Progress report
                    if (completed + failed) % 50 == 0:
                        print(f"📈 Progress: {completed}/{total_tasks} "
                              f"({completed/total_tasks*100:.1f}%) | "
                              f"Records: {total_records}")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed += 1
        
        # Final report
        print(f"\n✅ Collection Complete!")
        print(f"   Total: {total_records} POIs")
        print(f"   Completed tasks: {completed}")
        print(f"   Failed tasks: {failed}")
        
        return total_records
    
    def create_grid(self, city_data, radius_km=10):
        """Create grid of collection points."""
        center_lat = city_data["lat"]
        center_lng = city_data["lng"]
        
        points = []
        step_km = 2  # 2km grid
        steps = int(radius_km / step_km)
        
        # ~0.018 degrees = 2km
        lat_step = 0.018
        lng_step = 0.018
        
        for i in range(-steps, steps + 1):
            for j in range(-steps, steps + 1):
                lat = center_lat + (i * lat_step)
                lng = center_lng + (j * lng_step)
                points.append({"lat": lat, "lng": lng, "i": i, "j": j})
        
        return points


if __name__ == "__main__":
    # Load city configs
    cities = {
        "hanoi": {"lat": 21.0278, "lng": 105.8342},
        "hcm": {"lat": 10.8231, "lng": 106.6297},
        "danang": {"lat": 16.0544, "lng": 108.2022},
        "haiphong": {"lat": 20.8449, "lng": 106.6881},
        "cantho": {"lat": 10.0452, "lng": 105.7469},
        "nhatrang": {"lat": 12.2388, "lng": 109.1967},
        "dalat": {"lat": 11.9404, "lng": 108.4583},
        "hue": {"lat": 16.4637, "lng": 107.5909},
    }
    
    categories = [
        "restaurant", "cafe", "hotel", "tourist_attraction",
        "shopping_mall", "supermarket", "bar", "spa", "gym"
    ]
    
    collector = MassCollector()
    total = collector.run_collection(cities, categories, grid_points_per_city=9)
    
    print(f"\n🎉 Total collected: {total} POIs")
```

---

## Phase 7: Database Optimization

### MongoDB Indexes:
```javascript
db.bronze_records.createIndex({"poi_id": 1}, {unique: true})
db.bronze_records.createIndex({"city": 1, "category": 1})
db.bronze_records.createIndex({"location": "2dsphere"})
db.bronze_records.createIndex({"_source": 1})
db.bronze_records.createIndex({"_collected_at": -1})
```

### Sharding (nếu > 100K records):
```javascript
sh.shardCollection("smart_travel.bronze_records", {"city": 1})
```

---

## Phase 8: Monitoring & Dashboard

### Progress Tracking:
```python
class CollectionMonitor:
    def get_stats(self):
        return {
            "total_bronze": self.db.bronze_records.count(),
            "by_city": self.db.bronze_records.aggregate([
                {"$group": {"_id": "$city", "count": {"$sum": 1}}}
            ]),
            "by_category": self.db.bronze_records.aggregate([
                {"$group": {"_id": "$category", "count": {"$sum": 1}}}
            ]),
            "today": self.db.bronze_records.count({
                "_collected_at": {"$gte": datetime.now().replace(hour=0, minute=0)}
            })
        }
```

---

## Phase 9: Automation Scheduling

### Cron Job (Linux/Mac):
```bash
# Collect every 6 hours
0 */6 * * * cd /path/to/project && python scripts/mass_collection.py >> logs/collection.log 2>&1

# Daily report at 8am
0 8 * * * cd /path/to/project && python scripts/generate_report.py
```

### Windows Task Scheduler:
```powershell
# PowerShell script to schedule
gschtasks /create /tn "DataCollection" /tr "python scripts/mass_collection.py" /sc hourly /mo 6
```

---

## Phase 10: Estimated Timeline

| Phase | Description | Est. POIs | Time |
|-------|-------------|-----------|------|
| 1 | 8 Tier-1 cities × 9 categories × 9 grid | ~1,600 | 30 min |
| 2 | +15 Tier-2 cities | ~4,000 | 1 hour |
| 3 | +15 Tier-3 cities | ~6,000 | 1.5 hours |
| 4 | Increase grid density | ~10,000 | 2.5 hours |
| 5 | Full coverage (38 cities) | ~20,000 | 5 hours |

---

## Next Steps:

1. **Chạy Phase 1** (8 cities) → Target: 1,600 POIs
2. **Thêm Phase 2** (15 cities) → Target: 4,000 POIs
3. **Thêm Phase 3** (15 cities) → Target: 6,000 POIs
4. **Tăng grid density** → Target: 10,000+ POIs

**Tôi đã sẵn sàng implement Phase 1 (8 cities) ngay bây giờ!** 🚀
