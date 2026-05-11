# SMART TOURISM DATA PLATFORM - Complete Documentation Package

**Version:** 1.0  
**Status:** Final  
**Created:** May 2026

---

## 📋 Documentation Contents

This package contains comprehensive architecture and design documentation for the SMART TOURISM DATA PLATFORM.

### Files Included

#### 1. **SMART_TOURISM_DATA_PLATFORM.docx** (17 KB)
   - Professional Word document with complete system design
   - Covers all architectural components
   - Includes pipeline lifecycle, workflows, and database schema
   - **Best for:** Formal presentations, stakeholder reviews
   - **Sections:**
     - I. Pipeline Lifecycle Design
     - II. Pipeline Workflow Design  
     - III. Dataflow Design
     - IV. Entity Relationship Diagram (ERD)
     - V. Database Schema Design
     - VI. Index & Storage Design
     - VII. Final Architecture Summary

#### 2. **SMART_TOURISM_DATA_PLATFORM_Architecture.pdf** (15 KB)
   - Visually formatted PDF with diagrams and tables
   - Quick-reference architecture overview
   - State diagrams and data flow visualizations
   - **Best for:** Visual learners, quick reference
   - **Includes:**
     - System overview and use cases
     - State machine diagrams
     - Three-layer lakehouse architecture
     - Database design essentials
     - Monitoring and best practices

#### 3. **SMART_TOURISM_DEVELOPER_GUIDE.md** (20 KB)
   - Comprehensive developer guide with code examples
   - Practical implementation patterns
   - Detailed connector examples
   - MongoDB schema with validation
   - Query patterns and best practices
   - **Best for:** Developers and engineers
   - **Sections:**
     - System overview and architecture principles
     - Pipeline lifecycle and state management
     - Workflow patterns for each data source
     - Data lakehouse organization
     - Database schema with validation
     - Query patterns and examples
     - Deployment guide and troubleshooting
     - API reference
     - Quick commands and environment variables

#### 4. **SMART_TOURISM_SCHEMAS.json** (15 KB)
   - Complete JSON Schema reference for all MongoDB collections
   - Field definitions, types, and constraints
   - Index specifications
   - Query examples
   - **Best for:** Backend developers, database administrators
   - **Collections:**
     - source_registry
     - pipeline_registry
     - pipeline_execution
     - pipeline_stage_execution
     - master_poi
     - poi_reviews
     - poi_categories
     - data_quality_reports

#### 5. **SMART_TOURISM_CHEATSHEET.md** (10 KB)
   - Quick reference guide with visual diagrams
   - Common MongoDB queries
   - Command reference
   - Troubleshooting checklist
   - Performance tips
   - **Best for:** Quick lookup, daily reference
   - **Quick Maps:**
     - Pipeline state diagram
     - Data flow layers
     - Collection quick reference
     - Common queries
     - Index commands
     - Troubleshooting checklist

#### 6. **MONGODB_PIPELINE.md** (15 KB) ⭐⭐ NEW
   - **Simplified MongoDB-only 3-layer architecture**
   - All layers (Bronze/Silver/Gold) in MongoDB
   - Direct MongoDB query access
   - Easy backup and export
   - API endpoints for pipeline operations
   - **Best for:** Understanding simplified storage
   - **Sections:**
     - Architecture overview
     - Schema definitions for each layer
     - MongoDB query examples
     - Export/import guide
     - API usage examples

#### 7. **PLUGIN_SYSTEM.md** (15 KB) ⭐⭐ NEW
   - **Dynamic Plugin Architecture** for truly extensible system
   - Plugin registration and management via API
   - Base interfaces: BaseCollector, BaseTransformer
   - Plugin Registry (MongoDB-backed)
   - Dynamic loading and hot-swapping
   - Example: TripAdvisor collector implementation
   - **Best for:** Developers adding new data sources
   - **Sections:**
     - Plugin architecture overview
     - Base class interfaces
     - API endpoints for plugin management
     - Source configuration guide
     - Plugin development tutorial
     - Migration from hardcoded to dynamic

