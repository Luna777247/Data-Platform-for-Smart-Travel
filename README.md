# Smart Tourism Data Platform 🌍
# Nền Tảng Dữ Liệu Du Lịch Thông Minh

> **Enterprise-grade data platform for smart tourism applications**
> **Nền tảng dữ liệu cấp doanh nghiệp cho ứng dụng du lịch thông minh**
> 
> Built with FastAPI, MongoDB, Redis, and modern data engineering practices.
> Xây dựng với FastAPI, MongoDB, Redis và các phương pháp kỹ thuật dữ liệu hiện đại.

<!-- Các badge hiển thị thông tin công nghệ sử dụng -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47a248.svg)](https://www.mongodb.com)
[![Redis](https://img.shields.io/badge/Redis-7.0+-dc382d.svg)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed.svg)](https://www.docker.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents
## 📋 Mục Lục

<!-- Liên kết đến các phần chính của tài liệu -->
- [Overview](#overview) - Tổng quan
- [Architecture](#architecture) - Kiến trúc
- [Features](#features) - Tính năng
- [Quick Start](#quick-start) - Bắt đầu nhanh
- [Installation](#installation) - Cài đặt
- [Configuration](#configuration) - Cấu hình
- [API Documentation](#api-documentation) - Tài liệu API
- [Development](#development) - Phát triển
- [Deployment](#deployment) - Triển khai
- [Monitoring](#monitoring) - Giám sát
- [Contributing](#contributing) - Đóng góp

---

## 🎯 Overview
## 🎯 Tổng Quan

<!-- Giới thiệu về dự án và mục tiêu -->
Smart Tourism Data Platform là hệ thống data platform enterprise-grade được thiết kế để thu thập, xử lý và phục vụ dữ liệu du lịch thông minh. Hệ thống sử dụng kiến trúc **Hybrid Storage** với:
- **🥉 Bronze Layer**: MinIO Object Storage (raw JSON files)
- **🥈 Silver Layer**: MongoDB (cleaned & normalized)  
- **🥇 Gold Layer**: MongoDB (enriched & production-ready)

### Key Capabilities
### Khả Năng Chính

<!-- Liệt kê các tính năng và khả năng cốt lõi của hệ thống -->
- 🗺️ **POI Data Collection**: Tự động thu thập điểm đến (POI - Point of Interest) từ OpenStreetMap API và Google Places API
- 🔄 **Data Pipeline**: ETL pipeline xử lý dữ liệu qua 3 lớp Bronze → Silver → Gold với data quality checks
- 🚀 **REST API**: FastAPI endpoints cho real-time data serving với async/await support
- 📊 **Monitoring**: Prometheus metrics + Grafana dashboards cho hệ thống observability
- 🔐 **Security**: JWT authentication, role-based access control (RBAC), CORS, và rate limiting
- 🐳 **Cloud-Native**: Docker containerization, Kubernetes ready, horizontal scaling support
- 📝 **Structured Logging**: JSON format logs với correlation ID tracking
- 🧪 **Testing**: Comprehensive unit tests và integration tests với pytest

---

## 🏗️ Architecture
## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   FastAPI   │  │    JWT      │  │  Pipeline Management    │  │
│  │   Server    │  │    Auth     │  │       REST API          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Pipeline   │  │    POI      │  │    Data Validation    │  │
│  │  Service    │  │   Service   │  │       Service         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   MongoDB   │  │    Redis    │  │    MinIO                │  │
│  │   (Main)    │  │   (Cache)   │  │  (Bronze Storage)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│  MongoDB Collections:           MinIO Buckets:                  │
│  • silver_pois                  • smart-travel-bronze           │
│  • gold_master_pois                                             │
│  • places, users, tours                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Pipeline Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Bronze    │  │   Silver    │  │    Gold                 │  │
│  │   (MinIO)   │  │  (MongoDB)  │  │   (MongoDB)             │  │
│  │  Raw JSON   │  │  Cleaned    │  │   Enriched              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **API** | FastAPI, Pydantic, Uvicorn |
| **Database** | MongoDB (Motor), Redis |
| **Processing** | Pandas, NumPy, Celery |
| **External APIs** | OpenStreetMap, Google Places |
| **Monitoring** | Prometheus, Grafana, Sentry |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## ✨ Features

### Data Collection
- ✅ Multi-source POI ingestion (OSM, Google Places)
- ✅ Async HTTP operations với rate limiting
- ✅ Configurable cities và categories
- ✅ Automatic retry và error handling

### Data Processing
- ✅ 3-layer Lakehouse architecture (Bronze/Silver/Gold)
- ✅ Data deduplication và merging
- ✅ Quality scoring và validation
- ✅ Business metrics calculation

### API & Serving
- ✅ 14 REST API endpoints
- ✅ JWT authentication
- ✅ OpenAPI/Swagger documentation
- ✅ Rate limiting và CORS
- ✅ Request/response validation

### Operations
- ✅ Structured JSON logging
- ✅ Prometheus metrics
- ✅ Health checks
- ✅ Docker containerization
- ✅ Background task workers (Celery)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB 7.0+
- Redis 7.0+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/smart-tourism-platform.git
cd smart-tourism-platform

# Copy environment file
cp .env.example .env
# Edit .env với your actual values

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Access API docs
open http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env với MongoDB/Redis connection strings

# Run development server
python src/main.py

# Or with hot reload
uvicorn src.main:app --reload --port 8000
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` và thay đổi các giá trị:

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | Yes | MongoDB connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET` | Yes | JWT signing secret |
| `ENVIRONMENT` | No | development/staging/production |
| `LOG_LEVEL` | No | DEBUG/INFO/WARNING/ERROR |

### Data Sources

Configure trong `storage/configs/`:

- `cities.json`: City definitions với bounding boxes
- `poi_types.json`: POI category mappings
- `osm_settings.json`: Overpass API settings

---

## 📚 API Documentation

### Authentication

```bash
# Get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token trong requests
curl http://localhost:8000/api/v1/pipeline/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Pipeline Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/start` | Khởi động pipeline |
| POST | `/api/v1/pipeline/stop/{id}` | Dừng pipeline |
| GET | `/api/v1/pipeline/status/{id}` | Lấy status |
| GET | `/api/v1/pipeline/history` | Lịch sử executions |
| GET | `/api/v1/pipeline/dashboard` | Dashboard data |
| GET | `/api/v1/pipeline/metrics` | Performance metrics |
| GET | `/api/v1/health` | Health check |

#### NEW: MinIO + MongoDB Pipeline Endpoints (May 2026)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/bronze/collect` | Collect to MinIO (Bronze) |
| POST | `/api/v1/pipeline/bronze/mass-collect` | Mass collection to MinIO |
| GET | `/api/v1/pipeline/bronze/list` | List Bronze records |
| GET | `/api/v1/pipeline/bronze/stats` | Bronze layer statistics |
| POST | `/api/v1/pipeline/bronze-to-silver` | Transform → MongoDB |
| POST | `/api/v1/pipeline/silver-to-gold` | Enrich → Gold layer |
| POST | `/api/v1/pipeline/run-full-pipeline` | Bronze → Silver → Gold |
| GET | `/api/v1/pipeline/layers/stats` | All layers statistics |

### API Documentation URLs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

---

## 💻 Development

### Project Structure

```
smart-tourism-platform/
├── src/                      # Source code
│   ├── core/                # Core infrastructure
│   ├── db/models/            # Database models
│   ├── services/             # Business logic
│   ├── api/                  # API layer
│   └── main.py              # Application entry
├── pipelines/               # Data processing
│   ├── ingestion/           # Data ingestion
│   ├── bronze/              # Bronze layer
│   ├── silver/               # Silver layer
│   ├── validators/            # Data validation
│   └── shared/               # Shared utilities
├── deployment/               # Deployment configs
├── tests/                     # Test files
├── docs/                       # Documentation
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Local orchestration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run với coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_pipeline.py
```

### Code Style

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint
flake8 src/

# Type check
mypy src/
```

---

## 🚢 Deployment

### Docker Build

```bash
# Build image
docker build -t smart-tourism-api:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  smart-tourism-api:latest
```

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate strong JWT secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS origins
- [ ] Enable rate limiting
- [ ] Setup monitoring (Sentry, Datadog)
- [ ] Configure backups
- [ ] Setup log rotation
- [ ] Review security headers

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n smart-tourism
```

---

## 📊 Monitoring

### Prometheus Metrics

Access Prometheus at `http://localhost:9090`

Key metrics:
- `pipeline_executions_total`: Số pipeline runs
- `pipeline_duration_seconds`: Thời gian thực thi
- `api_requests_total`: API request count
- `api_request_duration_seconds`: API latency

### Grafana Dashboards

Access Grafana at `http://localhost:3001`

Default credentials: `admin/admin123` (đổi ngay!)

Pre-built dashboards:
- API Performance
- Pipeline Status
- System Resources
- Data Quality

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/ready
```

---

## 🤝 Contributing

### Development Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Coding Standards

- Python 3.11+ type hints
- Pydantic models cho data validation
- Async/await cho I/O operations
- Comprehensive error handling
- Detailed comments và docstrings
- pytest cho testing

### Commit Messages

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example: `feat(pipeline): add retry mechanism for OSM ingestion`

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Motor](https://motor.readthedocs.io) - Async MongoDB driver
- [Pydantic](https://docs.pydantic.dev) - Data validation
- [OpenStreetMap](https://www.openstreetmap.org) - POI data source

---

## 📞 Support

- 📧 Email: support@smarttravel.vn
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/smart-tourism-platform/issues)
- 📖 Wiki: [GitHub Wiki](https://github.com/your-org/smart-tourism-platform/wiki)

---

**Built with ❤️ by the Smart Tourism Team**
