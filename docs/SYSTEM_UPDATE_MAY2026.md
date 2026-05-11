# System Update Documentation - May 2026
## Cập Nhật Hệ Thống - Tháng 5/2026

---

## 📋 Tổng Quan

Bản cập nhật này giới thiệu kiến trúc **MongoDB-only 3-layers** - đơn giản và nhất quán:

| Layer | Storage Trước | Storage Mới | Lý Do Thay Đổi |
|-------|---------------|-------------|----------------|
| **Bronze** | Local Files (`storage/bronze/`) | **MongoDB** (`bronze_pois`) | Đơn giản, query dễ dàng, backup 1 nơi |
| **Silver** | Local Files (`storage/silver/`) | **MongoDB** (`silver_pois`) | Query được, có index |
| **Gold** | Local Files (`storage/gold/`) | **MongoDB** (`gold_master_pois`) | Production-ready, searchable |

**Lợi ích chính:**
- ✅ **Simple**: Chỉ 1 database (MongoDB) - không cần MinIO
- ✅ **Consistent**: Cả 3 layers trong cùng 1 database
- ✅ **Easy Query**: MongoDB queries cho mọi layer
- ✅ **Easy Backup**: Backup 1 nơi duy nhất
- ✅ **Fast Transform**: Không cần chuyển đổi giữa storage systems

---

