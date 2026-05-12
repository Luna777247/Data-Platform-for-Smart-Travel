# MongoDB Pipeline Architecture
================================

## Tổng quan

Kiến trúc **3-layers trong MongoDB duy nhất** - đơn giản và nhất quán:

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  Google Places API    OSM Overpass API                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BRONZE LAYER (MongoDB)                      │
│  Collection: bronze_records                                      │
│  - Raw data từ APIs                                              │
│  - Giữ nguyên format gốc                                         │
│  - Metadata: _source, _layer, city, category                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Transform
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER LAYER (MongoDB)                       │
│  Collection: silver_pois                                         │
│  - Cleaned & normalized                                        │
│  - Standardized schema                                         │
│  - Deduplicated                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Enrich
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GOLD LAYER (MongoDB)                        │
│  Collection: gold_master_pois                                    │
│  - Quality scoring                                             │
│  - Production-ready                                            │
│  - Master data                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Schema Chi tiết

### Bronze (MongoDB) - Raw Data

```javascript
{
  "_id": ObjectId("..."),
  "u_key": "05b30c17164df56e",
  "original_osm_name": "Quán Quốc Trung",
  "city": "hanoi",
  "category": "restaurant",
  "harvested_at": "2026-04-30T15:18:37.324532",
  "search_params": {
    "lat": 21.0278,
    "lng": 105.8342,
    "radius": 2000,
    "type": "restaurant"
  },
  "google_raw": {
    "id": "ChIJ...",
    "displayName": {"text": "Place Name"},
    "location": {"latitude": 21.0, "longitude": 105.8},
    "formattedAddress": "123 Street, Hanoi",
    "rating": 4.5,
    "userRatingCount": 1234,
    "types": ["restaurant", "food"],
    "photos": [...],
    "reviews": [...],
    "priceLevel": "PRICE_LEVEL_MODERATE"
  },
  "_source": "google",
  "_layer": "bronze"
}
```

### Silver (MongoDB) - Cleaned

```javascript
{
  "_id": ObjectId("..."),
  "place_id": "ChIJ...",
  "u_key": "05b30c17164df56e",
  "name": "Place Name",
  "city": "hanoi",
  "location": {
    "lat": 21.0,
    "lng": 105.8
  },
  "address": "123 Street, Hanoi",
  "category": "restaurant",
  "types": ["restaurant", "food"],
  "rating": 4.5,
  "user_rating_count": 1234,
  "price_level": 2,
  "photos": ["url1", "url2"],
  "image_url": "main_url",
  "_source": "google_places",
  "_bronze_id": "...",
  "_collected_at": "2026-04-30T15:18:37",
  "_transformed_at": "2026-05-10T...",
  "layer": "silver"
}
```

### Gold (MongoDB) - Enriched

```javascript
{
  "_id": ObjectId("..."),
  "poi_id": "gold_ChIJ...",
  "place_id": "ChIJ...",
  // ... All Silver fields
  "layer": "gold",
  "quality_score": 0.85,
  "data_completeness": 0.92,
  "subcategory": "vietnamese_restaurant",
  "review_count": 1234,
  "is_active": true,
  "verified": false,
  "created_at": "2026-05-10T...",
  "updated_at": "2026-05-10T..."
}
```

## Setup

### 1. Cấu hình MongoDB

```bash
# .env
MONGODB_URI=mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin
DB_NAME=smart_travel
```

### 2. Tạo Indexes

```python
# scripts/create_indexes.py
from pymongo import MongoClient, ASCENDING, TEXT

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Bronze indexes
db.bronze_records.create_index([("city", ASCENDING)])
db.bronze_records.create_index([("category", ASCENDING)])
db.bronze_records.create_index([("_layer", ASCENDING)])
db.bronze_records.create_index([("u_key", ASCENDING)], unique=True)

# Silver indexes
db.silver_pois.create_index([("place_id", ASCENDING), ("city", ASCENDING)])
db.silver_pois.create_index([("location", "2dsphere")])
db.silver_pois.create_index([("category", ASCENDING)])

# Gold indexes
db.gold_master_pois.create_index([("poi_id", ASCENDING)], unique=True)
db.gold_master_pois.create_index([("quality_score", ASCENDING)])

print("✅ Indexes created")
```

## API Endpoints

### Bronze Layer (MongoDB)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/bronze/collect` | POST | Collect to MongoDB |
| `/api/v1/pipeline/bronze/mass-collect` | POST | Mass collection |
| `/api/v1/pipeline/bronze/list` | GET | List records |
| `/api/v1/pipeline/bronze/stats` | GET | MongoDB stats |

### Transform Pipeline

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/bronze-to-silver` | POST | Transform Bronze → Silver |
| `/api/v1/pipeline/silver-to-gold` | POST | Transform Silver → Gold |
| `/api/v1/pipeline/run-full-pipeline` | POST | Full pipeline |

### Query API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pois` | GET | Query POIs |
| `/api/v1/pois/{poi_id}` | GET | Get single POI |

## Usage Examples

### 1. Collect Bronze Data

