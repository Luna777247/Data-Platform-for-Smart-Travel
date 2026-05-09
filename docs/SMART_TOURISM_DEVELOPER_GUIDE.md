# SMART TOURISM DATA PLATFORM
## Developer & Architecture Guide

**Version:** 1.0  
**Last Updated:** May 2026  
**Status:** Final

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [Pipeline Lifecycle](#3-pipeline-lifecycle)
4. [Workflow Patterns](#4-workflow-patterns)
5. [Data Lakehouse Design](#5-data-lakehouse-design)
6. [Database Schema](#6-database-schema)
7. [Query Patterns](#7-query-patterns)
8. [Deployment Guide](#8-deployment-guide)
9. [Troubleshooting](#9-troubleshooting)
10. [API Reference](#10-api-reference)

---

## 1. System Overview

### 1.1 What is SMART TOURISM DATA PLATFORM?

SMART TOURISM DATA PLATFORM is a metadata-driven data integration and processing system that:

- **Integrates** data from multiple tourism sources (OSM, Google Places, TripAdvisor)
- **Validates** data quality at each processing stage
- **Transforms** raw data into business-ready information
- **Deduplicates** entities across sources
- **Monitors** pipeline execution with full observability
- **Recovers** automatically from failures

### 1.2 Core Use Cases

```
1. POI Data Unification
   Multiple Sources → Canonical POI → Master Data

2. Real-time Data Enrichment
   Review Aggregation → Rating Calculation → Popularity Score

3. Data Quality Management
   Validation → Quality Reports → Alerting

4. AI/ML Feature Engineering
   Clean Data → Embeddings → Recommendation Models
```

### 1.3 Key Components

```
┌─────────────────────────────────────────────┐
│     SMART TOURISM DATA PLATFORM            │
├─────────────────────────────────────────────┤
│ • Pipeline Orchestration Engine             │
│ • Metadata-driven Configuration             │
│ • Dynamic State Machine Executor            │
│ • Data Lakehouse (Bronze/Silver/Gold)      │
│ • MongoDB Collections & Indexes             │
│ • Quality Monitoring & Observability       │
│ • Automatic Retry & Recovery               │
└─────────────────────────────────────────────┘
```

---

## 2. Architecture Principles

### 2.1 Design Patterns

#### State Machine Pattern
```
Each pipeline execution follows a strict state machine:
CREATED → REGISTERED → SCHEDULED → QUEUED → INITIALIZING
    ↓
RUNNING → VALIDATING → BRONZE → SILVER → GOLD → COMPLETED
```

**Benefits:**
- Clear state transitions
- Prevents invalid state changes
- Enables resumable executions
- Facilitates debugging

#### Lakehouse Pattern
```
Bronze Layer (Raw)
    ↓ (Schema Validation, Normalization)
Silver Layer (Clean)
    ↓ (Enrichment, Deduplication)
Gold Layer (Business-Ready)
    ↓ (AI/ML, Analytics, APIs)
```

**Benefits:**
- Separates concerns
- Enables rollback to any point
- Clear data quality levels
- Audit trail preservation

#### Plugin Pattern
```
PipelineRegistry
    ↓
SourceConnector Interface
    ↓
Pluggable Connectors (OSM, Google, TripAdvisor)
```

**Benefits:**
- Easy to add new sources
- Consistent interface
- Reusable connector logic

### 2.2 Non-Functional Requirements

| Requirement | Target | Implementation |
|-------------|--------|-----------------|
| **Availability** | 99.9% | Distributed scheduling, auto-retry |
| **Scalability** | Millions of POI | Partitioned storage, distributed processing |
| **Data Quality** | >99% | Multi-stage validation, quality reports |
| **Recovery Time** | <30 min | Checkpoint-based recovery |
| **Observability** | Real-time | Prometheus, logs, traces |

---

## 3. Pipeline Lifecycle

### 3.1 Execution States

```
State Machine Transitions:

CREATED
  ↓ (Metadata loaded)
REGISTERED
  ↓ (Schedule validated)
SCHEDULED
  ↓ (Trigger received)
QUEUED
  ↓ (Resources allocated)
INITIALIZING
  ↓ (Connectors prepared)
RUNNING
  ├→ VALIDATING (Schema check)
  ├→ BRONZE_PROCESSING (Raw fetch)
  ├→ BRONZE_COMPLETED
  ├→ SILVER_PROCESSING (Transform)
  ├→ SILVER_COMPLETED
  ├→ GOLD_PROCESSING (Enrich)
  ├→ GOLD_COMPLETED
  └→ COMPLETED (Success)

Error Handling:
Any Stage FAILED
  ↓
RETRY_PENDING (Check retry policy)
  ↓
RETRYING (Attempt again)
  ↓
RECOVERED (Success)
OR
FAILED_PERMANENTLY (Max retries exceeded)
```

### 3.2 Retry Policy

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

### 3.3 Checkpoint Management

```
Pipeline Execution Flow:
Start
  → Create checkpoint (execution_id, timestamp)
  → Execute Bronze stage
  → Checkpoint: Bronze completed
  → Execute Silver stage
  → Checkpoint: Silver completed
  → Execute Gold stage
  → Checkpoint: Gold completed
  → Mark COMPLETED
```

If failure occurs between checkpoints, resume from last checkpoint.

### 3.4 Metadata Tracking

Every execution records:

```javascript
{
  "execution_id": "exec_20260508_120000",
  "pipeline_name": "osm_pipeline",
  "source_name": "osm",
  "status": "RUNNING",
  "current_stage": "silver",
  "started_at": "2026-05-08T10:00:00Z",
  "updated_at": "2026-05-08T10:05:00Z",
  
  "records": {
    "total_processed": 15000,
    "successfully_processed": 14968,
    "failed": 32,
    "error_rate": 0.21
  },
  
  "timing": {
    "bronze_duration_ms": 120000,
    "silver_duration_ms": 180000,
    "gold_duration_ms": 60000,
    "total_duration_ms": 360000
  },
  
  "artifacts": {
    "bronze_location": "s3://bucket/bronze/osm/2026-05-08/",
    "silver_location": "s3://bucket/silver/osm/2026-05-08/",
    "gold_location": "s3://bucket/gold/master_poi/2026-05-08/"
  },
  
  "performance": {
    "memory_peak_mb": 2048,
    "cpu_avg_percent": 65,
    "throughput_rps": 41.7
  }
}
```

---

## 4. Workflow Patterns

### 4.1 OSM Pipeline Workflow

```
Input: OSM API
└→ Raw Fetch
   └→ Bronze Storage (raw_20260508_120000.json)
   └→ Schema Validation
   └→ Normalization (standardize field names, formats)
   └→ Silver Transformation (generate canonical fields)
   └→ Deduplication (group by name, location)
   └→ Silver Storage (processed_20260508_120000.parquet)
   └→ Gold Aggregation (aggregate ratings, counts)
   └→ Master POI Update
Output: Updated master_poi collection
```

### 4.2 Google Places Enrichment Workflow

```
Input: Silver OSM POI
└→ Google Matching Engine
   └→ Find matching POI in Google Places
   └→ Fetch Details (Google Places API)
   └→ Extract: reviews, ratings, photos, hours
   └→ Bronze Storage (google data)
   └→ Transform to Silver schema
   └→ Merge with OSM data
   └→ Calculate business scores
   └→ Update master_poi with enriched data
Output: Enhanced master_poi
```

### 4.3 Multi-Source Unification Workflow

```
Input: Silver data from multiple sources
├→ OSM Silver POI
├→ Google Silver POI
└→ TripAdvisor Silver POI

Processing:
├→ Entity Resolution
│  └→ Find duplicate entities (same location, similar names)
│  └→ Create equivalence groups
├→ Deduplication
│  └→ Select canonical entity
│  └→ Preserve source references
├→ Enrichment
│  └→ Aggregate ratings from all sources
│  └→ Calculate weighted scores
│  └→ Combine reviews
├→ Validation
│  └→ Verify data completeness
│  └→ Check for conflicts
└→ Master POI Update
   └→ Update unified master_poi record
   └→ Store source lineage
   └→ Record last_verified_at

Output: Gold master_poi with unified data
```

---

## 5. Data Lakehouse Design

### 5.1 Three-Layer Architecture

#### Bronze Layer (Raw)
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
  "checksum_sha256": "abc123...",
  "query_params": { "bbox": "..." }
}
```

#### Silver Layer (Processed)
```
Purpose: Standardized, validated data
Format: Parquet (columnar)
Location: storage/silver/{source}/{city}/{category}/processed_{datetime}.parquet
Retention: 1 year

Example: storage/silver/osm/tokyo/restaurant/processed_20260508_120000.parquet

Schema:
{
  "poi_id": "string",
  "name": "string",
  "latitude": "double",
  "longitude": "double",
  "category": "string",
  "rating": "float",
  "review_count": "integer",
  "opening_hours": "string",
  "phone": "string",
  "website": "string"
}

Metadata:
{
  "stage": "silver",
  "record_count": 1468,
  "validation_passed": 1468,
  "validation_failed": 32,
  "transformations_applied": ["normalize", "validate", "deduplicate"],
  "data_quality_score": 0.98
}
```

#### Gold Layer (Business-Ready)
```
Purpose: Unified, enriched, indexed data
Format: Parquet + MongoDB
Location: storage/gold/{entity_type}/{city}/

Example: storage/gold/master_poi/tokyo/master_poi_tokyo_20260508.parquet

Contents:
├→ master_poi_tokyo_20260508.parquet
│  └→ Unified POI data with all sources
├→ poi_reviews_tokyo_20260508.parquet
│  └→ Aggregated reviews
├→ poi_metadata_tokyo_20260508.parquet
│  └→ Processing metadata
├→ quality_report_tokyo_20260508.parquet
│  └→ Quality metrics
└→ MongoDB Collections (indexes, search)
   └→ master_poi
   └→ poi_reviews
   └→ poi_categories

Features:
- Full-text search indexes
- Geospatial 2dsphere indexes
- Composite indexes for common filters
- TTL indexes for cleanup
```

### 5.2 Data Partitioning Strategy

```
Partition Keys: [city, category, date]

Example:
storage/gold/master_poi/
├── tokyo/
│   ├── restaurant/
│   │   ├── 2026-05-08/
│   │   ├── 2026-05-07/
│   │   └── ...
│   ├── hotel/
│   └── ...
├── osaka/
├── kyoto/
└── ...

Benefits:
- Parallel processing by city
- Fast pruning by category
- Time-series queries optimized
- Efficient partitioning for Spark
```

---

## 6. Database Schema

### 6.1 Collection: master_poi

```javascript
// Create master_poi collection
db.createCollection("master_poi", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["poi_id", "name", "location"],
      properties: {
        poi_id: { bsonType: "string" },
        name: { bsonType: "string" },
        city: { bsonType: "string" },
        country: { bsonType: "string" },
        category: { bsonType: "string" },
        location: {
          bsonType: "object",
          required: ["type", "coordinates"],
          properties: {
            type: { enum: ["Point"] },
            coordinates: { bsonType: "array" }
          }
        },
        rating: {
          bsonType: "object",
          properties: {
            overall: { bsonType: "double" },
            osm: { bsonType: ["double", "null"] },
            google: { bsonType: ["double", "null"] },
            tripadvisor: { bsonType: ["double", "null"] }
          }
        },
        sources: { 
          bsonType: "array",
          items: { bsonType: "string" }
        },
        updated_at: { bsonType: "date" }
      }
    }
  }
})

// Create indexes
db.master_poi.createIndex({ poi_id: 1 }, { unique: true })
db.master_poi.createIndex({ location: "2dsphere" })
db.master_poi.createIndex({ name: "text", search_keywords: "text" })
db.master_poi.createIndex({ city: 1, category: 1 })
db.master_poi.createIndex({ rating: -1, review_count: -1 })
```

### 6.2 Collection: pipeline_execution

```javascript
db.createCollection("pipeline_execution", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["execution_id", "pipeline_name"],
      properties: {
        execution_id: { bsonType: "string" },
        pipeline_name: { bsonType: "string" },
        status: {
          enum: ["CREATED", "SCHEDULED", "RUNNING", "COMPLETED", "FAILED"]
        },
        started_at: { bsonType: "date" },
        records: {
          bsonType: "object",
          properties: {
            total_processed: { bsonType: "int" },
            successfully_processed: { bsonType: "int" },
            failed: { bsonType: "int" }
          }
        }
      }
    }
  }
})

// Create indexes
db.pipeline_execution.createIndex({ execution_id: 1 }, { unique: true })
db.pipeline_execution.createIndex({ status: 1, started_at: -1 })
db.pipeline_execution.createIndex({ pipeline_name: 1, started_at: -1 })
```

---

## 7. Query Patterns

### 7.1 Geographic Queries

```javascript
// Find POI within 5km radius
db.master_poi.find({
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [139.7454, 35.6586]  // Tokyo Tower
      },
      $maxDistance: 5000  // meters
    }
  }
}).limit(10)

