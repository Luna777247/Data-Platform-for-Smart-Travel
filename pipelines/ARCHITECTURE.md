# Smart Travel OSM Data Pipeline Architecture

## 🏗️ Overview

Smart Travel OSM Data Pipeline là một hệ thống enterprise-grade data lakehouse architecture được thiết kế để thu thập, xử lý và làm giàu dữ liệu POI (Point of Interest) từ OpenStreetMap và các nguồn khác.

## 📊 Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   OSM API   │  │ Google API  │  │ Manual Data │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                INGESTION LAYER                        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           OSM Ingestion Engine                │ │
│  │  - Async API calls                              │ │
│  │  - Rate limiting                               │ │
│  │  - Error handling                              │ │
│  │  - Metadata extraction                        │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  BRONZE LAYER                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           RAW DATA STORAGE                       │ │
│  │  - Original API responses                     │ │
│  │  - Metadata wrapper                          │ │
│  │  - No transformation                        │ │
│  │  - Immutable storage                         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              VALIDATION & TRANSFORMATION                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Data Validation                       │ │
│  │  - Schema validation                          │ │
│  │  - Quality checks                            │ │
│  │  - Duplicate detection                     │ │
│  │  - Error reporting                          │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Transformation Engine                 │ │
│  │  - Schema standardization                    │ │
│  │  - Data cleaning                            │ │
│  │  - Coordinate normalization                 │ │
│  │  - Category mapping                         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  SILVER LAYER                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         PROCESSED DATA STORAGE                   │ │
│  │  - Standardized schema                        │ │
│  │  - Clean data                                │ │
│  │  - Unified POI model                        │ │
│  │  - JSON format                              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              ENRICHMENT & BUSINESS LOGIC               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Data Enrichment                       │ │
│  │  - Business metrics calculation               │ │
│  │  - Quality scoring                          │ │
│  │  - Search keywords generation                 │ │
│  │  - Region hierarchy                        │ │
│  │  - Embedding text                          │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Deduplication Engine                 │ │
│  │  - Geographic proximity detection            │ │
│  │  - Name similarity matching                 │ │
│  │  - Best record selection                   │ │
│  │  - Duplicate reporting                    │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   GOLD LAYER                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         BUSINESS READY DATA                     │ │
│  │  - Analytics ready                           │ │
│  │  - ML/AI ready                              │ │
│  │  - Search ready                             │ │
│  │  - Parquet format                           │ │
│  │  - Optimized for queries                     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🗂️ Directory Structure

```
pipelines/
├── README.md                    # Pipeline overview
├── ARCHITECTURE.md              # Architecture documentation
├── shared/                      # Shared utilities and schemas
│   ├── schemas.py               # Data models (Bronze, Silver, Gold)
│   └── utils.py                # Common utilities
├── ingestion/                  # Data ingestion modules
│   └── osm_ingestion.py       # OSM API ingestion
├── bronze/                     # Bronze layer processing
│   └── osm_processor.py       # Process raw OSM data
├── silver/                     # Silver layer processing
│   └── silver_processor.py     # Process to Gold layer
├── validators/                 # Data validation
│   └── data_validator.py       # Quality validation
├── orchestration/              # Pipeline orchestration
│   └── pipeline_orchestrator.py # Main controller
└── config/                     # Configuration files
    └── pipeline_config.json    # Pipeline settings
```

## 📊 Data Flow

### 1. Ingestion Phase
- **Input**: OSM API responses
- **Process**: Async API calls with rate limiting
- **Output**: Raw JSON files in Bronze layer
- **Schema**: Original OSM response + metadata wrapper

### 2. Bronze Processing Phase
- **Input**: Raw OSM data from Bronze layer
- **Process**: Schema standardization, data cleaning
- **Output**: Processed JSON files in Silver layer
- **Schema**: Unified POI model

