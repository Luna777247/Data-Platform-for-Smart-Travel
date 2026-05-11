# ⚠️ DEPRECATED - MinIO + MongoDB Pipeline Architecture
======================================

> **⚠️ LƯU Ý: Tài liệu này đã LỖI THỜI**
> 
> Kiến trúc hiện tại đã được **đơn giản hóa** sang **MongoDB-only** (bỏ MinIO).
> 
> Vui lòng xem tài liệu mới: **[MONGODB_PIPELINE.md](./MONGODB_PIPELINE.md)**
> 
> Tài liệu này được giữ lại để tham khảo lịch sử.

---

# MinIO + MongoDB Pipeline Architecture (Deprecated)
======================================

## Tổng quan

Kiến trúc mới với **Bronze trong MinIO**, **Silver/Gold trong MongoDB**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  Google Places API    OSM Overpass API                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BRONZE LAYER (MinIO)                        │
│  Bucket: smart-travel-bronze                                      │
│  Structure: bronze/{source}/{city}/{category}/{file}.json       │
│                                                                  │
│  Ví dụ:                                                          │
│  bronze/google/hanoi/restaurant/20260510_143022_a1b2c3.json    │
│  bronze/osm/hochiminh/hotel/20260510_143045_d4e5f6.json        │
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

### Bronze (MinIO) - Raw JSON

```json
{
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
    "priceLevel": "PRICE_LEVEL_MODERATE",
    ...
  }
}
```

### Silver (MongoDB) - Cleaned

```javascript
{
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
  "_bronze_path": "bronze/google/hanoi/restaurant/...",
  "_collected_at": "2026-04-30T15:18:37",
  "_transformed_at": "2026-05-10T...",
  "layer": "silver"
}
```

### Gold (MongoDB) - Enriched

```javascript
{
  "poi_id": "gold_ChIJ...",
  "place_id": "ChIJ...",
  ... // All Silver fields
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

### 1. Cài đặt MinIO

#### Option A: Docker (Recommended)

```bash
# docker-compose.yml
docker-compose up -d minio
```

Hoặc standalone:

```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin123 \
  -v minio_data:/data \
  quay.io/minio/minio server /data --console-address ":9001"
```

#### Option B: Local Binary

```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/windows-amd64/minio.exe

# Start server
minio.exe server D:\minio-data --console-address :9001
```

### 2. Cấu hình Environment

```bash
# .env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
```

### 3. Cài đặt Dependencies

```bash
pip install minio
```

## API Endpoints

### Bronze Layer (MinIO)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/bronze/collect` | POST | Collect to MinIO |
| `/api/v1/pipeline/bronze/mass-collect` | POST | Mass collection |
| `/api/v1/pipeline/bronze/list` | GET | List objects |
| `/api/v1/pipeline/bronze/stats` | GET | MinIO stats |

### Transform Pipeline

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/bronze-to-silver` | POST | Transform to MongoDB |
| `/api/v1/pipeline/silver-to-gold` | POST | Enrich to Gold |
| `/api/v1/pipeline/run-full-pipeline` | POST | Bronze → Silver → Gold |

### Stats

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/pipeline/layers/stats` | GET | All layers stats |

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
  "saved_to_minio": 20,
  "paths": [
    "bronze/google/hanoi/restaurant/20260510_143022_a1b2c3.json",
    ...
  ],
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

### 4. Transform Silver → Gold

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/silver-to-gold?\
min_rating=3.5" \
  -H "Authorization: Bearer <token>"
```

### 5. Full Pipeline

```bash
curl -X POST "http://localhost:8000/api/v1/pipeline/run-full-pipeline?\
cities=hanoi&cities=hcm&\
categories=restaurant&categories=cafe&\
grid_points=4" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "status": "complete",
  "pipeline": {
    "bronze": {"saved_to_minio": 160},
    "silver": {"transformed": 150},
    "gold": {"enriched": 145}
  }
}
```

### 6. Check Stats

```bash
curl "http://localhost:8000/api/v1/pipeline/layers/stats" \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "layers": {
    "bronze": {
      "storage": "minio",
      "total_objects": 4452,
      "total_size_mb": 156.42,
      "by_source": {"google": 3300, "osm": 1152},
      "by_city": {"hanoi": 1690, "nhatrang": 934, ...}
    },
    "silver": {
      "storage": "mongodb",
      "total_documents": 3200
    },
    "gold": {
      "storage": "mongodb", 
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
4. Save to MinIO (bronze/google/{city}/{category}/...)
   ↓
5. [Optional] Transform Bronze → Silver
   - Read from MinIO
   - Clean & normalize
   - Save to MongoDB (silver_pois)
   ↓
6. [Optional] Transform Silver → Gold
   - Read from MongoDB
   - Enrich & score
   - Save to MongoDB (gold_master_pois)
```

## So sánh với Storage cũ

| Feature | Storage (Files) | MinIO (Object Storage) |
|---------|-----------------|--------------------------|
| Access | Local filesystem | HTTP API |
| Query | ❌ Khó | ✅ Dễ (list objects) |
| Scale | Limited by disk | Unlimited (distributed) |
| Metadata | File attrs | Custom metadata |
| Backup | Copy files | Replication/Mirroring |
| Cost | Disk only | Disk + network |

## Migration từ Storage hiện tại

```python
# migrate_to_minio.py
import os
import json
from src.core.minio_client import get_bronze_storage

storage = get_bronze_storage()

# Migrate existing files
for root, dirs, files in os.walk('storage/bronze'):
    for f in files:
        if f.endswith('.json'):
            filepath = os.path.join(root, f)
            with open(filepath) as fp:
                data = json.load(fp)
            
            # Parse path: storage/bronze/{source}/{city}/{file}
            parts = filepath.replace('storage/bronze/', '').split('/')
            source = parts[0]
            city = parts[1]
            category = data.get('category', 'general')
            
            # Save to MinIO
            storage.save_bronze_record(
                data=data,
                city=city,
                source=source,
                category=category,
                filename=f
            )
            print(f"Migrated: {filepath}")
```

## Troubleshooting

### MinIO không kết nối được

```bash
# Check if MinIO is running
curl http://localhost:9000/minio/health/live

# Check logs
docker logs minio

# Verify credentials
mc alias set local http://localhost:9000 minioadmin minioadmin123
mc ls local
```

### Bucket không tồn tại

```python
# Auto-created trong code, hoặc tạo thủ công:
from src.core.minio_client import get_bronze_storage
storage = get_bronze_storage()
# Bucket sẽ được tạo tự động khi khởi tạo
```

### Permission denied

```bash
# Ensure correct credentials in .env
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
```

## Kết luận

Kiến trúc mới cung cấp:
- ✅ Bronze trong MinIO (scalable object storage)
- ✅ Silver/Gold trong MongoDB (queryable database)
- ✅ Schema giữ nguyên như storage hiện tại
- ✅ Pipeline API để transform giữa các layers
- ✅ Stats endpoint để monitoring