```bash
# Single city + category
curl -X POST "http://localhost:8000/api/v1/pipeline/bronze/collect?\
city=hanoi&category=restaurant&lat=21.0278&lng=105.8342&radius=2000" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "status": "success",
  "saved_to_mongodb": 20,
  "poi_ids": ["...", "..."],
  "city": "hanoi",
  "category": "restaurant"
}
```

### 2. Mass Collection

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/bronze/mass-collect?\
cities=hanoi&cities=hcm&\
categories=restaurant&categories=cafe&\
grid_points=4" \
  -H "Authorization: Bearer <token>"
```

### 3. Transform Bronze → Silver

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/bronze-to-silver?\
city=hanoi&batch_size=100" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "status": "success",
  "transformed": 100,
  "errors": 0,
  "from_layer": "bronze",
  "to_layer": "silver"
}
```

### 4. Query POIs

```bash
# Query by city and category
curl "http://localhost:8000/api/v1/pois?city=hanoi&category=restaurant&limit=10"

# Query nearby
curl "http://localhost:8000/api/v1/pois/nearby?lat=21.0278&lng=105.8342&radius=1000"
```

### 5. Check Stats

```bash
curl "http://localhost:8000/api/v1/pipeline/layers/stats"
```

Response:
```json
{
  "layers": {
    "bronze": {
      "storage": "mongodb",
      "collection": "bronze_records",
      "total_documents": 4452,
      "by_city": {"hanoi": 1690, "nhatrang": 934}
    },
    "silver": {
      "storage": "mongodb",
      "collection": "silver_pois",
      "total_documents": 3200
    },
    "gold": {
      "storage": "mongodb",
      "collection": "gold_master_pois",
      "total_documents": 3100
    }
  }
}
```

## Data Flow

```
1. COLLECT (API Request)
   ↓
2. Google Places API
   ↓
3. Format Bronze Record
   ↓
4. Save to MongoDB (bronze_records)
   ↓
5. [Optional] Transform Bronze → Silver
   - Read from MongoDB
   - Clean & normalize
   - Save to MongoDB (silver_pois)
   ↓
6. [Optional] Transform Silver → Gold
   - Read from MongoDB
   - Enrich & score
   - Save to MongoDB (gold_master_pois)
```

## Truy cập dữ liệu trực tiếp

### Python

```python
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Bronze
bronze_docs = list(db.bronze_records.find({'city': 'hanoi'}).limit(10))

# Silver
silver_docs = list(db.silver_pois.find({'category': 'restaurant', 'rating': {'$gte': 4}}))

# Gold
gold_docs = list(db.gold_master_pois.find({'quality_score': {'$gte': 0.8}}))
```

### MongoDB Shell

```javascript
// Bronze
use smart_travel
db.bronze_records.find({city: "hanoi", category: "restaurant"}).limit(5)

// Silver - with rating
db.silver_pois.find({rating: {$gte: 4.5}}).sort({rating: -1}).limit(10)

// Gold - high quality
db.gold_master_pois.find({quality_score: {$gte: 0.9}})

// Count by city
db.bronze_records.aggregate([
  {$group: {_id: "$city", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

## Export dữ liệu

```python
# export_mongodb.py
from pymongo import MongoClient
import json

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Export từng layer
layers = {
    'bronze': 'bronze_records',
    'silver': 'silver_pois',
    'gold_master': 'gold_master_pois'
}

for layer, collection in layers.items():
    data = list(db[collection].find({}, {'_id': 0}))
    filename = f'pois_{layer}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {layer}: {len(data)} records → {filename}")
```

## So sánh với kiến trúc cũ

| Feature | Kiến trúc cũ (MinIO + MongoDB) | Kiến trúc mới (MongoDB only) |
|---------|-------------------------------|------------------------------|
| Nơi lưu Bronze | MinIO (object storage) | MongoDB (collection) |
| Nơi lưu Silver/Gold | MongoDB | MongoDB (giữ nguyên) |
| Query Bronze | ❌ Khó (cần list objects) | ✅ Dễ (MongoDB query) |
| Backup | 2 nơi (MinIO + MongoDB) | 1 nơi (MongoDB only) |
| Consistency | ⚠️ Cần đồng bộ | ✅ Tự động |
| Complexity | Cao (2 systems) | Thấp (1 system) |

## Kết luận

Kiến trúc mới cung cấp:
- ✅ **Simplicity**: Chỉ MongoDB, không cần MinIO
- ✅ **Consistency**: Tất cả layers ở cùng 1 database
- ✅ **Easy Query**: MongoDB query cho tất cả layers
- ✅ **Easy Backup**: Backup 1 nơi
- ✅ **Faster Transform**: Không cần chuyển đổi giữa storage systems

## Migration từ Local Files (nếu cần)

Nếu bạn đã có dữ liệu local files từ kiến trúc cũ:

```python
# migrate_from_files.py
from pymongo import MongoClient
import os, json

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Migrate from local files
for root, dirs, files in os.walk('storage/bronze'):
    for file in files:
        if file.endswith(".json"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                db.bronze_records.insert_one(data)
                print(f"Migrated: {filepath}")

print("✅ Migration complete")