// Find POI in bounding box
db.master_poi.find({
  location: {
    $geoWithin: {
      $box: [
        [139.7, 35.6],  // Southwest corner
        [139.8, 35.7]   // Northeast corner
      ]
    }
  }
})
```

### 7.2 Full-Text Search

```javascript
// Search by text
db.master_poi.find(
  { $text: { $search: "tokyo tower restaurant" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })
.limit(20)

// Multi-language search
db.master_poi.find({
  $text: { 
    $search: "塔 タワー",  // Japanese
    $language: "ja"
  }
})
```

### 7.3 Aggregation Pipeline

```javascript
// Category statistics
db.master_poi.aggregate([
  { $match: { city: "tokyo", rating: { $gte: 4.0 } } },
  { $group: {
      _id: "$category",
      count: { $sum: 1 },
      avg_rating: { $avg: "$rating.overall" },
      max_review_count: { $max: "$review_count" },
      cities: { $addToSet: "$city" }
    }
  },
  { $sort: { count: -1 } },
  { $limit: 10 }
])

// Time-series aggregation
db.pipeline_execution.aggregate([
  { $match: { status: "COMPLETED", started_at: {
      $gte: new Date("2026-05-01")
    }}
  },
  { $group: {
      _id: {
        pipeline: "$pipeline_name",
        date: { $dateToString: {
          format: "%Y-%m-%d",
          date: "$started_at"
        }}
      },
      count: { $sum: 1 },
      avg_duration: { $avg: "$duration_ms" },
      total_records: { $sum: "$records.total_processed" }
    }
  },
  { $sort: { "_id.date": -1 } }
])
```

### 7.4 Complex Filtering

```javascript
// Filter with multiple conditions
db.master_poi.find({
  city: "tokyo",
  category: "restaurant",
  rating: { $gte: 4.0 },
  review_count: { $gte: 100 },
  sources: { $in: ["osm", "google_places"] },
  tags: { $all: ["photo_spot", "tourist"] },
  business_score: { $gte: 0.8 }
}).sort({
  business_score: -1,
  rating: -1
}).limit(50)
```

---

## 8. Deployment Guide

### 8.1 Prerequisites

```bash
# System Requirements
- MongoDB 5.0+
- Python 3.9+
- Node.js 16+ (for pipeline scheduler)
- Docker (for containerization)
- Kubernetes (optional, for orchestration)

# Installation
pip install pymongo pandas spark pydantic
npm install -g airflow
```

### 8.2 Pipeline Registration

```python
from pymongo import MongoClient
import json

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["smart_travel"]

# Register new pipeline
pipeline_config = {
    "pipeline_name": "osm_pipeline",
    "source_name": "osm",
    "enabled": True,
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
    "schedule": "0 */6 * * *"  # Every 6 hours
}

db.pipeline_registry.insert_one(pipeline_config)
print("Pipeline registered successfully!")
```

### 8.3 Connector Implementation

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import requests

class SourceConnector(ABC):
    """Base class for source connectors"""
    
    def __init__(self, source_config: Dict[str, Any]):
        self.endpoint = source_config["api_endpoint"]
        self.rate_limit = source_config["rate_limit"]
    
    @abstractmethod
    def fetch(self, params: Dict) -> List[Dict]:
        """Fetch data from source"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict) -> bool:
        """Validate data structure"""
        pass

class OSMConnector(SourceConnector):
    """OpenStreetMap connector"""
    
    def fetch(self, bbox: str, amenity: str) -> List[Dict]:
        params = {
            "bbox": bbox,
            "amenity": amenity,
            "format": "json"
        }
        response = requests.get(self.endpoint, params=params)
        return response.json().get("elements", [])
    
    def validate(self, data: Dict) -> bool:
        required_fields = ["id", "lat", "lon", "tags"]
        return all(field in data for field in required_fields)

class GooglePlacesConnector(SourceConnector):
    """Google Places connector"""
    
    def fetch(self, poi_name: str, location: tuple) -> Dict:
        params = {
            "query": poi_name,
            "location": f"{location[0]},{location[1]}",
            "radius": 1000,
            "key": self.api_key
        }
        response = requests.get(
            f"{self.endpoint}/textsearch/json",
            params=params
        )
        return response.json()
    
    def validate(self, data: Dict) -> bool:
        return "results" in data and len(data["results"]) > 0
```

### 8.4 Running Pipelines

```bash
# Start pipeline orchestrator
python orchestrator.py \
  --config pipeline_registry \
  --log-level DEBUG

# Trigger manual pipeline execution
python execute.py \
  --pipeline osm_pipeline \
  --execution-id exec_20260508_120000

# Monitor execution
python monitor.py \
  --execution-id exec_20260508_120000 \
  --watch

# Check execution history
python history.py \
  --pipeline osm_pipeline \
  --limit 10
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue:** Pipeline stuck in RUNNING state

```bash
# Check execution status
db.pipeline_execution.find({
  execution_id: "exec_...",
  status: "RUNNING",
  started_at: { $lte: new Date(Date.now() - 3600000) }  # older than 1 hour
})

# Force state transition
db.pipeline_execution.updateOne(
  { execution_id: "exec_..." },
  { $set: { 
      status: "FAILED",
      error_message: "Forced timeout"
    }
  }
)
```

**Issue:** High error rate in Silver stage

```bash
# Check data quality report
db.data_quality_reports.findOne({
  execution_id: "exec_...",
  stage: "silver"
}, { sort: { report_date: -1 } })

# Identify problematic records
db.pipeline_logs.find({
  execution_id: "exec_...",
  stage: "silver",
  severity: "error"
}).limit(10)
```

**Issue:** Out of memory during Gold processing

```bash
# Check resource usage
db.pipeline_stage_execution.findOne({
  execution_id: "exec_...",
  stage_name: "gold"
})

// Solution: Increase batch size or add more workers
db.pipeline_registry.updateOne(
  { pipeline_name: "osm_pipeline" },
  { $set: { "stage_config.gold.batch_size": 500 } }
)
```

### 9.2 Performance Tuning

```javascript
// Analyze slow queries
db.setProfilingLevel(2)

// Review query plans
db.master_poi.find({ city: "tokyo" }).explain("executionStats")

// Add missing indexes if needed
db.master_poi.createIndex({ city: 1, updated_at: -1 })

// Compact collection
db.runCommand({ compact: "master_poi" })
```

---

## 10. API Reference

### 10.1 Pipeline Execution API

```
POST /api/v1/pipelines/{pipeline_name}/execute
Create execution

POST /api/v1/executions/{execution_id}/retry
Retry failed execution

GET /api/v1/executions/{execution_id}
Get execution status

GET /api/v1/pipelines/{pipeline_name}/history
Get execution history

DELETE /api/v1/executions/{execution_id}
Cancel execution
```

### 10.2 Data Query API

```
GET /api/v1/poi/search?q={query}
Full-text search

GET /api/v1/poi/nearby?lat={lat}&lng={lng}&radius={radius}
Geographic search

GET /api/v1/poi/{poi_id}
Get POI details

GET /api/v1/poi/{poi_id}/reviews
Get POI reviews
```

### 10.3 Monitoring API

```
GET /api/v1/metrics/execution/{execution_id}
Get execution metrics

GET /api/v1/metrics/pipeline/{pipeline_name}
Get pipeline metrics

GET /api/v1/health
Health check
```

---

## Quick Reference

### MongoDB Connection String
```
mongodb://user:password@localhost:27017/smart_travel?authSource=admin
```

### Pipeline Configuration Template
```json
{
  "pipeline_name": "new_pipeline",
  "source_name": "source_name",
  "enabled": true,
  "stages": ["bronze", "silver", "gold"],
  "retry_policy": {
    "max_retry": 3,
    "backoff_type": "exponential"
  },
  "schedule": "0 0 * * *"
}
```

### Environment Variables
```bash
MONGO_URI=mongodb://localhost:27017/smart_travel
STORAGE_PATH=/data/smart_tourism
LOG_LEVEL=INFO
API_PORT=8000
```

---

**For more information, contact the Data Engineering team.**
