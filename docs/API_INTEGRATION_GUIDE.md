# API Integration Guide - Frontend Admin

## 📚 Tổng Quan API Backend

Smart Tourism Platform cung cấp **41 API endpoints** được phân nhóm thành 6 module:

| Module | Endpoints | Authentication | Mô tả |
|--------|-----------|----------------|-------|
| Authentication | 6 | JWT Bearer | Đăng nhập, token refresh |
| Pipeline Management | 13 | JWT Bearer | Điều khiển pipeline, monitoring |
| Data Query | 8 | JWT Bearer | Query POIs, search, filter |
| Admin | 7 | JWT Bearer | Quản lý users, system logs |
| Monitoring | 4 | Public/Private | Health checks, system status |
| Health | 3 | Public | Basic health probes |

---

## 🔐 Authentication

### Login Flow
```typescript
// 1. Login để lấy token
const login = async (username: string, password: string) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  
  const data = await response.json();
  // { access_token: "eyJ...", token_type: "bearer" }
  
  // 2. Lưu token vào localStorage
  localStorage.setItem('token', data.access_token);
  
  return data;
};

// 3. Sử dụng token cho các request sau
const fetchWithAuth = (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
};
```

### Axios Interceptor
```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// Request interceptor - thêm token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - xử lý lỗi
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Token hết hạn
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Refresh token
        const refreshResponse = await api.post('/api/v1/auth/refresh');
        const newToken = refreshResponse.data.access_token;
        
        localStorage.setItem('token', newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh thất bại -> logout
        localStorage.removeItem('token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

---

## ⚙️ Pipeline API

### 1. Start Pipeline
```typescript
interface StartPipelineRequest {
  execution_type: 'bronze' | 'silver' | 'gold' | 'collection';
  config?: {
    cities?: string[];
    categories?: string[];
    radius?: number;
    workers?: number;
  };
}

interface PipelineResponse {
  execution_id: string;
  status: string;
  message: string;
}

// Start collection pipeline
const startCollection = async (cities: string[]) => {
  const response = await api.post<PipelineResponse>('/api/v1/pipeline/start', {
    execution_type: 'collection',
    config: { cities, radius: 1000, workers: 5 },
  });
  return response.data;
};

// Start processing pipeline
const startProcessing = async () => {
  const response = await api.post<PipelineResponse>('/api/v1/pipeline/start', {
    execution_type: 'silver',
  });
  return response.data;
};
```

### 2. Control Pipeline
```typescript
// Stop pipeline
const stopPipeline = async (executionId: string) => {
  const response = await api.post(`/api/v1/pipeline/stop/${executionId}`);
  return response.data;
};

// Pause pipeline
const pausePipeline = async (executionId: string) => {
  const response = await api.post(`/api/v1/pipeline/pause/${executionId}`);
  return response.data;
};

// Resume pipeline
const resumePipeline = async (executionId: string) => {
  const response = await api.post(`/api/v1/pipeline/resume/${executionId}`);
  return response.data;
};

// Restart pipeline
const restartPipeline = async (executionId: string) => {
  const response = await api.post(`/api/v1/pipeline/restart/${executionId}`);
  return response.data;
};
```

### 3. Monitor Pipeline
```typescript
interface PipelineStatus {
  execution_id: string;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'stopped';
  progress: number;
  cities: string[];
  pois_collected: number;
  pois_total: number;
  started_at: string;
  estimated_completion: string;
}

// Get specific pipeline status
const getPipelineStatus = async (executionId: string) => {
  const response = await api.get<PipelineStatus>(`/api/v1/pipeline/status/${executionId}`);
  return response.data;
};

// Get all active pipelines
const getActivePipelines = async () => {
  const response = await api.get<PipelineStatus[]>('/api/v1/pipeline/active');
  return response.data;
};

// Get pipeline history
interface PipelineHistoryParams {
  limit?: number;
  offset?: number;
  city?: string;
  category?: string;
}

