# Smart Tourism Platform - Refactored

Production-ready transition from PHP to FastAPI with multi-city data collection.

## 🚀 Changes Overview

1. **Backend Migration**: PHP Slim replaced with FastAPI for better performance and Python ecosystem integration.
2. **Unified Data Model**: Standardized schema for Attractions, Restaurants, and Hotels.
3. **Multi-City Collector**: Refactored OSM collector supporting Hanoi, HCM, and Da Nang.
4. **Intelligent Enrichment**: Google Places integration with key rotation and quota management.
5. **Dynamic Orchestration**: Airflow DAGs that auto-generate tasks for every city-type combination.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (Async via Motor)
- **Orchestration**: Apache Airflow
- **Data Sources**: OpenStreetMap (Overpass API), Google Places (RapidAPI)

## 🛠️ Getting Started

```bash
# Clone and setup env
copy .env.example .env

# Start the stack
docker-compose up --build
```

## 📡 API Endpoints (v2)

- `GET /places`: List all places with pagination/filters
- `GET /stats`: Global statistics
- `GET /top-rated`: Highest rated places
- `POST /pipeline/run`: Trigger data collection

## 📊 Sample Response (GET /places)

```json
[
  {
    "id": "671a...",
    "name": "Lăng Chủ tịch Hồ Chí Minh",
    "type": "attraction",
    "city": "hanoi",
    "address": "2 Hùng Vương, Điện Biện, Ba Đình, Hà Nội",
    "rating": 4.8,
    "reviews": 15000,
    "location": {"lat": 21.0368, "lon": 105.8347},
    "source": "google",
    "last_updated": "2026-04-24T12:00:00Z"
  }
]
```
