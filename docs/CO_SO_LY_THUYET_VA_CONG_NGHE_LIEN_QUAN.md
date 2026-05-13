# CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LIÊN QUAN
## SMART TOURISM DATA PLATFORM

**Phiên bản:** 1.0  
**Ngày tạo:** 13 tháng 5, 2026  
**Trạng thái:** Hoàn thành

---

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Cơ sở lý thuyết](#2-cơ-sở-lý-thuyết)
   - [Kiến trúc Data Lakehouse](#21-kiến-trúc-data-lakehouse)
   - [Pipeline Metadata-driven](#22-pipeline-metadata-driven)
   - [State Machine Architecture](#23-state-machine-architecture)
   - [Entity Resolution và Deduplication](#24-entity-resolution-và-deduplication)
   - [Data Quality Management](#25-data-quality-management)
3. [Công nghệ liên quan](#3-công-nghệ-liên-quan)
   - [Backend Framework](#31-backend-framework)
   - [Database Systems](#32-database-systems)
   - [Data Processing](#33-data-processing)
   - [APIs và Data Sources](#34-apis-và-data-sources)
   - [Monitoring và Observability](#35-monitoring-và-observability)
   - [Deployment và Infrastructure](#36-deployment-và-infrastructure)
   - [Security](#37-security)
4. [Kiến trúc tổng thể](#4-kiến-trúc-tổng-thể)
5. [Kết luận](#5-kết-luận)

---

## 1. Giới thiệu

**SMART TOURISM DATA PLATFORM** là một hệ thống xử lý dữ liệu du lịch quy mô lớn, được thiết kế dựa trên các nguyên lý kiến trúc hiện đại để tích hợp, xử lý và cung cấp dữ liệu từ nhiều nguồn khác nhau. Tài liệu này trình bày cơ sở lý thuyết và các công nghệ cốt lõi được sử dụng trong việc xây dựng nền tảng.

### Mục tiêu chính

- Tích hợp dữ liệu từ nhiều nguồn du lịch (OpenStreetMap, Google Places, TripAdvisor)
- Đảm bảo chất lượng dữ liệu thông qua pipeline validation
- Tạo ra dữ liệu chuẩn để phục vụ các ứng dụng AI/ML
- Giám sát toàn diện quá trình xử lý dữ liệu
- Tự động phục hồi từ lỗi và đảm bảo tính sẵn sàng cao

---

## 2. Cơ sở lý thuyết

### 2.1 Kiến trúc Data Lakehouse

**Data Lakehouse** là mô hình kiến trúc kết hợp ưu điểm của Data Lake (lưu trữ dữ liệu thô) và Data Warehouse (cấu trúc dữ liệu có schema). Trong SMART TOURISM DATA PLATFORM, kiến trúc này được triển khai theo ba tầng:

#### Bronze Layer (Dữ liệu thô)
- **Mục đích**: Lưu trữ dữ liệu gốc từ các API nguồn
- **Định dạng**: JSON (không chỉnh sửa)
- **Vị trí**: `storage/bronze/{source}/{city}/{category}/raw_{datetime}.json`
- **Thời gian lưu trữ**: 30 ngày
- **Đặc điểm**: Dữ liệu nguyên bản, chưa qua xử lý

#### Silver Layer (Dữ liệu chuẩn)
- **Mục đích**: Dữ liệu đã được chuẩn hóa và kiểm tra schema
- **Định dạng**: Parquet (cột)
- **Vị trí**: `storage/silver/{source}/{city}/{category}/processed_{datetime}.parquet`
- **Thời gian lưu trữ**: 1 năm
- **Đặc điểm**: Schema chuẩn, đã validation, sẵn sàng cho phân tích

#### Gold Layer (Dữ liệu kinh doanh)
- **Mục đích**: Dữ liệu đã làm giàu, gộp từ nhiều nguồn, sẵn sàng cho business
- **Định dạng**: Parquet + MongoDB collections
- **Vị trí**: `storage/gold/{entity}/{city}/` + MongoDB collections
- **Thời gian lưu trữ**: 2+ năm
- **Đặc điểm**: Đã deduplication, entity resolution, business scoring

**Lợi ích của kiến trúc Data Lakehouse:**
- Tách biệt các mức độ chất lượng dữ liệu
- Cho phép rollback về bất kỳ điểm nào
- Bảo toàn audit trail
- Tối ưu hóa cho các use case khác nhau

### 2.2 Pipeline Metadata-driven

**Metadata-driven Pipeline** là phương pháp thiết kế pipeline dựa trên metadata (siêu dữ liệu) thay vì hard-code logic. Trong hệ thống này:

- Pipeline được định nghĩa dưới dạng JSON metadata
- Hỗ trợ dynamic loading và execution
- Plugin-based connectors cho các nguồn dữ liệu khác nhau
- Centralized configuration management

**Ví dụ cấu trúc metadata pipeline:**

```json
{
  "pipeline_name": "osm_tokyo_restaurant",
  "source_name": "osm",
  "stages": ["bronze", "silver", "gold"],
  "stage_config": {
    "bronze": {
      "type": "api_fetch",
      "batch_size": 1000,
      "timeout_sec": 300
    },
    "silver": {
      "type": "normalization",
      "transformations": ["schema_validation", "geo_standardization"],
      "timeout_sec": 600
    },
    "gold": {
      "type": "enrichment",
      "aggregations": ["entity_merge", "deduplication"],
      "timeout_sec": 900
    }
  }
}
```

### 2.3 State Machine Architecture

Pipeline được quản lý theo **State Machine Pattern** với các trạng thái được định nghĩa rõ ràng:

```
CREATED → REGISTERED → SCHEDULED → QUEUED → INITIALIZING → RUNNING
    ↓
VALIDATING → BRONZE_PROCESSING → BRONZE_COMPLETED
    ↓
SILVER_PROCESSING → SILVER_COMPLETED
    ↓
GOLD_PROCESSING → GOLD_COMPLETED → COMPLETED
```

**Lợi ích:**
- Trạng thái chuyển đổi rõ ràng và có thể dự đoán
- Ngăn chặn các thay đổi trạng thái không hợp lệ
- Cho phép resumable executions
- Dễ dàng debugging và monitoring

**Error Handling với Retry Policy:**
- Exponential backoff: 1s, 2s, 4s, 8s...
- Maximum retries: 3 lần
- Automatic recovery từ checkpoint

### 2.4 Entity Resolution và Deduplication

**Entity Resolution** là quá trình xác định và gộp các thực thể trùng lặp từ nhiều nguồn dữ liệu khác nhau.

**Các kỹ thuật sử dụng:**
- Fuzzy matching trên tên và địa chỉ
- Geospatial proximity analysis
- Business logic rules
- Machine learning-based similarity scoring

**Deduplication Process:**
1. **Blocking**: Chia dữ liệu thành các block nhỏ để giảm so sánh
2. **Matching**: So sánh các entity trong cùng block
3. **Merging**: Gộp các entity trùng lặp
4. **Survivorship**: Chọn giá trị tốt nhất cho mỗi field

### 2.5 Data Quality Management

**Data Quality Framework** bao gồm:
- **Schema Validation**: Kiểm tra cấu trúc dữ liệu
- **Business Rules Validation**: Kiểm tra logic nghiệp vụ
- **Completeness Checks**: Đảm bảo dữ liệu đầy đủ
- **Accuracy Validation**: Kiểm tra độ chính xác
- **Timeliness Monitoring**: Giám sát thời gian cập nhật

**Quality Metrics:**
- Record completeness: >95%
- Schema compliance: >99%
- Duplicate rate: <1%
- Geospatial accuracy: ±10m

---

## 3. Công nghệ liên quan

### 3.1 Backend Framework

#### FastAPI
- **Mô tả**: Modern, fast web framework cho Python
- **Phiên bản**: 0.100+
- **Tính năng chính**:
  - Async/await support
  - Automatic OpenAPI documentation
  - Dependency injection
  - Type hints validation
- **Ứng dụng**: REST API endpoints, middleware, authentication

#### Python
- **Phiên bản**: 3.11+
- **Libraries chính**:
  - `pydantic`: Data validation
  - `motor`: Async MongoDB driver
  - `redis`: Redis client
  - `requests`: HTTP client
  - `pandas`: Data processing
  - `geopandas`: Geospatial data

### 3.2 Database Systems

#### MongoDB
- **Mô tả**: NoSQL document database
- **Phiên bản**: 7.0+
- **Collections chính**:
  - `master_poi`: Dữ liệu POI chính
  - `poi_reviews`: Đánh giá và review
  - `pipeline_execution`: Lịch sử thực thi pipeline
  - `data_quality_reports`: Báo cáo chất lượng
- **Indexing Strategy**:
  - Compound indexes cho queries phức tạp
  - Geospatial indexes cho location queries
  - Text indexes cho search functionality

#### Redis
- **Mô tả**: In-memory data structure store
- **Ứng dụng**: Caching, session storage, rate limiting
- **Data Structures**: Strings, Hashes, Lists, Sets, Sorted Sets

### 3.3 Data Processing

#### Apache Parquet
- **Mô tả**: Columnar storage format
- **Lợi ích**: Compression tốt, query performance cao
- **Ứng dụng**: Silver và Gold layer storage

#### Pandas/Geopandas
- **Mô tả**: Data manipulation libraries
- **Ứng dụng**: Data transformation, geospatial processing

### 3.4 APIs và Data Sources

#### OpenStreetMap API
- **Endpoint**: `https://api.openstreetmap.org/api/0.6`
- **Data Types**: POI, Ways, Relations
- **Rate Limit**: 60 requests/minute

#### Google Places API
- **Services**: Places API, Places Details API
- **Data**: Reviews, photos, ratings, business info
- **Authentication**: API Key

#### TripAdvisor API
- **Data**: Hotel reviews, restaurant ratings
- **Integration**: Content API

### 3.5 Monitoring và Observability

#### Prometheus
- **Mô tả**: Metrics collection và alerting
- **Metrics**:
  - Pipeline execution time
  - Data quality scores
  - API response times
  - Error rates

#### Logging
- **Framework**: Python logging
- **Levels**: DEBUG, INFO, WARNING, ERROR
- **Storage**: Structured JSON logs

#### Health Checks
- **Endpoints**: `/health`, `/ready`, `/metrics`
- **Checks**: Database connectivity, Redis availability

### 3.6 Deployment và Infrastructure

#### Docker
- **Containerization**: Multi-stage builds
- **Images**: Python base, MongoDB, Redis
- **Orchestration**: Docker Compose

#### Kubernetes
- **Deployment**: Pod, Service, ConfigMap
- **Scaling**: Horizontal Pod Autoscaler
- **Storage**: Persistent Volumes

#### Terraform
- **Infrastructure as Code**: Azure resources
- **Modules**: Networking, compute, storage

### 3.7 Security

#### JWT Authentication
- **Algorithm**: HS256
- **Token Structure**: Header, Payload, Signature
- **Expiration**: 24 hours
- **Roles**: user, admin

#### Rate Limiting
- **Implementation**: Redis-based
- **Limits**: 60 requests/minute per user

#### CORS
- **Allowed Origins**: Configurable
- **Headers**: Authorization, Content-Type

---

## 4. Kiến trúc tổng thể

```
External Data Sources (OSM, Google Places, TripAdvisor)
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
   MongoDB Collections + Redis Cache
           ↓
   FastAPI REST APIs / Analytics / AI/ML
           ↓
   Monitoring (Prometheus) + Logging
```

**Các thành phần chính:**
1. **Pipeline Orchestration**: Quản lý lifecycle của pipelines
2. **Data Lakehouse**: Ba tầng xử lý dữ liệu
3. **MongoDB**: Primary database cho dữ liệu kinh doanh
4. **Redis**: Caching và session management
5. **FastAPI**: REST API framework
6. **Monitoring Stack**: Prometheus, logging, health checks

---

## 5. Kết luận

SMART TOURISM DATA PLATFORM được xây dựng dựa trên các nguyên lý kiến trúc hiện đại như Data Lakehouse, Metadata-driven Pipelines, và State Machine Architecture. Các công nghệ được chọn (FastAPI, MongoDB, Redis, Docker, Kubernetes) đảm bảo tính scalable, reliable và maintainable của hệ thống.

**Điểm mạnh của kiến trúc:**
- **Scalability**: Xử lý hàng triệu POI records
- **Reliability**: Automatic retry và fault tolerance
- **Data Quality**: Multi-stage validation
- **Observability**: Real-time monitoring
- **Flexibility**: Plugin-based connectors

**Ứng dụng thực tế:**
- Tourism recommendation systems
- Location-based services
- Business intelligence dashboards
- AI/ML model training data
- Mobile applications

Tài liệu này cung cấp nền tảng lý thuyết và kỹ thuật để hiểu và phát triển SMART TOURISM DATA PLATFORM.