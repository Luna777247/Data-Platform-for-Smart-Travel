# Smart Travel Data Pipeline Architecture

## 📊 Data Lakehouse Architecture

```
Raw Ingestion
    ↓
Bronze Storage (Raw Data)
    ↓
Data Validation
    ↓
Transformation Engine
    ↓
Schema Standardization
    ↓
Deduplication
    ↓
Silver Storage (Processed Data)
    ↓
Business Enrichment
    ↓
Gold Storage (Business Ready Data)
```

## 🗂️ Directory Structure

```
pipelines/
├── ingestion/          # Raw data ingestion from APIs
├── bronze/             # Bronze layer processing
├── silver/             # Silver layer processing  
├── gold/               # Gold layer processing
├── validators/         # Data validation modules
├── transformers/       # Data transformation modules
├── enrichers/         # Business enrichment modules
├── exporters/          # Data export modules
├── shared/             # Shared utilities
└── config/             # Pipeline configuration
```

## 🏗️ Layer Definitions

### Bronze Layer - Raw Data
- **Purpose**: Store original API responses without transformation
- **Format**: Raw OSM API response with metadata wrapper
- **Structure**: `storage/bronze/osm/{city}/{category}/raw_YYYYMMDD_HHMMSS.json`
- **Schema**: Original OSM response + metadata

### Silver Layer - Processed Data  
- **Purpose**: Standardized schema across all cities/countries
- **Format**: Canonical POI schema
- **Structure**: `storage/silver/osm/{city}/{category}/processed_YYYYMMDD_HHMMSS.json`
- **Schema**: Unified POI model

### Gold Layer - Business Ready Data
- **Purpose**: Business-enriched data for analytics and AI
- **Format**: Optimized for queries and ML
- **Structure**: `storage/gold/osm/` with parquet files
- **Schema**: Business model with enrichment

## 🚀 Pipeline Features

- **Unified Schema**: Consistent data model across all sources
- **Data Quality**: Validation and quality checks
- **Deduplication**: Smart duplicate detection
- **Enrichment**: Business metrics and scoring
- **Scalability**: Batch and streaming support
- **Monitoring**: Pipeline health and metrics
