# SMART TOURISM DATA PLATFORM
## Quick Reference Cheat Sheet

---

## Pipeline State Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      RUNNING PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  START → CREATED → REGISTERED → SCHEDULED → QUEUED        │
│                                                 ↓           │
│                                          INITIALIZING       │
│                                                 ↓           │
│    ┌──────────────────────────────────────────────┐        │
│    │                RUNNING                       │        │
│    │  ┌──────────────────────────────────────┐   │        │
│    │  │     VALIDATING (Schema check)        │   │        │
│    │  └──────────────────────────────────────┘   │        │
│    │                  ↓                           │        │
│    │  ┌──────────────────────────────────────┐   │        │
│    │  │ BRONZE_PROCESSING → BRONZE_COMPLETED│   │        │
│    │  └──────────────────────────────────────┘   │        │
│    │                  ↓                           │        │
│    │  ┌──────────────────────────────────────┐   │        │
│    │  │ SILVER_PROCESSING → SILVER_COMPLETED│   │        │
│    │  └──────────────────────────────────────┘   │        │
│    │                  ↓                           │        │
│    │  ┌──────────────────────────────────────┐   │        │
│    │  │  GOLD_PROCESSING → GOLD_COMPLETED   │   │        │
│    │  └──────────────────────────────────────┘   │        │
│    └──────────────────────────────────────────────┘        │
│                        ↓                                    │
│                    COMPLETED                               │
│                    (Success)                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Layers

```
┌──────────────────────────────────────────────────────────┐
│ BRONZE LAYER (Raw Data)                                  │
│ Format: JSON | Retention: 30 days                        │
│ storage/bronze/{source}/{city}/{category}/raw_*.json     │
└──────────────────────────────────────────────────────────┘
                        ↓ (Normalize, Validate)
┌──────────────────────────────────────────────────────────┐
│ SILVER LAYER (Standardized)                              │
│ Format: Parquet | Retention: 1 year                      │
│ storage/silver/{source}/{city}/{category}/processed_*.p  │
└──────────────────────────────────────────────────────────┘
                   ↓ (Enrich, Merge, Deduplicate)
┌──────────────────────────────────────────────────────────┐
│ GOLD LAYER (Business-Ready)                              │
│ Format: Parquet + MongoDB | Retention: 2+ years         │
│ storage/gold/{entity}/{city}/ + master_poi collection    │
└──────────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│ SERVING LAYER (APIs, Analytics, AI/ML)                  │
│ REST API | Elasticsearch | Vector Search | Dashboards   │
└──────────────────────────────────────────────────────────┘
```

---

## MongoDB Collections Quick Map

| Collection | Purpose | Key Index | Typical Size |
|------------|---------|-----------|--------------|
| **source_registry** | Source management | source_name | ~10 docs |
| **pipeline_registry** | Pipeline definitions | pipeline_name | ~20 docs |
| **pipeline_execution** | Execution history | execution_id | 1000s/day |
| **pipeline_stage_execution** | Stage details | execution_id | 3000s/day |
| **master_poi** | POI main data | poi_id, location | Millions |
| **poi_reviews** | POI reviews | poi_id, created_at | 10s millions |
| **data_quality_reports** | Quality metrics | execution_id | 1000s/day |
| **pipeline_logs** | Detailed logs | execution_id | 10s millions |

---

## Common Queries (MongoDB)

### Find POI Near Location
```javascript
db.master_poi.find({
  location: {
    $near: {
      $geometry: { type: "Point", coordinates: [139.7454, 35.6586] },
      $maxDistance: 5000
    }
  }
}).limit(10)
```

### Full-Text Search
```javascript
db.master_poi.find(
  { $text: { $search: "tokyo tower" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
```

### Filter by Category & City
```javascript
db.master_poi.find({
  city: "tokyo",
  category: "restaurant",
  rating: { $gte: 4.0 }
}).sort({ rating: -1 }).limit(20)
```

### Get Execution History
```javascript
db.pipeline_execution.find({
  pipeline_name: "osm_pipeline"
}).sort({ started_at: -1 }).limit(10)
```