---

## 🏗️ Architecture Overview

### High-Level System Design

```
External Sources (OSM, Google Places, TripAdvisor)
           ↓
   Metadata-driven Pipeline Platform
           ↓
   Dynamic Orchestration Engine
           ↓
   ┌─────────────────────────────────────────────────────┐
   │      THREE-LAYER STORAGE (MongoDB Only)            │
   │                                                     │
   │  🥉 Bronze Layer (MongoDB Collection)               │
   │     └─ Collection: bronze_records                  │
   │     └─ Raw API responses                           │
   │                                                     │
   │  🥈 Silver Layer (MongoDB Collection)               │
   │     └─ Collection: silver_pois                      │
   │     └─ Cleaned & normalized data                   │
   │                                                     │
   │  🥇 Gold Layer (MongoDB Collection)                 │
   │     └─ Collection: gold_master_pois                 │
   │     └─ Enriched, production-ready                  │
   └─────────────────────────────────────────────────────┘
           ↓
   REST APIs / Analytics / AI/ML Features
```

### NEW: Simplified MongoDB Pipeline (May 2026)

**Kiến trúc mới** - Tất cả layers trong MongoDB:
- **Bronze**: `bronze_records` collection - Raw API responses
- **Silver**: `silver_pois` collection - Cleaned & normalized
- **Gold**: `gold_master_pois` collection - Production-ready

| Layer | Collection | Format | Use Case |
|-------|-----------|--------|----------|
| **Bronze** | `bronze_records` | BSON documents | Raw API responses |
| **Silver** | `silver_pois` | BSON documents | Cleaned, searchable data |
| **Gold** | `gold_master_pois` | BSON documents | Production-ready master data |

**Lợi ích:**
- ✅ **Simple**: Chỉ 1 database (MongoDB)
- ✅ **Easy Query**: MongoDB queries cho mọi layer
- ✅ **Easy Backup**: Backup 1 nơi
- ✅ **Fast Transform**: Không chuyển đổi storage systems

**API Endpoints:**
- `POST /api/v1/pipeline/bronze/collect` → Collect to MongoDB
- `POST /api/v1/pipeline/bronze-to-silver` → Transform Bronze → Silver
- `POST /api/v1/pipeline/silver-to-gold` → Transform Silver → Gold
- `GET /api/v1/pipeline/layers/stats` → View all layers stats

📖 **Chi tiết:** Xem [MONGODB_PIPELINE.md](./MONGODB_PIPELINE.md)

### Key Features

✅ **State Machine Pipeline Lifecycle**
- Guaranteed state transitions
- Checkpoint-based recovery
- Automatic retry with exponential backoff

✅ **Three-Layer Data Lakehouse (MongoDB)**
- Bronze: `bronze_records` - Store raw API responses
- Silver: `silver_pois` - Normalize and validate data
- Gold: `gold_master_pois` - Unified, enriched, indexed data

✅ **Multi-Source Data Unification**
- Entity resolution and deduplication
- Cross-source rating aggregation
- Business scoring and ranking

✅ **Enterprise Observability**
- Real-time execution metrics
- Data quality reporting
- Health checks and alerting

✅ **Fault Tolerance & Recovery**
- Automatic retry mechanisms
- Checkpoint-based resume
- Comprehensive error logging

---

## 📊 Data Model Quick Reference

### Bronze Layer (MinIO) - Raw Data
```json
{
  "u_key": "05b30c17164df56e",
  "original_osm_name": "Quán Quốc Trung",
  "city": "hanoi",
  "category": "restaurant",
  "harvested_at": "2026-05-10T15:18:37.324532",
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
    "priceLevel": "PRICE_LEVEL_MODERATE"
  }
}
// Stored in MinIO: bronze/google/hanoi/restaurant/20260510_143022_a1b2c3.json
```