const getPipelineHistory = async (params?: PipelineHistoryParams) => {
  const response = await api.get('/api/v1/pipeline/history', { params });
  return response.data;
};
```

### 4. Pipeline Dashboard & Metrics
```typescript
// Get pipeline dashboard
const getPipelineDashboard = async () => {
  const response = await api.get('/api/v1/pipeline/dashboard');
  return response.data;
};

// Get pipeline metrics
const getPipelineMetrics = async () => {
  const response = await api.get('/api/v1/pipeline/metrics');
  return response.data;
};

// Get pipeline errors
const getPipelineErrors = async () => {
  const response = await api.get('/api/v1/pipeline/errors');
  return response.data;
};

// Get data quality report
const getDataQuality = async () => {
  const response = await api.get('/api/v1/pipeline/data-quality');
  return response.data;
};

// Cleanup resources
const cleanupPipeline = async () => {
  const response = await api.delete('/api/v1/pipeline/cleanup');
  return response.data;
};
```

---

## 🗺️ POI Data API

### 1. List POIs
```typescript
interface POIListParams {
  city?: string;
  category?: string;
  layer?: 'bronze' | 'silver' | 'gold';
  limit?: number;
  offset?: number;
  sort_by?: 'quality_score' | 'rating' | 'name';
  sort_order?: 'asc' | 'desc';
}

interface POIListResponse {
  total: number;
  offset: number;
  limit: number;
  items: POI[];
}

const getPOIs = async (params?: POIListParams) => {
  const response = await api.get<POIListResponse>('/api/v1/data/pois', { params });
  return response.data;
};

// Example usage
const hanoiHotels = await getPOIs({
  city: 'hanoi',
  category: 'hotel',
  layer: 'gold',
  limit: 50,
  sort_by: 'quality_score',
  sort_order: 'desc',
});
```

### 2. Search POIs
```typescript
interface POISearchParams {
  q: string;
  city?: string;
  category?: string;
  limit?: number;
}

const searchPOIs = async (query: string, filters?: Omit<POISearchParams, 'q'>) => {
  const response = await api.get<POIListResponse>('/api/v1/data/pois/search', {
    params: { q: query, ...filters },
  });
  return response.data;
};

// Example: Search for "pho" in Hanoi
const phoInHanoi = await searchPOIs('pho', { city: 'hanoi', limit: 20 });
```

### 3. Get POI Detail
```typescript
interface POIDetail {
  poi_id: string;
  name: string;
  category: string;
  address: string;
  city: string;
  location: {
    lat: number;
    lng: number;
  };
  rating: number;
  review_count: number;
  quality_score: number;
  layer: string;
  sources: string[];
  created_at: string;
  updated_at: string;
}

const getPOIDetail = async (poiId: string) => {
  const response = await api.get<POIDetail>(`/api/v1/data/pois/${poiId}`);
  return response.data;
};
```

### 4. Find Nearby POIs
```typescript
interface NearbyPOIParams {
  lat: number;
  lng: number;
  radius?: number; // meters, default 1000
  category?: string;
  limit?: number;
}

const getNearbyPOIs = async (lat: number, lng: number, params?: Omit<NearbyPOIParams, 'lat' | 'lng'>) => {
  const response = await api.get<POIListResponse>('/api/v1/data/pois/nearby', {
    params: { lat, lng, ...params },
  });
  return response.data;
};

// Example: Find restaurants within 500m of a location
const nearbyRestaurants = await getNearbyPOIs(21.0278, 105.8342, {
  radius: 500,
  category: 'restaurant',
  limit: 10,
});
```

### 5. Metadata APIs
```typescript
// Get data statistics
const getDataStats = async () => {
  const response = await api.get('/api/v1/data/stats');
  return response.data;
};

// Get data layers info
const getDataLayers = async () => {
  const response = await api.get('/api/v1/data/layers');
  return response.data;
};

// Get all cities
const getCities = async () => {
  const response = await api.get<string[]>('/api/v1/data/cities');
  return response.data;
};

