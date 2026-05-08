# Tài liệu Hướng dẫn Cài đặt & Code Thực tế

## Dự án: Smart Travel Data Platform (Hệ thống Nền tảng Dữ liệu Du lịch Thông minh)

---

### 1. Giới thiệu

Tài liệu này cung cấp hướng dẫn chi tiết để cài đặt, cấu hình và chạy hệ thống Smart Travel Data Platform. Hệ thống bao gồm:
- **Backend**: FastAPI (Python) REST API (port 8000)
- **Frontend**: Next.js 15 với TypeScript (port 3000)
- **Orchestration**: Apache Airflow 2.9 (port 8080)
- **Database**: MongoDB Atlas (cloud) + PostgreSQL (Airflow metadata) + Redis (cache)
- **Storage**: MinIO (S3-compatible)

Sau khi cài đặt, bạn sẽ có một pipeline hoàn chỉnh có thể thu thập dữ liệu POI từ OSM và Google Places API, xử lý dữ liệu qua các layer Bronze → Silver → Gold, và phục vụ qua API dashboard.

---

### 2. Prerequisites (Yêu cầu Hệ thống)

#### 2.1. Phần mềm Cần thiết
- **Windows 10/11** với PowerShell 5.1+
- **Docker Desktop** (version 4.0+)
- **Git** (để clone repository)
- **Visual Studio Code** (khuyến nghị)

#### 2.2. Tài nguyên Hệ thống
- **RAM**: Tối thiểu 8GB, khuyến nghị 16GB+
- **CPU**: 4 cores trở lên
- **Disk**: 20GB free space cho containers và data
- **Network**: Kết nối internet ổn định (để pull images và API calls)

