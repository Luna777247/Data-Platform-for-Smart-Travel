# Smart Travel Data Platform

A comprehensive data platform for collecting, processing, and analyzing travel destination information (POI - Points of Interest) across Vietnam and Southeast Asia. Built with modern microservices architecture using FastAPI, Next.js, MongoDB, and Apache Airflow.

## 🎯 Project Overview

**Smart Travel Data Platform** is an enterprise-grade solution that enables travel companies to:
- 🗺️ **Collect** POI data from multiple sources (OSM, Google Places API)
- 🔄 **Process** data through Bronze → Silver → Gold layer pipeline
- 📊 **Analyze** travel data with advanced dashboards and visualizations
- 🤖 **Enrich** data using AI-powered deduplication and categorization
- 🚀 **Serve** real-time APIs for travel applications and services

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                    │
│              Port 3000 - React Components                   │
└──────────────┬────────────────────────────────────┬─────────┘
               │                                    │
┌──────────────▼────────────────┐    ┌─────────────▼──────────┐
│   Backend (FastAPI Python)    │    │  Airflow (Scheduler)   │
│      Port 8000 - REST API     │    │   Port 8080            │
│   Controller → Service →      │    │ - Task scheduling      │
│   Repository Pattern          │    │ - DAG management       │
└──────────────┬────────────────┘    └─────────────┬──────────┘
               │                                    │
┌──────────────┴────────────────┬───────────────────┴──────────┐
│                                │                             │
│   ┌─────────────────────────────┴──────────┐                 │
│   │   MongoDB Atlas (Cloud Database)       │                 │
│   │   - smart_travel.places (4,972+ docs) │                 │
│   │   - api_connections                    │                 │
│   │   - api_schedules                      │                 │
│   │   - api_runs                           │                 │
│   └────────────────────────────────────────┘                 │
│                                                              │
│   ┌─────────────────────────────┬──────────┐                 │
│   │  PostgreSQL                 │  Redis   │                 │
│   │  (Airflow metadata)         │ (Cache)  │                 │
│   └─────────────────────────────┴──────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 📚 Documentation

### 📋 Project Documentation
- **[Thiết kế Hệ thống Chi tiết](docs/system_design_detailed.md)** - ERD, System Architecture, Data Flow Diagrams
- **[Hướng dẫn Cài đặt & Code](docs/installation_guide.md)** - Setup guide với FastAPI code samples, API testing
- **[Kết quả Thực nghiệm](docs/experiment_results.md)** - Hanoi data validation, KPI measurements, performance analysis
- **[So sánh Giải pháp Tương tự](docs/related_work.md)** - Competitive analysis với Google Places, OSM, Foursquare, etc.
- **[Hạn chế & Hướng Phát triển](docs/limitation_future_work.md)** - Limitations assessment và 4-phase roadmap

### 🔧 Development Resources
- **[AI Coding Instructions](.github/copilot-instructions.md)** - 730+ lines of patterns, best practices, debugging guides
- **[Backend README](apps/backend/README.md)** - FastAPI development guide
- **[Frontend README](frontendphp/README.md)** - Next.js development guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Git
- Google Places API Key
- MongoDB Atlas account

### Setup & Running

#### 1. Clone and Setup (Windows PowerShell)
```powershell
# Clone the repository
git clone https://github.com/your-org/smart-travel-data-platform.git
cd smart-travel-data-platform

# Configure environment variables
# Copy .env.example to .env and fill in your API keys

# Start all services
.\setup.ps1
```

#### 2. Access the Platform
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Airflow Scheduler**: http://localhost:8080
- **API Health Check**: GET http://localhost:8000/api/admin/health

#### 3. Load Sample Data
```powershell
# Run initial data pipeline for Hanoi
.\scripts\run_pipeline.py --city hanoi --source osm,google
```

## � Core Features

### 1. Multi-Source Data Collection
- **OSM Integration**: Collect POI data from OpenStreetMap
- **Google Places API**: Enrich with ratings, reviews, photos
- **Hybrid Processing**: Intelligent deduplication across sources
- **Real-time Updates**: Incremental data synchronization

**Data Sources**:
- OpenStreetMap (Overpass API)
- Google Places API (Places Details, Photos, Reviews)
- Future: Foursquare, Yelp, local tourism APIs

### 2. Advanced Data Pipeline
- **Bronze Layer**: Raw data ingestion and storage
- **Silver Layer**: Data cleaning, normalization, deduplication
- **Gold Layer**: AI-enriched analytics-ready data
- **Automated Scheduling**: Airflow-based orchestration

**Pipeline Stages**:
```
Raw Data → Deduplication → Normalization → AI Enrichment → Analytics
```

### 3. Smart Travel Analytics Dashboard
Comprehensive analytics with 9+ visualization types:

**Key Metrics**:
- 📊 **Category Distribution** - Top 20 POI categories
- 🏆 **City Rankings** - Top cities by average rating
- 📈 **Rating Analysis** - Rating distribution and trends
- 🔥 **Heatmap Matrix** - City vs Category intensity visualization
- ⭐ **Top Places** - Highest-rated destinations table
- 🗺️ **Geographic Coverage** - Interactive map with clustering

**Analytics Endpoints**:
```
GET /api/smart-travel/dashboard/overview
GET /api/smart-travel/dashboard/city-ranking
GET /api/smart-travel/dashboard/city-category-matrix
GET /api/smart-travel/dashboard/places-by-category
GET /api/smart-travel/dashboard/places-by-rating
GET /api/smart-travel/dashboard/average-rating-by-category
GET /api/smart-travel/dashboard/places-by-province
GET /api/smart-travel/dashboard/top-places
GET /api/smart-travel/dashboard/map-data
```

### 4. RESTful API Services
- **POI Search API**: Location-based POI queries
- **Analytics API**: Real-time dashboard data
- **Pipeline API**: Manual execution and monitoring
- **Admin API**: System health and configuration

### 5. AI-Powered Data Processing
- **Smart Deduplication**: ML-based entity resolution
- **Category Classification**: Automated POI categorization
- **Quality Scoring**: Data accuracy assessment
- **Sentiment Analysis**: Review text processing

## 📊 Database Schema

### MongoDB Collections

#### `smart_travel.places` (Primary Data)
```javascript
{
  "_id": ObjectId,
  "name": "Ho Chi Minh Mausoleum",
  "city": "Hanoi",
  "province": "Hanoi",
  "latitude": 21.0367,
  "longitude": 105.8342,
  "rating": 4.5,
  "types": ["tourist_attraction", "historical_site"],
  "address": "2 Hùng Vương, Điện Bàn, Ba Đình District",
  "reviews": [...],
  "photos": [...],
  "u_key": "ho_chi_minh_mausoleum|21.0367|105.8342",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### `api_connections` (API Management)
```javascript
{
  "_id": ObjectId,
  "name": "Google Places API",
  "baseUrl": "https://maps.googleapis.com/maps/api/place",
  "headers": { "Authorization": "Bearer ..." },
  "rateLimit": 100,
  "isActive": true
}
```

#### `api_schedules` (Pipeline Scheduling)
```javascript
{
  "_id": ObjectId,
  "name": "Daily Hanoi Updates",
  "cronExpression": "0 2 * * *",
  "city": "Hanoi",
  "sources": ["osm", "google"],
  "isActive": true
}
```
  "startTime": ISODate,
  "endTime": ISODate,
  "duration": 1234,  // milliseconds
  "errorMessage": null
}
```

#### `smart_travel.places` (Sample Data)
```javascript
{
  "_id": ObjectId,
  "name": "Opera House",
  "city": "Sydney",
  "province": "New South Wales",
  "latitude": -33.8568,
  "longitude": 151.2153,
  "rating": 4.7,
  "types": ["tourist_attraction", "landmark"],
  "address": "Bennelong Point, Sydney NSW 2000, Australia",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

Documents: **4,972 tourist places** across multiple countries with ratings, categories, and geolocation.

## 🎨 Frontend Pages

### Main Pages
- **Dashboard** (`/`) - Overview and quick actions
- **Smart Travel Dashboard** (`/dashboards/smart-travel`) - Advanced analytics with 9 visualizations
- **Connections** (`/connections`) - Manage API connections
- **Schedules** (`/schedules`) - Create and manage schedules
- **Runs** (`/runs`) - View execution history
- **Data Explorer** (`/data`) - Browse stored data

### Wizard Pages (Create New API Integration)
- **Step 1: Connection** - Configure API endpoint
- **Step 2: Data Mapping** - Map API fields to database
- **Step 3: Schedule** - Set up automatic execution
- **Step 4: Review** - Verify configuration before saving

## 🔧 Development Patterns

### Backend: FastAPI with Pydantic Models

```python
# 1. Pydantic Models for Data Validation
from pydantic import BaseModel
from typing import List, Optional

class Place(BaseModel):
    name: str
    city: str
    province: str
    latitude: float
    longitude: float
    rating: Optional[float] = None
    types: List[str] = []
    address: Optional[str] = None

# 2. FastAPI Router with Async Operations
from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.smart_travel

@router.get("/places/{city}")
async def get_places_by_city(city: str, limit: int = 100):
    places = await db.places.find({"city": city}).limit(limit).to_list(length=None)
    return {"places": places, "count": len(places)}

@router.post("/places")
async def create_place(place: Place):
    result = await db.places.insert_one(place.dict())
    return {"id": str(result.inserted_id), **place.dict()}