// Get all categories
const getCategories = async () => {
  const response = await api.get<string[]>('/api/v1/data/categories');
  return response.data;
};
```

---

## 👤 Admin API

### 1. User Management
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  created_at: string;
  is_active: boolean;
}

interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  role: string;
}

// List users
const getUsers = async () => {
  const response = await api.get<User[]>('/api/v1/admin/users');
  return response.data;
};

// Create user
const createUser = async (userData: CreateUserRequest) => {
  const response = await api.post<User>('/api/v1/admin/users', userData);
  return response.data;
};

// Delete user
const deleteUser = async (userId: string) => {
  const response = await api.delete(`/api/v1/admin/users/${userId}`);
  return response.data;
};
```

### 2. System Management
```typescript
// Get system statistics
const getSystemStats = async () => {
  const response = await api.get('/api/v1/admin/stats');
  return response.data;
};

// Get system logs
const getSystemLogs = async () => {
  const response = await api.get('/api/v1/admin/logs');
  return response.data;
};

// Toggle maintenance mode
const toggleMaintenance = async (enabled: boolean) => {
  const response = await api.post('/api/v1/admin/maintenance', { enabled });
  return response.data;
};

// Run system cleanup
const runCleanup = async () => {
  const response = await api.post('/api/v1/admin/cleanup');
  return response.data;
};
```

---

## 📊 Monitoring API

### 1. System Status
```typescript
// Get detailed system status
const getSystemStatus = async () => {
  const response = await api.get('/api/v1/monitoring/status');
  return response.data;
};

// Get API version
const getVersion = async () => {
  const response = await api.get('/api/v1/monitoring/version');
  return response.data;
};

// Get dependency health
const getDependencies = async () => {
  const response = await api.get('/api/v1/monitoring/dependencies');
  return response.data;
};

// Get Prometheus metrics
const getMetrics = async () => {
  const response = await api.get('/metrics');
  return response.data;
};
```

---

## ❤️ Health API (Public)

```typescript
// Basic health check
const checkHealth = async () => {
  const response = await fetch('/health');
  return response.json();
  // { status: "healthy" }
};

// Readiness check (includes DB connectivity)
const checkReadiness = async () => {
  const response = await fetch('/ready');
  return response.json();
  // { status: "ready", checks: { mongodb: {...}, redis: {...} } }
};

// Detailed health information
const getDetailedHealth = async () => {
  const response = await fetch('/health/detailed');
  return response.json();
};
```

---

## 🔄 React Query Integration

### Pipeline Hooks
```typescript
// hooks/usePipeline.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const useActivePipelines = () => {
  return useQuery({
    queryKey: ['pipelines', 'active'],
    queryFn: () => pipelineApi.getActive(),
    refetchInterval: 5000, // Auto refresh every 5s
  });
};

export const useStartPipeline = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: pipelineApi.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
};

export const useStopPipeline = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: pipelineApi.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines', 'active'] });
    },
  });
};
```

### POI Hooks
```typescript
// hooks/usePOIs.ts
export const usePOIs = (params?: POIListParams) => {
  return useQuery({
    queryKey: ['pois', params],
    queryFn: () => poiApi.getAll(params),
    keepPreviousData: true,
  });
};

export const usePOISearch = () => {
  return useMutation({
    mutationFn: ({ query, filters }: { query: string; filters?: any }) =>
      poiApi.search(query, filters),
  });
};

export const usePOIDetail = (poiId: string) => {
  return useQuery({
    queryKey: ['pois', poiId],
    queryFn: () => poiApi.getById(poiId),
    enabled: !!poiId,
  });
};

export const useCities = () => {
  return useQuery({
    queryKey: ['metadata', 'cities'],
    queryFn: () => poiApi.getCities(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['metadata', 'categories'],
    queryFn: () => poiApi.getCategories(),
    staleTime: 5 * 60 * 1000,
  });
};
```

### System Hooks
```typescript
// hooks/useSystem.ts
export const useSystemStatus = () => {
  return useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => monitoringApi.getSystemStatus(),
    refetchInterval: 30000,
  });
};

export const useDataStats = () => {
  return useQuery({
    queryKey: ['system', 'stats'],
    queryFn: () => poiApi.getStats(),
    refetchInterval: 30000,
  });
};

export const useUsers = () => {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminApi.getUsers(),
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: adminApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
};
```