### 3. Silver Processing Phase
- **Input**: Processed data from Silver layer
- **Process**: Business enrichment, deduplication
- **Output**: Business-ready Parquet files in Gold layer
- **Schema**: Enriched POI model with business metrics

### 4. Validation Phase
- **Input**: Data from all layers
- **Process**: Quality checks, validation reporting
- **Output**: Quality reports and metrics

## 🔧 Key Components

### OSM Ingestion Engine
- **Purpose**: Thu thập dữ liệu gốc từ OSM API
- **Features**: 
  - Async processing với rate limiting
  - Error handling và retry logic
  - Metadata extraction
  - Configurable cities và categories

### Bronze Processor
- **Purpose**: Chuyển đổi raw data sang standardized schema
- **Features**:
  - Schema mapping và validation
  - Coordinate normalization
  - Category standardization
  - Data cleaning

### Silver Processor
- **Purpose**: Làm giàu dữ liệu và chuẩn bị cho analytics
- **Features**:
  - Business metrics calculation
  - Duplicate detection và merging
  - Search keywords generation
  - Region hierarchy creation

### Data Validator
- **Purpose**: Đảm bảo chất lượng và consistency
- **Features**:
  - Multi-layer validation
  - Quality scoring
  - Error reporting
  - Performance metrics

### Pipeline Orchestrator
- **Purpose**: Điều phối toàn bộ pipeline
- **Features**:
  - Sequential phase execution
  - Error handling và recovery
  - Progress reporting
  - Configuration management

## 📈 Performance Characteristics

### Scalability
- **Horizontal scaling**: Parallel city processing
- **Batch processing**: Chunked data processing
- **Memory efficiency**: Streaming cho large datasets
- **Async I/O**: Non-blocking API calls

### Reliability
- **Error handling**: Comprehensive error management
- **Retry logic**: Automatic retry với exponential backoff
- **Data validation**: Multi-layer quality checks
- **Monitoring**: Real-time progress tracking

### Maintainability
- **Modular design**: Loosely coupled components
- **Configuration-driven**: External configuration files
- **Type safety**: Pydantic schemas với validation
- **Documentation**: Comprehensive documentation

## 🔍 Data Quality

### Validation Rules
- **Schema validation**: Required fields và type checking
- **Coordinate validation**: Latitude/longitude range checking
- **Name validation**: Length, encoding, character validation
- **Category validation**: Standardized category mapping
- **Duplicate detection**: Geographic proximity và name similarity

### Quality Metrics
- **Completeness score**: Data field completeness
- **Accuracy score**: Coordinate và name accuracy
- **Consistency score**: Cross-field consistency
- **Timeliness score**: Data freshness

## 🚀 Deployment

### Environment Requirements
- **Python**: 3.8+
- **Dependencies**: Pydantic, httpx, pandas, pyarrow
- **Storage**: Local filesystem hoặc cloud storage
- **Memory**: Minimum 4GB RAM cho large datasets

### Configuration
- **Pipeline settings**: JSON configuration files
- **City definitions**: Geographic boundaries
- **Category mappings**: OSM tag mappings
- **Quality thresholds**: Validation parameters

### Monitoring
- **Logging**: Structured logging với levels
- **Metrics**: Performance và quality metrics
- **Reports**: Automated quality reports
- **Alerts**: Error notification system

## 🔄 Future Enhancements

### Scalability
- **Distributed processing**: Multi-node processing
- **Streaming**: Real-time data ingestion
- **Cloud storage**: S3/ADLS integration
- **Caching**: Redis caching cho API responses

### Features
- **ML enrichment**: Automated categorization
- **Image processing**: POI image analysis
- **Social media integration**: Sentiment analysis
- **Real-time updates**: Change detection

### Quality
- **Automated fixing**: Self-healing data
- **Human-in-the-loop**: Manual review workflow
- **Source verification**: Cross-source validation
- **Historical tracking**: Data lineage tracking