### Category Statistics
```javascript
db.master_poi.aggregate([
  { $match: { city: "tokyo" } },
  { $group: {
      _id: "$category",
      count: { $sum: 1 },
      avg_rating: { $avg: "$rating.overall" }
    }
  },
  { $sort: { count: -1 } }
])
```

---

## Index Commands

### Create Indexes for master_poi
```javascript
// Geospatial
db.master_poi.createIndex({ location: "2dsphere" })

// Text search
db.master_poi.createIndex({ name: "text", search_keywords: "text" })

// Filtering
db.master_poi.createIndex({ city: 1, category: 1 })

// Sorting
db.master_poi.createIndex({ rating: -1, review_count: -1 })

// Performance
db.master_poi.createIndex({ business_score: -1 })
db.master_poi.createIndex({ updated_at: -1 })
```

### Create Indexes for pipeline_execution
```javascript
db.pipeline_execution.createIndex({ execution_id: 1 }, { unique: true })
db.pipeline_execution.createIndex({ status: 1, started_at: -1 })
db.pipeline_execution.createIndex({ pipeline_name: 1, started_at: -1 })
```

---

## POI Document Structure

```javascript
{
  "_id": ObjectId,
  "poi_id": "poi_tokyo_001",
  "name": "Tokyo Tower",
  "city": "tokyo",
  "country": "japan",
  "category": "tourist_attraction",
  "location": {
    "type": "Point",
    "coordinates": [139.7454, 35.6586]  // [lng, lat]
  },
  "rating": {
    "overall": 4.7,
    "osm": 4.5,
    "google": 4.8,
    "tripadvisor": 4.6
  },
  "review_count": 25000,
  "sources": ["osm", "google_places", "tripadvisor"],
  "source_pois": {
    "osm": "osm_12345",
    "google": "google_67890",
    "tripadvisor": "ta_11111"
  },
  "business_score": 0.92,
  "search_keywords": ["tokyo tower", "japan landmark"],
  "tags": ["landmark", "photo_spot", "tourist"],
  "opening_hours": "9:00-23:00",
  "phone": "+81-3-5802-8111",
  "website": "https://www.tokyotower.co.jp/",
  "amenities": ["restroom", "restaurant", "gift_shop"],
  "updated_at": ISODate("2026-05-08T10:00:00Z"),
  "created_at": ISODate("2026-04-01T10:00:00Z")
}
```

---

## Execution Metadata Structure

```javascript
{
  "execution_id": "exec_20260508_120000",
  "pipeline_name": "osm_pipeline",
  "source_name": "osm",
  "status": "COMPLETED",  // RUNNING, COMPLETED, FAILED
  "current_stage": "gold",
  
  "timing": {
    "started_at": ISODate("2026-05-08T10:00:00Z"),
    "completed_at": ISODate("2026-05-08T10:06:00Z"),
    "duration_ms": 360000
  },
  
  "records": {
    "total_processed": 15000,
    "successfully_processed": 14968,
    "failed": 32,
    "error_rate": 0.21
  },
  
  "artifacts": {
    "bronze_location": "s3://bucket/bronze/osm/2026-05-08/",
    "silver_location": "s3://bucket/silver/osm/2026-05-08/",
    "gold_location": "s3://bucket/gold/2026-05-08/"
  },
  
  "retry_count": 0,
  "error_message": null
}
```

---

## Pipeline Configuration Template

```json
{
  "pipeline_name": "osm_pipeline",
  "source_name": "osm",
  "version": "1.0",
  "enabled": true,
  "stages": ["bronze", "silver", "gold"],
  
  "stage_config": {
    "bronze": {
      "type": "raw_fetch",
      "batch_size": 1000,
      "timeout_sec": 300
    },
    "silver": {
      "type": "transformation",
      "transformations": ["normalize", "validate", "deduplicate"],
      "timeout_sec": 600
    },
    "gold": {
      "type": "aggregation",
      "aggregations": ["merge", "enrich", "score"],
      "timeout_sec": 900
    }
  },
  
  "retry_policy": {
    "max_retry": 3,
    "backoff_type": "exponential",
    "backoff_ms": 1000
  },
  
  "schedule": "0 */6 * * *",
  "schedule_timezone": "UTC",
  "owner": "data_engineering_team"
}
```