### Silver Layer (MongoDB) - Cleaned Data
```javascript
{
  "_id": ObjectId("..."),
  "place_id": "ChIJ...",
  "u_key": "05b30c17164df56e",
  "name": "Place Name",
  "city": "hanoi",
  "location": { "lat": 21.0, "lng": 105.8 },
  "address": "123 Street, Hanoi",
  "category": "restaurant",
  "types": ["restaurant", "food"],
  "rating": 4.5,
  "user_rating_count": 1234,
  "price_level": 2,
  "photos": ["url1", "url2"],
  "image_url": "main_photo_url",
  "_source": "google_places",
  "_bronze_path": "bronze/google/hanoi/restaurant/...",
  "_collected_at": "2026-05-10T15:18:37",
  "_transformed_at": "2026-05-10T16:00:00",
  "layer": "silver"
}
```

### Gold Layer (MongoDB) - Master Data
```javascript
{
  "_id": ObjectId("..."),
  "poi_id": "gold_ChIJ...",
  "place_id": "ChIJ...",
  // ... (all Silver fields)
  "layer": "gold",
  "quality_score": 0.85,
  "data_completeness": 0.92,
  "subcategory": "vietnamese_restaurant",
  "review_count": 1234,
  "is_active": true,
  "verified": false,
  "created_at": ISODate("2026-05-10T16:00:00Z"),
  "updated_at": ISODate("2026-05-10T16:00:00Z")
}
```

### Execution Metadata
```javascript
{
  execution_id: "exec_20260508_120000",
  pipeline_name: "minio_pipeline",
  status: "COMPLETED",
  records: {
    bronze_collected: 4452,
    silver_transformed: 3200,
    gold_enriched: 3100,
    error_rate: 0.03
  },
  duration_ms: 360000,
  storage: {
    bronze_bucket: "smart-travel-bronze",
    silver_collection: "silver_pois",
    gold_collection: "gold_master_pois"
  }
}
```

---

## 🔍 Getting Started

### For Architects & Decision Makers
→ Read: **SMART_TOURISM_DATA_PLATFORM.docx**
- Complete system overview
- Design principles and patterns
- Scalability and performance considerations

### For Developers & Engineers
→ Start with: **SMART_TOURISM_DEVELOPER_GUIDE.md**
- Implementation patterns
- Code examples
- Deployment guide
- Then reference: **SMART_TOURISM_SCHEMAS.json** for exact field specifications

### For Quick Lookups
→ Use: **SMART_TOURISM_CHEATSHEET.md**
- Common queries
- Command reference
- Troubleshooting tips

### For Database Design
→ Reference: **SMART_TOURISM_SCHEMAS.json**
- Complete field definitions
- Index specifications
- Example documents

### For Visual Understanding
→ View: **SMART_TOURISM_DATA_PLATFORM_Architecture.pdf**
- System diagrams
- Data flow visualizations
- Architecture layers

---

## 🚀 Key Use Cases

### 1. POI Data Unification
```
OSM Data + Google Data + TripAdvisor Data
    → Entity Resolution
    → Deduplication
    → Unified Master POI
```

### 2. Real-time Data Enrichment
```
New Review
    → Quality Check
    → Aggregation
    → Score Update
    → Index Update
```

### 3. Geographic Search
```
User Query: "Restaurants near Tokyo"
    → Geospatial Query (2dsphere index)
    → Filter by Category
    → Sort by Business Score
    → Return Top 20 Results
```

### 4. Full-Text Search
```
User Query: "Best temples Tokyo"
    → Text Search (text index)
    → Match Keywords
    → Sort by Score
    → Return Results
```

---

## 📈 System Scalability

| Component | Capacity | Scaling Strategy |
|-----------|----------|-----------------|
| **POI Records** | Millions | Partition by city, category, date |
| **Daily Executions** | 1000s | Parallel processing, distributed scheduling |
| **Reviews** | 10s millions | Sharded collection by poi_id |
| **Query Throughput** | 10k QPS | Read replicas, index optimization |
| **Storage** | PB scale | Cloud object storage (S3/GCS) |

---

## 🔒 Data Governance