---

## ⚠️ Error Handling

### Error Types
```typescript
enum APIErrorCode {
  // 400 Bad Request
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  
  // 401 Unauthorized
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',
  
  // 403 Forbidden
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  
  // 404 Not Found
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
  
  // 429 Too Many Requests
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  
  // 500 Internal Server Error
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  PIPELINE_ERROR = 'PIPELINE_ERROR',
}

interface APIError {
  code: APIErrorCode;
  message: string;
  details?: Record<string, string[]>;
  retryAfter?: number; // For rate limiting
}
```

### Error Handler Component
```typescript
// components/ErrorDisplay.tsx
const ErrorDisplay: React.FC<{ error: Error }> = ({ error }) => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const apiError = error.response?.data as APIError;
    
    switch (status) {
      case 401:
        return <AuthError message={apiError?.message} />;
      case 403:
        return <PermissionError />;
      case 429:
        return <RateLimitError retryAfter={apiError?.retryAfter} />;
      case 500:
        return <ServerError message={apiError?.message} />;
      default:
        return <GenericError error={error} />;
    }
  }
  
  return <GenericError error={error} />;
};
```

---

## 📝 TypeScript Types

```typescript
// types/index.ts

// Pipeline Types
export interface PipelineExecution {
  execution_id: string;
  execution_type: 'bronze' | 'silver' | 'gold' | 'collection';
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'stopped';
  progress: number;
  cities: string[];
  categories: string[];
  pois_collected: number;
  pois_total: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

// POI Types
export interface POI {
  poi_id: string;
  name: string;
  category: string;
  subcategory?: string;
  address: string;
  city: string;
  district?: string;
  location: {
    lat: number;
    lng: number;
  };
  rating: number;
  review_count: number;
  quality_score: number;
  price_level?: number;
  phone?: string;
  website?: string;
  opening_hours?: Record<string, string>;
  photos?: string[];
  tags: string[];
  layer: 'bronze' | 'silver' | 'gold';
  sources: string[];
  created_at: string;
  updated_at: string;
}

// User Types
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

// Stats Types
export interface DataStats {
  total_pois: number;
  total_cities: number;
  total_categories: number;
  by_layer: {
    bronze: number;
    silver: number;
    gold: number;
  };
  by_category: Record<string, number>;
  by_city: Record<string, number>;
  data_quality: {
    high: number;
    good: number;
    average: number;
    low: number;
  };
}

// Health Types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
}

export interface ReadinessStatus {
  status: 'ready' | 'not_ready';
  checks: {
    mongodb: { status: 'connected' | 'disconnected'; latency_ms?: number };
    redis?: { status: 'connected' | 'disconnected' | 'optional' };
  };
  timestamp: string;
}
```

---

## 🧪 Testing API Integration

```typescript
// __tests__/api.test.ts
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  // Mock auth
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        access_token: 'mock-token',
        token_type: 'bearer',
      })
    );
  }),
  
  // Mock pipeline
  rest.get('/api/v1/pipeline/active', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          execution_id: 'test-123',
          status: 'running',
          progress: 45,
          cities: ['hanoi'],
          pois_collected: 234,
          pois_total: 500,
        },
      ])
    );
  }),
  
  // Mock POIs
  rest.get('/api/v1/data/pois', (req, res, ctx) => {
    return res(
      ctx.json({
        total: 15525,
        offset: 0,
        limit: 10,
        items: [
          { poi_id: '1', name: 'Test Hotel', category: 'hotel' },
        ],
      })
    );
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Integration', () => {
  it('should login successfully', async () => {
    const result = await authApi.login('admin', 'password');
    expect(result.access_token).toBe('mock-token');
  });
  
  it('should fetch active pipelines', async () => {
    const pipelines = await pipelineApi.getActive();
    expect(pipelines).toHaveLength(1);
    expect(pipelines[0].status).toBe('running');
  });
});
```

---

## 📚 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Axios Documentation](https://axios-http.com/)

---

**Sẵn sàng triển khai?** 🚀
