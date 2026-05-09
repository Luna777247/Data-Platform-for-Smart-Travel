# SMART TOURISM DATA PLATFORM
## Architecture & Design Documentation

**Version:** 1.0  
**Status:** Final  
**Created:** May 2026

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Pipeline Lifecycle](#pipeline-lifecycle)
4. [Pipeline Workflows](#pipeline-workflows)
5. [Data Lakehouse Architecture](#data-lakehouse-architecture)
6. [MongoDB Database Design](#mongodb-database-design)
7. [Indexing Strategy](#indexing-strategy)
8. [Monitoring & Observability](#monitoring--observability)
9. [Best Practices & Recommendations](#best-practices--recommendations)
10. [Conclusion](#conclusion)

---

## Introduction

**SMART TOURISM DATA PLATFORM** là một hệ thống xử lý dữ liệu du lịch quy mô lớn, được thiết kế dựa trên kiến trúc data lakehouse hiện đại. Hệ thống tích hợp dữ liệu từ nhiều nguồn (OpenStreetMap, Google Places, TripAdvisor, v.v.) để tạo ra một kho dữ liệu thống nhất và sẵn sàng cho các ứng dụng AI/ML.

### Mục tiêu chính

- ✅ Tích hợp dữ liệu từ nhiều nguồn khác nhau
- ✅ Bảo đảm chất lượng dữ liệu thông qua validation pipeline
- ✅ Tạo ra dữ liệu chuẩn (canonical) để tránh trùng lặp
- ✅ Cung cấp dữ liệu sẵn sàng cho các ứng dụng và dịch vụ
- ✅ Giám sát chi tiết mỗi bước xử lý (observability)
- ✅ Tự động phục hồi từ lỗi (fault tolerance)

### Lợi ích

- 📉 Giảm chi phí duy trì dữ liệu nhờ tự động hóa
- ⚡ Tăng tốc độ phát triển các tính năng mới
- 🎯 Nâng cao độ tin cậy của dữ liệu
- 🔍 Dễ dàng theo dõi nguồn gốc dữ liệu (data lineage)

---

## System Overview

### Kiến trúc tổng quan

```
External Sources (OSM, Google Places, TripAdvisor)
           ↓
   Metadata-driven Pipeline Platform
           ↓
   Dynamic Orchestration Engine
           ↓
   ┌─────────────────────────────────────┐
   │  Bronze/Silver/Gold Lakehouse       │
   │  ├─ Bronze: Raw JSON                │
   │  ├─ Silver: Standardized Parquet    │
   │  └─ Gold: Business-Ready Data       │
   └─────────────────────────────────────┘
           ↓
   MongoDB Collections + Indexes
           ↓
   REST APIs / Analytics / AI/ML Features
```

### Các thành phần chính

1. **Metadata-driven Pipeline Platform**
   - Pipeline định nghĩa dưới dạng metadata (JSON)
   - Hỗ trợ nhiều loại source và stage
   - Dynamic pipeline loading và execution

2. **Dynamic Orchestration Engine**
   - State-machine architecture cho lifecycle
   - Automatic retry với exponential backoff
   - Dependency management và scheduling

3. **Plugin-based Source Connectors**
   - Pluggable connector interface
   - Hỗ trợ REST API, GraphQL, gRPC
   - Built-in rate limiting và pagination

4. **Bronze/Silver/Gold Lakehouse**
   - Bronze: Lưu trữ dữ liệu thô (JSON)
   - Silver: Dữ liệu chuẩn (Parquet)
   - Gold: Dữ liệu sẵn sàng kinh doanh

5. **Unified Gold Business Layer**
   - Entity resolution & deduplication
   - Multi-source data merging
   - Business scoring & ranking

6. **Monitoring & Observability**
   - Real-time execution metrics
   - Data quality reports
   - Health checks & alerting

7. **Enterprise Data Governance**
   - Data lineage tracking
   - Schema versioning
   - Access control & audit logging

---

## Pipeline Lifecycle

### State Machine Architecture

Pipeline được quản lý theo state-machine architecture, cho phép theo dõi chính xác trạng thái của mỗi lần thực thi.

```
CREATED
   ↓
REGISTERED
   ↓
SCHEDULED
   ↓
QUEUED
   ↓
INITIALIZING
   ↓
RUNNING
├─ VALIDATING (Schema check)
├─ BRONZE_PROCESSING (Raw fetch)
├─ BRONZE_COMPLETED
├─ SILVER_PROCESSING (Transform)
├─ SILVER_COMPLETED
├─ GOLD_PROCESSING (Enrich)
├─ GOLD_COMPLETED
   ↓
COMPLETED (Success)
```

### Failure Recovery

Khi pipeline gặp lỗi, hệ thống sẽ tự động thử lại (retry) với exponential backoff:

```
FAILED
   ↓
RETRY_PENDING (Check retry policy)
   ↓
RETRYING (Attempt again)
   ↓
RECOVERED (Success)
   ↓
FAILED_PERMANENTLY (Max retries exceeded)
```

### Retry Policy

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_type": "exponential",
    "initial_delay_ms": 1000,
    "max_delay_ms": 60000,
    "multiplier": 2.0
  }
}
```

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: After 1s (1000ms)
- Attempt 3: After 2s (2000ms)
- Attempt 4: After 4s (4000ms)

---

## Pipeline Workflows

### 2.1 OSM (OpenStreetMap) Pipeline

Quy trình xử lý dữ liệu từ OpenStreetMap - một trong những nguồn dữ liệu địa lý lớn nhất:

```
OSM API
   ↓
Raw Fetch
   ↓
Bronze Storage (nguyên bản)
   ↓
Schema Validation (kiểm tra cấu trúc)
   ↓
Silver Transformation (chuẩn hóa)
   ↓
Canonical POI Generation (tạo POI chuẩn)
   ↓
Deduplication (loại bỏ trùng)
   ↓
Silver Storage (lưu bản chuẩn)
   ↓
Gold Aggregation (tổng hợp)
   ↓
Analytics/Search Layer
```

### 2.2 Google Places Enrichment

Quy trình làm giàu dữ liệu từ Google Places - tích hợp thông tin đánh giá, ảnh, chi tiết cơ sở:

```
Silver OSM POI
   ↓
Google Matching Engine (tìm POI khớp)
   ↓
Google Places API (lấy chi tiết)
   ↓
Google Bronze Storage
   ↓
Google Transformation
   ↓
Review/Rating Enrichment (thêm đánh giá)
   ↓
Google Silver
   ↓
Entity Merge Engine (gộp entities)
   ↓
Unified Gold Layer
```

### 2.3 Unified Gold Workflow

Quy trình hợp nhất dữ liệu từ nhiều nguồn:

```
OSM Silver
        ↓
Google Silver
        ↓
TripAdvisor Silver
        ↓
Entity Resolution (giải quyết trùng)
        ↓
POI Deduplication
        ↓
Business Scoring (tính điểm)
        ↓
Search Optimization (tối ưu tìm kiếm)
        ↓
Recommendation Features (tính năng gợi ý)
        ↓
Gold Master POI
```

---

## Data Lakehouse Architecture

### Three-Layer Architecture

Dữ liệu được tổ chức theo ba layer: Bronze (thô), Silver (chuẩn), Gold (kinh doanh).

| Layer | Mục đích | Format | Chi tiết |
|-------|---------|--------|---------|
| **Bronze** | Lưu trữ thô | JSON | Dữ liệu gốc từ API |
| **Silver** | Chuẩn hóa | Parquet | Schema chuẩn, đã kiểm tra |
| **Gold** | Sẵn sàng | Parquet | Dữ liệu làm giàu, có chỉ mục |

### Bronze Layer (Raw Data)

```
Purpose: Store raw API responses
Format: JSON (unmodified)
Location: storage/bronze/{source}/{city}/{category}/raw_{datetime}.json
Retention: 30 days (after successful Silver processing)

Example: storage/bronze/osm/tokyo/restaurant/raw_20260508_120000.json

Metadata:
{
  "source": "osm",
  "fetch_time": "2026-05-08T10:00:00Z",
  "api_version": "0.6",
  "record_count": 1500,
  "file_size_bytes": 45000,
  "checksum_sha256": "abc123..."
}
```

### Silver Layer (Processed)

```
Purpose: Standardized, validated data
Format: Parquet (columnar)
Location: storage/silver/{source}/{city}/{category}/processed_{datetime}.parquet
Retention: 1 year

Schema includes:
- poi_id: string
- name: string
- latitude: double
- longitude: double
- category: string
- rating: float
- review_count: integer
- opening_hours: string
- phone: string
- website: string

Validation:
- Records validated: 1468
- Records failed: 32
- Quality score: 0.98
```

### Gold Layer (Business-Ready)

```
Purpose: Unified, enriched, indexed data
Format: Parquet + MongoDB
Location: storage/gold/{entity_type}/{city}/

Contents:
├─ master_poi_{city}_{date}.parquet
│  └─ Unified POI data with all sources
├─ poi_reviews_{city}_{date}.parquet
│  └─ Aggregated reviews
├─ poi_metadata_{city}_{date}.parquet
│  └─ Processing metadata
├─ quality_report_{city}_{date}.parquet
│  └─ Quality metrics
└─ MongoDB Collections
   ├─ master_poi (with indexes)
   ├─ poi_reviews
   └─ poi_categories

Features:
- Full-text search indexes
- Geospatial 2dsphere indexes
- Composite indexes for common filters
- TTL indexes for cleanup
```

---

## MongoDB Database Design

### Collection Overview

```
smart_travel database
├── source_registry (Quản lý nguồn dữ liệu)
├── pipeline_registry (Định nghĩa pipeline)
├── pipeline_execution (Lịch sử thực thi)
├── pipeline_stage_execution (Thực thi từng stage)
├── retry_history (Lịch sử retry)
├── pipeline_logs (Log chi tiết)
├── monitoring_metrics (Metrics giám sát)
├── data_quality_reports (Báo cáo chất lượng)
├── bronze_metadata (Metadata layer bronze)
├── silver_metadata (Metadata layer silver)
├── gold_metadata (Metadata layer gold)
├── master_poi (POI chính)
├── poi_reviews (Đánh giá POI)
├── poi_categories (Loại POI)
├── poi_tags (Tag POI)
├── geo_index (Chỉ mục địa lý)
└── search_index (Chỉ mục tìm kiếm)
```

### Master POI Document

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
    "coordinates": [139.7454, 35.6586]
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
    "osm": "osm_poi_12345",
    "google": "google_poi_67890",
    "tripadvisor": "ta_poi_11111"
  },
  "search_keywords": ["tokyo tower", "japan landmark"],
  "business_score": 0.92,
  "popularity_score": 0.95,
  "relevance_score": 0.88,
  "tags": ["landmark", "photo_spot", "tourist"],
  "opening_hours": "9:00-23:00",
  "phone": "+81-3-5802-8111",
  "website": "https://www.tokyotower.co.jp/",
  "amenities": ["restroom", "restaurant", "gift_shop"],
  "quality_score": 0.94,
  "updated_at": ISODate("2026-05-08T10:00:00Z")
}
```

### Pipeline Execution Document

```javascript
{
  "_id": ObjectId,
  "execution_id": "exec_001",
  "pipeline_name": "osm_pipeline",
  "source_name": "osm",
  "status": "RUNNING",
  "current_stage": "silver",
  "started_at": ISODate("2026-05-08T10:00:00Z"),
  "completed_at": ISODate,
  "duration_ms": 120000,
  "records": {
    "total_processed": 10000,
    "successfully_processed": 9988,
    "failed": 12,
    "error_rate": 0.12
  },
  "retry_count": 1,
  "artifacts": {
    "bronze_location": "s3://bucket/bronze/osm/2026-05-08/",
    "silver_location": "s3://bucket/silver/osm/2026-05-08/"
  }
}
```

---

## Indexing Strategy

### Master POI Indexes

Các chỉ mục được tạo để tối ưu các truy vấn thường dùng:

```javascript
// Geospatial Index (tìm kiếm địa lý)
db.master_poi.createIndex({ "location": "2dsphere" })

// Text Search Index
db.master_poi.createIndex({
  name: "text",
  search_keywords: "text"
})

// Composite Indexes
db.master_poi.createIndex({ city: 1, category: 1 })
db.master_poi.createIndex({ rating: -1, review_count: -1 })
db.master_poi.createIndex({ sources: 1, poi_id: 1 })
db.master_poi.createIndex({ business_score: -1 })
db.master_poi.createIndex({ updated_at: -1 })
```

### Pipeline Execution Indexes

```javascript
db.pipeline_execution.createIndex({ execution_id: 1 }, { unique: true })
db.pipeline_execution.createIndex({ status: 1, started_at: -1 })
db.pipeline_execution.createIndex({ pipeline_name: 1, started_at: -1 })
db.pipeline_execution.createIndex({ created_at: -1 })
```

---

## Monitoring & Observability

### Execution Metrics

Mỗi pipeline execution được theo dõi chi tiết với các metrics:

**Timing Metrics:**
- started_at, completed_at - Thời điểm bắt đầu/kết thúc
- duration_ms - Tổng thời gian thực thi

**Data Metrics:**
- records_processed - Số record đã xử lý
- records_failed - Số record lỗi
- error_rate - Tỷ lệ lỗi (%)

**Performance Metrics:**
- memory_used_mb - Bộ nhớ sử dụng
- cpu_usage_percent - CPU sử dụng
- throughput_records_per_sec - Thông lượng

### Data Quality Monitoring

- ✓ Schema validation - Kiểm tra cấu trúc dữ liệu
- ✓ Duplicate detection - Phát hiện bản ghi trùng
- ✓ Null value tracking - Theo dõi giá trị NULL
- ✓ Outlier detection - Phát hiện anomaly
- ✓ Freshness check - Kiểm tra độ tươi của dữ liệu

---

## Best Practices & Recommendations

### Pipeline Design

- ✓ Giữ pipeline nhỏ và tập trung vào một mục đích
- ✓ Sử dụng idempotent operations để hỗ trợ retry
- ✓ Thêm checkpoints cho recovery
- ✓ Giám sát từng stage riêng biệt

### Data Quality

- ✓ Validate dữ liệu sớm (Bronze → Silver)
- ✓ Giữ dữ liệu lịch sử cho audit trail
- ✓ Sử dụng data contracts để định nghĩa schema
- ✓ Tự động phát hiện schema drift

### Performance Optimization

- ✓ Partition dữ liệu theo city, category, date
- ✓ Tạo index trước khi deploy pipeline
- ✓ Sử dụng batch processing cho cập nhật lớn
- ✓ Monitor query performance thường xuyên

### Operational Excellence

- ✓ Automated testing cho mỗi pipeline
- ✓ Centralized logging và monitoring
- ✓ Regular backup và disaster recovery drills
- ✓ Documentation tự động từ pipeline config

---

## Conclusion

**SMART TOURISM DATA PLATFORM** cung cấp một nền tảng mạnh mẽ để xử lý dữ liệu du lịch từ nhiều nguồn khác nhau.

### Điểm mạnh chính:

1. **Kiến trúc State-Machine** cho pipeline lifecycle đảm bảo đáng tin cậy và observability cao

2. **Mô hình Lakehouse ba lớp** (Bronze/Silver/Gold) cho phép tổ chức dữ liệu hiệu quả với mức độ trừu tượng tăng dần

3. **Hỗ trợ toàn diện:**
   - Xử lý dữ liệu tự động
   - Validation chất lượng
   - Recovery từ lỗi
   - Theo dõi lineage
   - Monitoring toàn diện

4. **MongoDB cho flexibility** và khả năng scale
5. **Parquet cho storage hiệu quả** trong lakehouse

### Lợi ích kinh doanh:

Với kiến trúc này, tổ chức có thể:
- ✅ Nhanh chóng xây dựng các ứng dụng du lịch mới
- ✅ Cải thiện chất lượng dữ liệu
- ✅ Tạo ra các tính năng AI/ML mới dựa trên dữ liệu thống nhất
- ✅ Giảm chi phí vận hành
- ✅ Tăng tốc độ phát triển sản phẩm

---

## Appendix: Technology Stack

- **Orchestration:** Apache Airflow
- **Processing:** Apache Spark / Pandas
- **Storage:** S3/GCS (Lakehouse) + MongoDB
- **Data Formats:** JSON (Bronze), Parquet (Silver/Gold)
- **APIs:** FastAPI / REST
- **Search:** Elasticsearch (optional)
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack
- **Deployment:** Docker + Kubernetes

---

**Document Version:** 1.0 | **Created:** May 2026 | **Status:** Final

**For more information, refer to the complete documentation package.**