### Data Lineage
Every POI record tracks:
- Original source (osm, google, tripadvisor)
- Transform pipeline and stage
- Quality scores at each layer
- Last update timestamp

### Quality Assurance
- Schema validation at Bronze → Silver transition
- Duplicate detection at Silver → Gold transition
- Quality reports generated per execution
- Automated alerting for quality issues

### Retention Policy
- Bronze: 30 days
- Silver: 1 year
- Gold: 2+ years
- Execution logs: 90 days

---

## 🛠️ Common Operations

### Register New Pipeline
```bash
# Edit pipeline_registry.json
python register_pipeline.py --config pipeline_registry.json
```

### Trigger Pipeline Execution
```bash
python execute.py --pipeline osm_pipeline --execution-id exec_20260508_120000
```

### Monitor Execution
```bash
python monitor.py --execution-id exec_20260508_120000 --watch
```

### Query POI Data
```javascript
db.master_poi.find({ city: "tokyo", category: "restaurant" })
             .sort({ business_score: -1 })
             .limit(20)
```

### View Execution History
```javascript
db.pipeline_execution.find({ pipeline_name: "osm_pipeline" })
                    .sort({ started_at: -1 })
                    .limit(10)
```

---

## 📚 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow | Pipeline scheduling |
| **Processing** | Apache Spark / Pandas | Data transformation |
| **Bronze Storage** | MinIO (S3-compatible) | Raw JSON files |
| **Silver/Gold Storage** | MongoDB | Cleaned, indexed data |
| **API Framework** | FastAPI | REST endpoints |
| **Formats** | JSON (Bronze), BSON (Silver/Gold) | Data serialization |
| **Search** | MongoDB Text/Geo | Full-text & geospatial |
| **Monitoring** | Prometheus + Grafana | Metrics & dashboards |
| **Logging** | ELK Stack | Centralized logging |
| **Deployment** | Docker + Kubernetes | Container orchestration |

---

## 🆘 Support & Troubleshooting

### Common Issues

**Q: Pipeline stuck in RUNNING state**
A: Check execution logs, force state transition if necessary
   → See SMART_TOURISM_DEVELOPER_GUIDE.md section 9.1

**Q: High error rate in Silver stage**
A: Review data quality report, check validation rules
   → See SMART_TOURISM_CHEATSHEET.md Troubleshooting section

**Q: Slow query performance**
A: Verify indexes exist, analyze query plan
   → See SMART_TOURISM_DEVELOPER_GUIDE.md section 7

**Q: Out of memory during processing**
A: Reduce batch size or add more workers
   → See SMART_TOURISM_DEVELOPER_GUIDE.md section 9.1

---

## 📞 Contact & Resources

For questions or issues:
1. Check relevant documentation section
2. Review SMART_TOURISM_CHEATSHEET.md for quick answers
3. Consult SMART_TOURISM_DEVELOPER_GUIDE.md for detailed examples
4. Contact Data Engineering team

---

## 📝 Document Versions

| Date | Version | Status | Changes |
|------|---------|--------|---------|
| May 2026 | 1.0 | ✅ Final | Initial comprehensive documentation |
| May 10, 2026 | 1.1 | ✅ Updated | Added MinIO + MongoDB hybrid architecture |

### Version 1.1 Changes:
- ⭐ **NEW:** MinIO object storage for Bronze layer
- ⭐ **NEW:** API endpoints for pipeline operations (`/api/v1/pipeline/*`)
- ⭐ **NEW:** Service classes: `BronzePipeline`, `SilverGoldPipeline`
- 🔄 **Updated:** Architecture diagram (Bronze→MinIO, Silver/Gold→MongoDB)
- 🔄 **Updated:** Data model documentation with 3-layer schemas
- 🔄 **Updated:** Technology stack with MinIO
- 📖 **NEW:** Document `MINIO_MONGODB_PIPELINE.md`

---

## 📄 License & Usage

These documents are for internal use within the organization.
Unauthorized distribution is not permitted.

---

**For more details, refer to specific documentation files provided in this package.**

Happy Building! 🚀