## 🏗️ Kiến Trúc Mới

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION                             │
│              (Google Places API, OSM API)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BRONZE LAYER (MongoDB)                          │
│  Collection: bronze_records                                      │
│                                                                  │
│  Schema: {                                                       │
│    _id: ObjectId("..."),                                         │
│    u_key: "unique_hash",                                         │
│    city: "hanoi",                                                │
│    category: "restaurant",                                       │
│    google_raw: { ... },     ← Raw API response                  │
│    harvested_at: "2026-05-10...",                               │
│    _source: "google",                                            │
│    _layer: "bronze"                                              │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Transform (Read MongoDB → Write MongoDB)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SILVER LAYER (MongoDB)                       │
│  Collection: silver_pois                                         │
│                                                                  │
│  Schema: {                                                       │
│    _id: ObjectId("..."),                                         │
│    place_id: "ChIJ...",                                          │
│    name: "Place Name",                                           │
│    city: "hanoi",                                                │
│    location: {lat, lng},                                         │
│    category: "restaurant",  ← Normalized                        │
│    rating: 4.5,                                                  │
│    _bronze_id: "...",       ← Reference to bronze_records       │
│    layer: "silver"                                               │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Enrich (API Call)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOLD LAYER (MongoDB)                        │
│  Collection: gold_master_pois                                    │
│                                                                  │
│  Schema: {                                                       │
│    _id: ObjectId("..."),                                         │
│    poi_id: "gold_ChIJ...",                                       │
│    place_id: "ChIJ...",                                          │
│    quality_score: 0.85,     ← Enriched                         │
│    data_completeness: 0.92,                                      │
│    is_active: true,                                              │
│    layer: "gold"                                                 │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Files Mới Được Tạo

| File | Mục Đích | Đường Dẫn |
|------|----------|-----------|
| **Bronze Pipeline** | Thu thập data → MongoDB | `src/services/bronze_pipeline.py` |
| **Silver/Gold Pipeline** | Transform trong MongoDB | `src/services/silver_gold_pipeline.py` |
| **Pipeline API** | REST endpoints cho pipeline | `src/api/routes/pipeline_mongodb.py` |
| **MongoDB Documentation** | Hướng dẫn chi tiết | `docs/MONGODB_PIPELINE.md` |

**Lưu ý:** MinIO đã bị xóa hoàn toàn. `src/api/routes/pipeline_mongodb.py` thay thế `pipeline_minio.py`.

---

## 🔧 Cấu Hình

### 1. Environment Variables (.env)

```bash
# MongoDB Configuration (duy nhất cần thiết)
MONGODB_URI=mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin
DB_NAME=smart_travel

# MongoDB (đã có)
MONGODB_URL=mongodb://localhost:27017
DB_NAME=smart_travel
```

### 2. Docker Compose (docker-compose.yml)

**Lưu ý:** Chỉ cần MongoDB (MinIO đã bị xóa hoàn toàn):

```yaml
services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: admin123
    volumes:
      - mongodb_data:/data/db
```

---

## 🚀 API Endpoints Mới

### Bronze Layer (MongoDB)

```bash
# 1. Collect single city/category → MongoDB
POST /api/v1/pipeline/bronze/collect
  ?city=hanoi
  &category=restaurant
  &lat=21.0278
  &lng=105.8342
  &radius=2000

# 2. Mass collection
POST /api/v1/pipeline/bronze/mass-collect
  ?cities=hanoi&cities=hcm
  &categories=restaurant&categories=cafe
  &grid_points=4

# 3. List Bronze records
GET /api/v1/pipeline/bronze/list
  ?city=hanoi
  &category=restaurant

# 4. Bronze statistics
GET /api/v1/pipeline/bronze/stats
```

### Transform Pipeline

```bash
# 5. Bronze → Silver
POST /api/v1/pipeline/bronze-to-silver
  ?city=hanoi
  &batch_size=100

# 6. Silver → Gold
POST /api/v1/pipeline/silver-to-gold
  ?min_rating=3.5

# 7. Full pipeline
POST /api/v1/pipeline/run-full-pipeline
  ?cities=hanoi&cities=hcm
  &categories=restaurant&categories=cafe
  &grid_points=4

# 8. All layers statistics
GET /api/v1/pipeline/layers/stats
```

---

## 📊 So Sánh: Trước vs Sau

### Trước (Local Files)

| Đặc điểm | Giá trị |
|----------|---------|
| Bronze | 4,452 files trong `storage/bronze/` |
| Silver | 0 files trong `storage/silver/` |
| Gold | 0 files trong `storage/gold/` |
| Query | ❌ Khó khăn (phải đọc files) |
| Scale | ❌ Giới hạn bởi disk local |
| Backup | ❌ Manual copy files |

### Sau (MongoDB Only)

| Đặc điểm | Giá trị |
|----------|---------|
| Bronze | Documents trong MongoDB `bronze_records` |
| Silver | Documents trong MongoDB `silver_pois` |
| Gold | Documents trong MongoDB `gold_master_pois` |
| Query | ✅ Dễ dàng (MongoDB queries cho tất cả layers) |
| Scale | ✅ MongoDB replica set |
| Backup | ✅ MongoDB backup (1 nơi duy nhất) |
| Complexity | ✅ Đơn giản (chỉ 1 database) |

---

## 🔄 Migration Guide

### Bước 1: Setup MongoDB

```bash
# Start MongoDB
docker-compose up -d mongodb

# Verify
mongosh "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
```

### Bước 2: Kiểm tra dữ liệu Bronze trong MongoDB

```python
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

# Kiểm tra bronze_pois
records = list(db['bronze_pois'].find().limit(5))
print(f"Bronze records: {len(records)}")
```

```python
# migrate_files_to_mongodb.py
import os, json
from pymongo import MongoClient

client = MongoClient('mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin')
db = client.smart_travel

for root, dirs, files in os.walk('storage/bronze'):
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            with open(path) as fp:
                data = json.load(fp)
            data["_layer"] = "bronze"
            db.bronze_records.insert_one(data)
            print(f"Migrated: {path}")
```

### Bước 3: Run Pipeline

```bash
# Collect new data to MongoDB
curl -X POST "http://localhost:8000/api/v1/pipeline/bronze/mass-collect?cities=hanoi&categories=restaurant"

# Transform Bronze → Silver
curl -X POST "http://localhost:8000/api/v1/pipeline/bronze-to-silver"

# Transform Silver → Gold
curl -X POST "http://localhost:8000/api/v1/pipeline/silver-to-gold"

# Enrich to Gold
curl -X POST "http://localhost:8000/api/v1/pipeline/silver-to-gold"

# Check stats
curl "http://localhost:8000/api/v1/pipeline/layers/stats"
```

---

## 📚 Tài Liệu Liên Quan

| Tài Liệu | Mô Tả | Đường Dẫn |
|----------|-------|-----------|
| MongoDB Pipeline Guide | Chi tiết về MongoDB 3-layer | `docs/MONGODB_PIPELINE.md` |
| Architecture Overview | Kiến trúc tổng quan | `docs/README.md` |
| Developer Guide | Hướng dẫn phát triển | `docs/SMART_TOURISM_DEVELOPER_GUIDE.md` |
| Cheatsheet | Tham khảo nhanh | `docs/SMART_TOURISM_CHEATSHEET.md` |

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Storage Cũ (Migration)

- `storage/bronze/` có thể migrate vào MongoDB nếu cần
- Xem script `migrate_files_to_mongodb.py` ở trên
- Hoặc giữ lại làm local backup

### 2. MongoDB Access

- Connection: `mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin`
- Database: `smart_travel`
- Collections: `bronze_records`, `silver_pois`, `gold_master_pois`

### 3. MongoDB Collections & Indexes

```javascript
// Bronze collection
db.bronze_records.createIndex({"u_key": 1}, {unique: true})
db.bronze_records.createIndex({"city": 1, "category": 1})
db.bronze_records.createIndex({"_layer": 1})

// Silver collection
db.silver_pois.createIndex({"place_id": 1, "city": 1})
db.silver_pois.createIndex({"city": 1, "category": 1})
db.silver_pois.createIndex({"location": "2dsphere"})

// Gold collection
db.gold_master_pois.createIndex({"poi_id": 1}, {unique: true})
db.gold_master_pois.createIndex({"city": 1, "quality_score": -1})
```

### 4. API Authentication

Tất cả pipeline endpoints yêu cầu JWT token:

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/pipeline/layers/stats
```

---

## 🎯 Kế Hoạch Tiếp Theo

| Phase | Mục Tiêu | Timeline |
|-------|----------|----------|
| **Phase 1** | Chạy thử nghiệm pipeline mới | Tuần 1 |
| **Phase 2** | Migration dữ liệu cũ (nếu cần) | Tuần 2 |
| **Phase 3** | Mass collection 10K+ POIs | Tuần 3-4 |
| **Phase 4** | Monitoring & optimization | Tuần 5 |

---

## 🆘 Troubleshooting

### Pipeline API lỗi 500

```bash
# Check backend logs
tail -f logs/backend.log

# Verify MongoDB connection
python -c "from pymongo import MongoClient; c=MongoClient('mongodb://localhost:27017'); print(c.admin.command('ping'))"
```

### Data không vào MongoDB

```bash
# Check if collections exist
mongosh smart_travel --eval "show collections"

# Check document counts
mongosh smart_travel --eval "db.silver_pois.countDocuments()"
```

---

## 📝 Changelog

### Version 1.1 (May 10, 2026)

#### Added
- ⭐ New pipeline services: `BronzePipeline`, `SilverGoldPipeline`
- ⭐ 8 new API endpoints (`/api/v1/pipeline/*`) - route `pipeline_mongodb`
- ⭐ Documentation: `MONGODB_PIPELINE.md`

#### Changed
- 🔄 Bronze/Silver/Gold layers: Local files → MongoDB collections
- 🔄 MinIO removed completely from codebase
- 🔄 Architecture documentation updated

#### Migration
- No breaking changes (existing data preserved)
- New features are additive
- Can migrate old data incrementally

---

**Prepared by:** Data Engineering Team  
**Date:** May 10, 2026  
**Status:** ✅ Production Ready