```

### Frontend: Next.js with TypeScript & Axios

```typescript
// services/apiClient.ts
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const apiClient = {
  timeout: 120000,  // 120s for large datasets
  
  async get(endpoint: string, timeoutMs: number = 15000) {
    return Promise.race([
      axios.get(`${API_BASE}${endpoint}`),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), timeoutMs)
      ),
    ]);
  },
};

// components/Dashboard.tsx
import { useEffect, useState } from 'react';
import { apiClient } from '../services/apiClient';

export default function Dashboard() {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiClient.get('/api/smart-travel/dashboard/overview');
        setData(response.data);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      }
    };
    fetchData();
  }, []);
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Smart Travel Dashboard</h1>
      {/* Dashboard content */}
    </div>
  );
}
```
};
```

### MongoDB Aggregation Pipeline Pattern

```python
# ✅ CORRECT: Single pipeline (1 database call, fast)
async def get_city_ranking(limit: int = 20):
    pipeline = [
        {"$group": {
            "_id": "$city",
            "count": {"$sum": 1},
            "avgRating": {"$avg": "$rating"}
        }},
        {"$sort": {"avgRating": -1}},
        {"$limit": limit}
    ]
    
    cursor = db.places.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append({
            "city": doc["_id"],
            "count": doc["count"],
            "avgRating": round(doc["avgRating"], 2)
        })
    return results

# ❌ SLOW: Nested loops (400+ database calls, timeout)
async def get_city_ranking_slow():
    cities = await db.places.distinct("city")
    results = []
    for city in cities:  # N iterations
        count = await db.places.count_documents({"city": city})
        # More queries for each city...
        results.append({"city": city, "count": count})
    return results
```

**Performance**: 400+ queries → 1 pipeline = **120s+ timeout → <5s response (400× faster)**

## 📈 Performance Optimization

### Frontend Timeout Strategy
Different endpoints require different timeouts based on query complexity:

```typescript
// Critical endpoints (fast aggregations)
const fetchCritical = () => Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/overview', 15000),
  fetchWithTimeout('/api/smart-travel/dashboard/city-ranking', 15000),
]);

// Complex aggregations (heatmap with $unwind/$group)
const fetchHeavy = () => Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/city-category-matrix', 30000),  // Needs 30s
  fetchWithTimeout('/api/smart-travel/dashboard/map-data', 20000),
]);

// Sequential loading: Critical → Heavy
Promise.all([...fetchCritical()]).then(() => Promise.all([...fetchHeavy()]));
```

### MongoDB Query Optimization

**Key Techniques**:
1. **Single aggregation pipeline** instead of N×M queries
2. **Result limiting** to avoid memory explosion (e.g., top 15×15 for heatmaps)
3. **Proper MongoDB indexes** on frequently aggregated fields
4. **Connection initialization** before aggregation (`connectToMongoDB()`)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (or local MongoDB)
- Google Places API key
- OpenStreetMap access (free)

### 1. Clone & Setup
```bash
git clone <repository-url>
cd data-platform-for-smart-travel

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

### 2. Configure Environment
```bash
# backend/.env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/smart_travel
GOOGLE_PLACES_API_KEY=your_google_api_key
OSM_API_URL=https://overpass-api.de/api/interpreter

# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 3. Start Services
```bash
# Start all services (MongoDB, Backend, Frontend, Airflow)
docker-compose up -d

# Or start development mode
./scripts/start-dev.sh
```

### 4. Access Applications
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080

### 5. Run Initial Pipeline
```bash
# Execute Hanoi data collection pipeline
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"city": "Hanoi", "sources": ["osm", "google"]}'

# Check pipeline status
curl http://localhost:8000/api/pipeline/status
```

### 6. View Dashboard
Navigate to http://localhost:3000/dashboards/smart-travel to see:
- City rankings by average rating
- Category distribution charts
- Interactive heatmaps
- Top-rated places tables

## 🎓 Learning Resources

### Key Documentation
- **System Design**: `docs/system_design_detailed.md` - ERD, architecture diagrams, data flow
- **Installation Guide**: `docs/installation_guide.md` - FastAPI code samples, API testing
- **Experiment Results**: `docs/experiment_results.md` - Hanoi data KPIs, performance metrics
- **Related Work**: `docs/related_work.md` - Competitive analysis, SWOT comparison
- **Limitations & Future**: `docs/limitation_future_work.md` - Roadmap, risk assessment

### Example Use Cases
1. **Tourism Analytics**: Analyze POI data for travel recommendations
2. **City Planning**: Use heatmap data for urban development insights
3. **Business Intelligence**: Track tourism trends and ratings
4. **Data Enrichment**: Combine OSM + Google data for comprehensive POI database

---

**Built with ❤️ using FastAPI, Next.js, MongoDB, and Apache Airflow**

Last Updated: November 11, 2025