---

## Stage Definitions

### Bronze Stage
- **Input:** API responses (JSON)
- **Output:** Raw JSON files
- **Operations:** Fetch, Store
- **Duration:** Usually 30-60 min
- **Failure:** Network error, API quota
- **Retry:** Yes, with backoff

### Silver Stage
- **Input:** Bronze JSON
- **Output:** Parquet files
- **Operations:** Normalize, Validate, Deduplicate
- **Duration:** Usually 60-120 min
- **Failure:** Schema mismatch, data type error
- **Retry:** Yes, from checkpoint

### Gold Stage
- **Input:** Silver Parquet
- **Output:** MongoDB + Parquet
- **Operations:** Merge, Enrich, Index
- **Duration:** Usually 30-60 min
- **Failure:** Memory limit, index error
- **Retry:** Yes, idempotent

---

## Troubleshooting Checklist

| Issue | Check | Fix |
|-------|-------|-----|
| **Stuck RUNNING** | `db.pipeline_execution.find({status: "RUNNING"})` | Force FAILED status |
| **High error rate** | `db.data_quality_reports.findOne({})` | Review validation rules |
| **Memory issues** | Resource usage in stage execution | Reduce batch size |
| **Slow queries** | `db.master_poi.find({city: "tokyo"}).explain()` | Add index |
| **Missing data** | Check retry_count, error_message | Re-run pipeline |
| **Outdated cache** | Check updated_at timestamp | Run Gold stage again |

---

## Performance Tips

```javascript
// 1. Always use indexes
db.master_poi.createIndex({ city: 1, category: 1 })

// 2. Limit result sets
db.master_poi.find({...}).limit(1000)

// 3. Project only needed fields
db.master_poi.find({...}, { poi_id: 1, name: 1, rating: 1 })

// 4. Use aggregation pipeline for complex ops
db.master_poi.aggregate([
  { $match: {...} },
  { $group: {...} }
])

// 5. Partition data by city/date
// storage/gold/master_poi/tokyo/2026-05-08/

// 6. Archive old records
// Move data >1 year old to archive collection
```

---

## Environment Variables

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017/smart_travel
MONGO_USER=admin
MONGO_PASS=secure_password

# Storage
STORAGE_PATH=/data/smart_tourism
STORAGE_TYPE=s3  # or gcs, local

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Pipeline
MAX_RETRIES=3
BACKOFF_MS=1000
TIMEOUT_SEC=600

# Resources
MEMORY_LIMIT_MB=4096
CPU_LIMIT=4
```

---

## Command Reference

### Start Services
```bash
# Start MongoDB
mongod --dbpath /data/db

# Start API server
python -m smart_tourism.api

# Start pipeline orchestrator
python -m smart_tourism.orchestrator

# Start monitoring
prometheus --config.file=prometheus.yml
grafana-server
```

### Pipeline Operations
```bash
# Trigger pipeline
python execute.py --pipeline osm_pipeline

# Monitor execution
python monitor.py --execution-id exec_20260508_120000 --watch

# View history
python history.py --pipeline osm_pipeline --limit 10

# Cancel execution
python cancel.py --execution-id exec_20260508_120000
```

### Database Operations
```bash
# Backup
mongodump --uri "mongodb://localhost:27017/smart_travel" --out ./backup

# Restore
mongorestore --uri "mongodb://localhost:27017/smart_travel" ./backup

# Compact collection
db.runCommand({ compact: "master_poi" })

# Rebuild indexes
db.master_poi.reIndex()
```

---

## Key Metrics to Monitor

| Metric | Threshold | Alert |
|--------|-----------|-------|
| **Error Rate** | >5% | High error rate |
| **Execution Time** | >2x avg | Slow execution |
| **Memory Usage** | >80% limit | OOM risk |
| **Data Staleness** | >24hrs | Stale data |
| **Index Size** | >10GB | Large indexes |
| **Queue Length** | >100 | Backlog building |

---

**Last Updated:** May 2026 | **Version:** 1.0