#### 2.3. API Keys (Bắt buộc)
- **Google Places API Key**: Đăng ký tại [Google Cloud Console](https://console.cloud.google.com/)
- **MongoDB Atlas Cluster**: Tạo cluster miễn phí tại [MongoDB Atlas](https://www.mongodb.com/atlas)

---

### 3. Cài đặt Development Environment

#### 3.1. Clone Repository
```powershell
git clone https://github.com/your-org/smart-travel-data-platform.git
cd smart-travel-data-platform
```

#### 3.2. Cấu hình Environment Variables
Tạo file `.env` trong thư mục gốc:

```env
# MongoDB Atlas (thay thế bằng connection string thực tế)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/smart_travel_db?retryWrites=true&w=majority
MONGODB_DATABASE=smart_travel_db

# Google Places API
GOOGLE_PLACES_API_KEY=your_google_api_key_here

# Airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
AIRFLOW__CORE__FERNET_KEY=your_fernet_key_here
AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
AIRFLOW__CORE__LOAD_EXAMPLES=False

# Redis (cache)
REDIS_URL=redis://redis:6379

# JWT Secret
JWT_SECRET=your_jwt_secret_here

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### 3.3. Chạy Setup Script
```powershell
# Chạy script setup tự động
.\setup.ps1
```

Script này sẽ:
- Pull Docker images
- Start tất cả services
- Chạy database migrations
- Seed initial data

#### 3.4. Kiểm tra Services
Sau khi setup, kiểm tra các services đang chạy:

```powershell
docker-compose ps
```

Expected output:
```
NAME                          COMMAND                  SERVICE             STATUS              PORTS
backendphp-backend-1          "docker-php-entrypoi…"   backend             running             0.0.0.0:8000->80/tcp
backendphp-frontend-1         "docker-entrypoint.s…"   frontend            running             0.0.0.0:3000->3000/tcp
backendphp-airflow-webserver-1 "airflow webserver"      airflow-webserver   running             0.0.0.0:8080->8080/tcp
backendphp-airflow-scheduler-1 "airflow scheduler"     airflow-scheduler   running
backendphp-mongo-1            "docker-entrypoint.s…"   mongo              running             0.0.0.0:27017->27017/tcp
backendphp-postgres-1         "docker-entrypoint.s…"   postgres            running             0.0.0.0:5432->5432/tcp
backendphp-redis-1            "redis-server"           redis               running             0.0.0.0:6379->6379/tcp
```

---

### 4. Chạy Pipeline (Data Ingestion & Processing)

#### 4.1. Truy cập Airflow UI
Mở browser và truy cập: http://localhost:8080
- **Username**: airflow
- **Password**: airflow

#### 4.2. Kích hoạt DAG
1. Tìm DAG `smart_travel_pipeline`
2. Click toggle để bật DAG
3. Click "Trigger DAG" để chạy thủ công

#### 4.3. Monitor Pipeline Execution
- Xem Graph View để theo dõi các tasks
- Check logs trong Log tab của mỗi task
- Monitor metrics trong Admin > Pools

#### 4.4. Code Pipeline Thực tế (DAG Definition)

File: `dags/smart_travel_pipeline.py`

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'smart_travel_pipeline',
    default_args=default_args,
    description='Smart Travel Data Pipeline',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Task 1: Ingest data from OSM and Google Places
ingest_task = PythonOperator(
    task_id='ingest_data',
    python_callable=ingest_data,
    dag=dag,
)

# Task 2: Process and clean data (Bronze → Silver)
process_task = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag,
)

# Task 3: Enrich with AI and store in Gold layer
enrich_task = PythonOperator(
    task_id='enrich_data',
    python_callable=enrich_data,
    dag=dag,
)

# Task 4: Update dashboard cache
cache_task = BashOperator(
    task_id='update_cache',
    bash_command='curl -X POST http://backend:8000/api/admin/cache/refresh',
    dag=dag,
)

# Define dependencies
ingest_task >> process_task >> enrich_task >> cache_task

def ingest_data():
    """Ingest POI data from external APIs"""
    from src.collectors.osm_collector import OSMCollector
    from src.collectors.google_enrichor import GoogleEnrichor

    # Collect from OSM
    osm_collector = OSMCollector(city="Hanoi")
    osm_data = osm_collector.collect()

    # Enrich with Google Places
    google_enrichor = GoogleEnrichor()
    enriched_data = google_enrichor.enrich(osm_data)

    # Save to Bronze layer (MinIO)
    save_to_bronze(enriched_data)

def process_data():
    """Process data: deduplication, normalization"""
    from src.ingestion.silver_processor import SilverProcessor

    processor = SilverProcessor()
    processor.process_bronze_to_silver()

def enrich_data():
    """AI enrichment and Gold layer storage"""
    from src.ingestion.gold_generator import GoldGenerator

    generator = GoldGenerator()
    generator.generate_gold_layer()
```

---

### 5. Test API Endpoints

#### 5.1. Health Check
```powershell
# Test backend health
Invoke-WebRequest -Uri "http://localhost:8000/api/admin/health" -Method GET
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "airflow": "running"
  }
}
```

#### 5.2. Authentication
```powershell
# Login to get JWT token
$body = @{
    email = "admin@smarttravel.com"
    password = "admin123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
$token = ($response.Content | ConvertFrom-Json).token
```

#### 5.3. Data API Endpoints

##### Get Places Data
```powershell
# Get all places with pagination
Invoke-WebRequest -Uri "http://localhost:8000/api/places?page=1&limit=10" -Method GET -Headers @{Authorization="Bearer $token"}
```

##### Run Pipeline Manually
```powershell
# Trigger pipeline execution
$body = @{
    city = "Hanoi"
    bbox = "105.8,20.9,105.9,21.0"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/pipeline/run" -Method POST -Body $body -ContentType "application/json" -Headers @{Authorization="Bearer $token"}
```

##### Dashboard Analytics
```powershell
# Get city ranking
Invoke-WebRequest -Uri "http://localhost:8000/api/analytics/city-ranking" -Method GET -Headers @{Authorization="Bearer $token"}
```

#### 5.4. Code API Thực tế (Backend Python/FastAPI)

File: `apps/backend/app/main.py`

```python
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import places, dashboard, system, airflow, admin
from app.db.client import MongoClient
from app.db.repository import PlaceRepository
from app.models.place import PipelineStatus
from datetime import datetime, timezone
import os
import logging
from prometheus_client import Counter, Histogram

app = FastAPI(title="Smart Travel Production API", version="2.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(places.router, prefix="/api", tags=["places"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(airflow.router, prefix="/api", tags=["airflow"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

# Health check endpoint
@app.get("/api/admin/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        mongo_client = MongoClient()
        await mongo_client.connect()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "mongodb": "connected",
                "api": "running"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

File: `apps/backend/app/api/places.py`

```python
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.place import Place, PlaceCreate, PlaceUpdate
from app.services.place_service import PlaceService
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/places", response_model=List[Place])
async def get_places(
    city: Optional[str] = Query(None),
    place_type: Optional[str] = Query(None, alias="type"),
    min_rating: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get places with filtering and pagination"""
    try:
        service = PlaceService()
        filters = {}
        if city:
            filters["city"] = city
        if place_type:
            filters["type"] = place_type
        if min_rating is not None:
            filters["rating"] = {"$gte": min_rating}
        
        places = await service.get_places(filters, page, limit)
        return places
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch places: {str(e)}")

@router.get("/places/{place_id}", response_model=Place)
async def get_place(
    place_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific place by ID"""
    try:
        service = PlaceService()
        place = await service.get_place_by_id(place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return place
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch place: {str(e)}")

@router.post("/places", response_model=Place)
async def create_place(
    place_data: PlaceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new place"""
    try:
        service = PlaceService()
        place = await service.create_place(place_data.dict())
        return place
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create place: {str(e)}")

@router.put("/places/{place_id}", response_model=Place)
async def update_place(
    place_id: str,
    place_data: PlaceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing place"""
    try:
        service = PlaceService()
        place = await service.update_place(place_id, place_data.dict(exclude_unset=True))
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        return place
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update place: {str(e)}")

@router.delete("/places/{place_id}")
async def delete_place(
    place_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a place"""
    try:
        service = PlaceService()
        deleted = await service.delete_place(place_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Place not found")
        return {"message": "Place deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete place: {str(e)}")
```

File: `apps/backend/app/services/place_service.py`

```python
from app.db.repository import PlaceRepository
from app.models.place import PlaceCreate, PlaceUpdate
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timezone

class PlaceService:
    def __init__(self):
        self.repository = PlaceRepository()
    
    async def get_places(self, filters: Dict[str, Any], page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """Get places with filtering and pagination"""
        skip = (page - 1) * limit
        
        # Build MongoDB query
        query = {}
        if "city" in filters:
            query["city"] = filters["city"]
        if "type" in filters:
            query["type"] = filters["type"]
        if "rating" in filters:
            query["rating"] = filters["rating"]
        
        places = await self.repository.find_many(query, skip=skip, limit=limit)
        return places
    
    async def get_place_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get a place by ID"""
        return await self.repository.find_by_id(place_id)
    
    async def create_place(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new place"""
        # Generate u_key for deduplication
        u_key = self._generate_u_key(place_data["name"], place_data["location"])
        place_data["u_key"] = u_key
        place_data["created_at"] = datetime.now(timezone.utc)
        place_data["updated_at"] = datetime.now(timezone.utc)
        
        return await self.repository.create(place_data)
    
    async def update_place(self, place_id: str, place_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing place"""
        place_data["updated_at"] = datetime.now(timezone.utc)
        return await self.repository.update(place_id, place_data)
    
    async def delete_place(self, place_id: str) -> bool:
        """Delete a place"""
        return await self.repository.delete(place_id)
    
    def _generate_u_key(self, name: str, location: Dict[str, float]) -> str:
        """Generate unique key for deduplication"""
        normalized_name = name.lower().strip()
        rounded_lat = round(location["lat"], 4)
        rounded_lng = round(location["lng"], 4)
        
        key_string = f"{normalized_name}|{rounded_lat}|{rounded_lng}"
        return hashlib.md5(key_string.encode()).hexdigest()
```

File: `apps/backend/app/models/place.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)

class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(restaurant|hotel|attraction|shop|entertainment)$")
    location: Location
    rating: Optional[float] = Field(None, ge=0, le=5)
    reviews: Optional[List[Dict[str, Any]]] = []
    photos: Optional[List[str]] = []
    _lineage_source: Optional[str] = "manual"

class PlaceCreate(PlaceBase):
    pass

class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern="^(restaurant|hotel|attraction|shop|entertainment)$")
    location: Optional[Location] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    reviews: Optional[List[Dict[str, Any]]] = None
    photos: Optional[List[str]] = None

class Place(PlaceBase):
    id: str = Field(..., alias="_id")
    u_key: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PipelineStatus(BaseModel):
    city: str
    last_run: datetime
    records_count: int
    quality_score: float
    status: str = Field(..., pattern="^(running|completed|failed)$")
```

---

### 6. Frontend Code Samples

#### 6.1. API Client (Axios)

File: `frontendphp/services/apiClient.js`

```javascript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 minutes for large datasets
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on unauthorized
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const placesApi = {
  getPlaces: (params = {}) => apiClient.get('/api/places', { params }),
  getPlace: (id) => apiClient.get(`/api/places/${id}`),
  createPlace: (data) => apiClient.post('/api/places', data),
  updatePlace: (id, data) => apiClient.put(`/api/places/${id}`, data),
  deletePlace: (id) => apiClient.delete(`/api/places/${id}`),
};

export const pipelineApi = {
  runPipeline: (data) => apiClient.post('/api/pipeline/run', data),
  getStatus: () => apiClient.get('/api/pipeline/status'),
};

export const analyticsApi = {
  getCityRanking: () => apiClient.get('/api/analytics/city-ranking'),
  getOverview: () => apiClient.get('/api/analytics/overview'),
};

export default apiClient;
```

#### 6.2. Dashboard Component

File: `frontendphp/components/Dashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { placesApi, analyticsApi } from '../services/apiClient';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [places, setPlaces] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Parallel API calls for better performance
      const [placesResponse, analyticsResponse] = await Promise.all([
        placesApi.getPlaces({ limit: 100 }),
        analyticsApi.getOverview()
      ]);

      setPlaces(placesResponse.data.data);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900">Total Places</h3>
          <p className="text-2xl font-bold text-blue-600">{analytics.totalPlaces || 0}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900">Cities Covered</h3>
          <p className="text-2xl font-bold text-green-600">{analytics.citiesCount || 0}</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-purple-900">Avg Rating</h3>
          <p className="text-2xl font-bold text-purple-600">{analytics.avgRating?.toFixed(1) || 0}</p>
        </div>
      </div>

      {/* City Ranking Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold mb-4">Top Cities by Places Count</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={analytics.cityRanking || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="city" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Places Table */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-semibold mb-4">Recent Places</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full table-auto">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-left">City</th>
                <th className="px-4 py-2 text-left">Type</th>
                <th className="px-4 py-2 text-left">Rating</th>
              </tr>
            </thead>
            <tbody>
              {places.slice(0, 10).map((place) => (
                <tr key={place.u_key} className="border-t">
                  <td className="px-4 py-2">{place.name}</td>
                  <td className="px-4 py-2">{place.city}</td>
                  <td className="px-4 py-2">{place.type}</td>
                  <td className="px-4 py-2">{place.rating || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
```

---

### 7. Troubleshooting (Khắc phục Sự cố)

#### 7.1. Pipeline Không chạy
```powershell
# Check Airflow logs
docker-compose logs airflow-scheduler

# Restart Airflow services
docker-compose restart airflow-webserver airflow-scheduler
```

#### 7.2. API Timeout
```powershell
# Increase timeout in apiClient.js
const apiClient = axios.create({
  timeout: 300000, // 5 minutes for very large datasets
});
```

#### 7.3. MongoDB Connection Failed
```powershell
# Check MongoDB connection
docker exec -it smart-travel-data-platform-mongo-1 mongosh --eval "db.runCommand('ping')"

# Verify connection string in .env
# Ensure MongoDB Atlas IP whitelist includes your IP
```

#### 7.4. Frontend Build Errors
```powershell
cd frontendphp
npm install
npm run build
```

#### 7.5. Port Conflicts
```powershell
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :8080

# Kill process if needed
taskkill /PID <PID> /F
```

---

### 8. Performance Optimization

#### 8.1. Database Indexes
```javascript
// MongoDB indexes for better query performance
db.places.createIndex({ "city": 1, "type": 1 });
db.places.createIndex({ "location": "2dsphere" });
db.places.createIndex({ "rating": -1 });
db.places.createIndex({ "u_key": 1 }, { unique: true });
```

#### 8.2. Caching Strategy
```php
// Redis caching for frequent queries
$redis = new Redis();
$redis->connect('redis', 6379);

$cacheKey = 'places_city_' . $city;
$cachedData = $redis->get($cacheKey);

if (!$cachedData) {
    $data = $this->repository->findByCity($city);
    $redis->setex($cacheKey, 3600, json_encode($data)); // Cache for 1 hour
} else {
    $data = json_decode($cachedData, true);
}
```

#### 8.3. API Rate Limiting
```php
// Rate limiting middleware
$rateLimiter = new RateLimiter();
$rateLimiter->limitRequests('api_calls', 100, 60); // 100 requests per minute
```

---

*Tài liệu này được cập nhật lần cuối: May 6, 2026. Vui lòng tham khảo README.md trong từng thư mục con để biết thêm chi tiết.*
