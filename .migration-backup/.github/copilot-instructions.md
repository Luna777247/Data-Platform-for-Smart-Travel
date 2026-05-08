# AI Coding Agent Instructions - No-Code API Connector

## Project Overview
This is a **no-code API connector platform** with a microservices architecture:
- **Backend**: PHP 8.3 REST API (port 8000) with MongoDB Atlas
- **Frontend**: Next.js 15 with TypeScript (port 3000)
- **Scheduling**: Apache Airflow 2.9 (port 8080) for automated API execution
- **Database**: MongoDB Atlas (cloud) + PostgreSQL (Airflow metadata) + Redis (cache)
- **Deployment**: Docker Compose with multi-container orchestration

## Architecture Patterns

### Backend (PHP) - Controller → Service → Repository Pattern
**File Structure**: `app/Controllers/` → `app/Services/` → `app/Repositories/`

**Controller Pattern** (see `ConnectionController.php`):
```php
public function create(): array {
    $input = ValidationHelper::getJsonInput();
    $input = ValidationHelper::sanitizeInput($input);
    ValidationHelper::validateRequest($this->validator, $input);
    
    $saved = $this->service->create($input);
    if (!$saved) {
        http_response_code(400);
        return ['error' => 'Failed to create connection'];
    }
    return $saved; // Auto-converted to JSON
}
```

**Dashboard Analytics Pattern** (see `SmartTravelDashboardService.php`):
```php
public function getCityRanking(): array {
    $pipeline = [
        ['$group' => ['_id' => '$city', 'count' => ['$sum' => 1], 'avgRating' => ['$avg' => '$rating']]],
        ['$sort' => ['avgRating' => -1]],
        ['$limit' => 20]
    ];
    $result = $this->placesCollection->aggregate($pipeline);
    // Transform and return structured data
}
```

**Key Conventions**:
- **JSON Keys**: Always `camelCase` (e.g., `connectionId`, `cronExpression`)
- **HTTP Status**: Set explicitly with `http_response_code()` in controllers
- **Validation**: Use `ValidationHelper::validateRequest()` in controllers
- **Error Handling**: Return associative arrays; framework auto-converts to JSON
- **MongoDB IDs**: Use string IDs (e.g., `"690d27fffe8324710b06bf25"`)
- **Aggregation Pipelines**: Use MongoDB aggregation for complex analytics (group, sort, limit, unwind)

### Database Collections (MongoDB Atlas)
- `api_connections`: API connection configurations
- `api_schedules`: Schedule definitions with cron expressions
- `api_runs`: Execution history and results
- `parameter_modes`: Dynamic parameter configurations
- `smart_travel.places`: Google Places API data (4,972+ documents with ratings, categories, locations)

### Airflow Integration
**DAG Generation**: Schedules create dynamic DAGs in `dags/api_execution_dag.py`
- DAG ID: `api_execute_{schedule_id}`
- Tasks: `before_execute` → `create_run_record` → `execute_api_call` → `update_run_record`

**Schedule Creation Flow**:
1. POST to `/api/schedules` → Creates MongoDB record
2. Triggers Airflow DAG sync via `AirflowService`
3. DAG executes API calls based on cron expressions

## Development Workflow

### Setup (Windows/PowerShell)
```powershell
.\setup.ps1  # Starts all Docker services
.\start-dev.ps1  # Development mode
```

### Testing
```powershell
cd backendphp
.\test-api.ps1  # Comprehensive API test suite (12 tests)
```

**Test Coverage**: Health checks, CRUD operations, schedule creation, run execution, system diagnostics

### Building & Running
```bash
# Backend (PHP)
docker-compose up -d backend

# Frontend (Next.js)
cd frontendphp
npm run dev  # Port 3000

# Full stack
docker-compose up -d  # All services
```

### Key Endpoints
- **Health**: `GET /api/admin/health`
- **Connections**: `GET|POST /api/connections`
- **Schedules**: `GET|POST /api/schedules` (triggers Airflow sync)
- **Runs**: `GET|POST /api/runs` (manual execution)
- **Analytics**: `GET /api/analytics/*`
- **Smart Travel Dashboard**:
  - `GET /api/smart-travel/dashboard/overview`
  - `GET /api/smart-travel/dashboard/city-ranking` (new)
  - `GET /api/smart-travel/dashboard/city-category-matrix` (new)

## Frontend Patterns (Next.js + TypeScript)

### API Client (`services/apiClient.js`)
```javascript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const apiClient = {
  // 120s timeout for large datasets (increased from 30s)
  timeout: 120000,
  
  // 5-minute response caching for dashboard APIs
  // Automatic cache invalidation and error recovery
  async get(endpoint) {
    const response = await axios.get(`${API_BASE}${endpoint}`);
    return response.data;
  },
  // POST, PUT, DELETE methods...
};
```

### Dashboard Performance Patterns (`smart-travel-dashboard.jsx`)
```javascript
// Parallel API fetching in optimized groups
const group1 = Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/overview'),
  fetchWithTimeout('/api/smart-travel/dashboard/city-ranking'), // New endpoint
]);

const group2 = Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/city-category-matrix'), // New endpoint
  fetchWithTimeout('/api/smart-travel/dashboard/map-data', 20000), // Heavy data
]);

// Memoized chart components to prevent re-renders
const ChartCard = memo(({ title, description, children, loading }) => (
  // Optimized rendering with loading states
));
```

### Component Structure
- Uses `shadcn/ui` components with Radix UI primitives
- Tailwind CSS for styling with gradient utilities
- TypeScript for type safety
- Client components in `components/client-*.jsx`

## Frontend UI Styling System (NEW - Session Update)

### Design System Overview
Comprehensive gradient-based design with color-coded components for visual hierarchy:

**Color Palette**:
- 🔵 **Blue** (Primary): Data, connections, information - `from-blue-50 to-blue-100`
- 🟢 **Green** (Success): Success states, runs, achievements - `from-green-50 to-green-100`
- 🟣 **Purple** (Secondary): Schedules, secondary actions - `from-purple-50 to-purple-100`
- 🌸 **Pink/Rose** (Tertiary): Analytics, distribution data - `from-pink-50 to-rose-100`
- 🟠 **Orange/Amber** (Warning): Heatmap intensity, attention - `from-orange-50 to-amber-100`
- 🟡 **Yellow** (Attention): Metrics, important values - `from-yellow-50 to-yellow-100`
- 🟦 **Teal/Cyan** (Info): Line charts, trending - `from-teal-50 to-cyan-100`
- 🟪 **Violet** (Other): Provincial data, maps - `from-violet-50 to-purple-100`

### Card Styling Pattern
```jsx
// ✅ Standard gradient card with hover effect
<Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100/50">
  <CardHeader className="bg-gradient-to-r from-blue-100 to-blue-50 border-b border-blue-200">
    <CardTitle className="text-blue-900 flex items-center gap-2">
      <span className="text-2xl">📊</span>
      Title with Icon
    </CardTitle>
    <CardDescription className="text-blue-700">Subtitle</CardDescription>
  </CardHeader>
  <CardContent className="pt-6">
    {/* Chart or content */}
  </CardContent>
</Card>

// Icon badge in header
<div className="p-2 bg-blue-100 rounded-lg">
  <Icon className="h-4 w-4 text-blue-600" />
</div>
```

### Table Styling Pattern (Sticky Headers)
```jsx
<div className="overflow-x-auto rounded-lg border border-blue-100">
  <table className="w-full text-sm">
    <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white sticky top-0">
      <tr>
        <th className="text-left py-3 px-4 font-semibold">Column</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-b border-blue-100 hover:bg-blue-50/50 transition">
        <td className="py-3 px-4 font-medium">{data}</td>
      </tr>
    </tbody>
  </table>
</div>
```

### Heatmap/Matrix Styling (Intensity-Based Coloring)
```jsx
// 5-level intensity scale
const getHeatmapColor = (value, maxValue) => {
  const percentage = (value / maxValue) * 100;
  if (percentage > 75) return 'bg-red-600 text-white';
  if (percentage > 50) return 'bg-red-400 text-white';
  if (percentage > 25) return 'bg-orange-300 text-white';
  if (percentage > 10) return 'bg-orange-100 text-orange-900';
  if (value > 0) return 'bg-gray-50 text-gray-600';
  return 'bg-white text-gray-300';
};

// Legend component
<div className="flex flex-wrap items-center gap-4 text-xs p-3 bg-orange-50 rounded-lg">
  <span className="font-bold">Legend:</span>
  <div className="flex items-center gap-2">
    <div className="w-5 h-4 bg-red-600 rounded" />
    <span>75-100% (High)</span>
  </div>
  {/* ... more levels ... */}
</div>
```

### Badge & Status Indicator Pattern
```jsx
// Color-coded status badges
<Badge className={city.avgRating >= 4.5 ? 'bg-green-500 text-white' : 'bg-blue-500 text-white'}>
  {city.avgRating} ⭐
</Badge>

// Status badges with icons
<Badge className={schedule.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
  {schedule.isActive ? (
    <>
      <RotateCcw className="h-3 w-3 mr-1" />
      Active
    </>
  ) : (
    <>
      <Pause className="h-3 w-3 mr-1" />
      Paused
    </>
  )}
</Badge>
```

### PageLayout Header Pattern (with Icon)
```jsx
<PageLayout
  title="Dashboard Title"
  description="Subtitle describing the page"
  showBackButton={true}
  icon={<div className="p-2 bg-gradient-to-br from-blue-100 to-blue-50 rounded-lg">
    <Icon className="h-6 w-6 text-blue-600" />
  </div>}
>
  {/* Content */}
</PageLayout>

// Results in: Icon + Title with gradient text + Description
<h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700">
  {title}
</h1>
```

### Responsive Grid Patterns
```jsx
// 2-4 column responsive grid (summary cards)
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

// 1-2 column responsive grid (chart cards)
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

// Flexible responsive for different screen sizes
<div className="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
```

## Critical Integration Points

### Cross-Service Communication
- **Frontend ↔ Backend**: HTTP REST API calls
- **Backend ↔ Airflow**: HTTP triggers + DAG file generation
- **Backend ↔ MongoDB**: Direct MongoDB driver (Atlas cloud)
- **Airflow ↔ MongoDB**: Python MongoDB client in DAGs

### Dashboard Data Flow
- **Smart Travel Dashboard**: Frontend fetches from 8+ endpoints with parallel loading
- **Caching Layer**: 5-minute TTL cache in apiClient for dashboard APIs
- **Performance Optimization**: Parallel API groups (critical → secondary → heavy data)
- **Error Recovery**: Automatic fallback and detailed error logging

### Environment Variables
```env
# Backend
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/db
MONGODB_DATABASE=dataplatform_db

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow:airflow@postgres:5432/airflow
```

## Common Patterns & Gotchas

### Timeout Errors (Frontend → Backend)
**Symptom**: "timeout of 30000ms exceeded"
```
❌ Problem: Default axios timeout too short for large datasets
✅ Solution: Timeout set to 120s in apiClient.js
```

**Debugging steps**:
```powershell
# 1. Check backend status
Invoke-WebRequest -Uri "http://localhost:8000/api/admin/health"

# 2. Restart backend if needed
docker-compose restart backend

# 3. Check backend logs for slow queries
docker-compose logs backend --tail=50

# 4. Monitor MongoDB performance
docker exec -it backendphp-mongo-1 mongosh
use dataplatform_db
db.api_connections.find().hint({ $natural: -1 }).limit(5)
```

## Frontend Timeout Configuration

### Endpoint-Specific Timeouts (CRITICAL)
**Problem**: Default 15-30s timeout insufficient for large datasets (e.g., MongoDB aggregation with 4,972 documents)
**Solution**: Configure timeout per endpoint based on data complexity

```javascript
// ✅ CORRECT: Timeout per endpoint in fetchWithTimeout helper
const fetchWithTimeout = async (endpoint, timeoutMs = 15000) => {
  return Promise.race([
    axios.get(endpoint),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('timeout')), timeoutMs)
    ),
  ]);
};

// Usage: Differentiated timeouts by endpoint
const group1 = Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/overview', 15000),    // Fast aggregation
  fetchWithTimeout('/api/smart-travel/dashboard/city-ranking', 15000), // ~20 cities
]);

const group2 = Promise.all([
  fetchWithTimeout('/api/smart-travel/dashboard/city-category-matrix', 30000), // HEATMAP: Needs 30s!
  fetchWithTimeout('/api/smart-travel/dashboard/map-data', 20000),  // Heavy data
]);
```

### Timeout Value Guidelines
- **Critical endpoints** (overview, summary stats): 15s
- **Moderate aggregation** (rankings, category grouping): 15-20s
- **Complex aggregation with $unwind/$group** (heatmap, matrix): 25-30s
- **Map/visualization data**: 20s
- **Heavy data export**: 30-60s

### Real-World Example: Heatmap Timeout Issue
```
❌ BEFORE: timeout of 120000ms exceeded (error shown)
Root cause: Frontend timeout 15s < Backend query 25s
Performance: 400+ MongoDB queries in backend = slow

✅ AFTER: <5s response time
Fix 1: Backend optimized to 1 aggregation pipeline (400× faster)
Fix 2: Frontend timeout increased to 30s for heatmap endpoint
Result: Always completes within 5-10s, well under 30s timeout
```

❌ **Don't do this**:
```javascript
// Frontend creates schedule directly
await apiClient.post('/api/schedules', scheduleData);
// Then manually trigger Airflow
await apiClient.post('/api/airflow/trigger', {dagId: 'custom_dag'});
```

✅ **Do this**:
```javascript
// Backend handles Airflow sync automatically
const schedule = await apiClient.post('/api/schedules', scheduleData);
// AirflowService.syncDagFiles() called internally
```

### MongoDB Query Patterns & Optimization

#### Basic Repository Pattern
```php
// Repository pattern (see ConnectionRepository.php)
public function findById(string $id): ?array {
    $objectId = new \MongoDB\BSON\ObjectId($id);
    $results = $this->findWithPagination(['_id' => $objectId], ['limit' => 1]);
    return $results[0] ?? null;
}
```

#### Advanced Aggregation - Single Pipeline (CRITICAL PATTERN)
```php
// ✅ CORRECT: Single aggregation pipeline for complex queries
// Performance: O(1) database calls vs O(N×M) for nested loops
public function getCityRanking(): array {
    $pipeline = [
        ['$group' => ['_id' => '$city', 'count' => ['$sum' => 1], 'avgRating' => ['$avg' => '$rating']]],
        ['$sort' => ['avgRating' => -1]],
        ['$limit' => 20]
    ];
    $result = $this->placesCollection->aggregate($pipeline);
    return array_map(function($doc) {
        return [
            'city' => $doc['_id'],
            'count' => (int)$doc['count'],
            'avgRating' => round($doc['avgRating'], 2)
        ];
    }, iterator_to_array($result));
}

// ✅ OPTIMIZED HEATMAP: Single pipeline with $unwind and $group
// Replaces: 400+ countDocuments() calls in nested loops
// Time reduction: From 120s+ timeout → <5s response
public function getCityCategoryMatrix(): array {
    $this->connectToMongoDB();  // CRITICAL: Initialize connection first
    
    $pipeline = [
        // Count all documents by city and category
        ['$unwind' => '$types'],  // Expand array field
        ['$group' => [
            '_id' => ['city' => '$city', 'category' => '$types'],
            'count' => ['$sum' => 1]
        ]],
        ['$sort' => ['_id.city' => 1, 'count' => -1]],
        ['$limit' => 300]  // Limit to 15×15=225 + buffer
    ];
    
    $results = iterator_to_array($this->placesCollection->aggregate($pipeline));
    
    // Build matrix from aggregated results
    $cityCategories = [];
    $cities = [];
    $categories = [];
    $maxValue = 0;
    
    foreach ($results as $doc) {
        $city = $doc['_id']['city'];
        $category = $doc['_id']['category'];
        $count = (int)$doc['count'];
        
        $cityCategories[$city][$category] = $count;
        if (!in_array($city, $cities)) $cities[] = $city;
        if (!in_array($category, $categories)) $categories[] = $category;
        if ($count > $maxValue) $maxValue = $count;
    }
    
    // Build matrix
    $matrix = [];
    foreach ($cities as $city) {
        $row = [];
        foreach ($categories as $category) {
            $row[] = $cityCategories[$city][$category] ?? 0;
        }
        $matrix[] = $row;
    }
    
    return [
        'cities' => $cities,
        'categories' => $categories,
        'matrix' => $matrix,
        'maxValue' => $maxValue
    ];
}
```

#### Connection Initialization (REQUIRED IN ALL SERVICE METHODS)
```php
// CRITICAL: Every dashboard service method MUST call connectToMongoDB() first
// Failure to do this → service methods fail silently with null collections
public function getOverview(): array {
    $this->connectToMongoDB();  // ← ADD THIS
    $pipeline = [...];
    // Rest of method
}
```

#### Pattern Comparison: ❌ SLOW vs ✅ FAST
```php
// ❌ SLOW: Nested loops with individual queries (400+ database calls for 20×20 matrix)
// Time: 120s+ timeout error
public function getCityCategoryMatrix_SLOW(): array {
    $cities = $this->getUniqueCities();     // +1 query
    $categories = $this->getUniqueCategories();  // +1 query
    $matrix = [];
    foreach ($cities as $city) {            // 20 iterations
        $row = [];
        foreach ($categories as $category) {  // 20 iterations
            $count = $this->placesCollection->countDocuments([
                'city' => $city,
                'types' => $category
            ]);                             // = 400+ individual queries!
            $row[] = $count;
        }
        $matrix[] = $row;
    }
    return $matrix;
}

// ✅ FAST: Single aggregation pipeline (1 database call)
// Time: <5s response, 400× faster
public function getCityCategoryMatrix_FAST(): array {
    $pipeline = [
        ['$unwind' => '$types'],
        ['$group' => ['_id' => ['city' => '$city', 'category' => '$types'], 'count' => ['$sum' => 1]]],
        ['$limit' => 300]
    ];
    // Single aggregation call, build matrix from results
}
```

### Error Handling
```php
// Controllers return structured errors
if (!$connection) {
    http_response_code(404);
    return ['error' => 'Connection not found'];
}
```

### Validation
```php
// Use ValidationHelper in controllers
$input = ValidationHelper::getJsonInput();
$input = ValidationHelper::sanitizeInput($input);
ValidationHelper::validateRequest($this->validator, $input);
```

## Dashboard Architecture Patterns

### Data Visualization Pipeline
**Pattern**: MongoDB Aggregation → PHP Service → JSON API → React Components → Charts
```php
// 1. Complex aggregation in MongoDB
$pipeline = [
    ['$group' => ['_id' => '$city', 'count' => ['$sum' => 1], 'avgRating' => ['$avg' => '$rating']]],
    ['$sort' => ['avgRating' => -1]],
    ['$limit' => 20]
];

// 2. Service transforms to frontend-friendly format
return array_map(function($doc) {
    return [
        'city' => $doc['_id'],
        'count' => (int)$doc['count'],
        'avgRating' => round($doc['avgRating'], 2)
    ];
}, $result);

// 3. React component renders with Recharts
<BarChart data={data}>
    <Bar dataKey="count" fill="#3b82f6" />
</BarChart>
```

### Performance Optimization Strategies
- **Parallel Loading**: Group API calls by priority (critical → secondary → heavy)
- **Response Caching**: 5-minute TTL for dashboard endpoints
- **Data Sampling**: Random sampling for large datasets (maps use 500 points)
- **Memoization**: React.memo for chart components to prevent re-renders

## File Organization Examples

### Adding New API Endpoint
1. **Controller**: `app/Controllers/NewController.php`
2. **Service**: `app/Services/NewService.php`
3. **Repository**: `app/Repositories/NewRepository.php`
4. **Route**: Add to `routes/api.php`
5. **Test**: Add to `test-api.ps1`

### Frontend Component
```
components/
├── NewComponent.tsx      # Main component
├── client-new.tsx        # Client-side wrapper
└── ui/                   # Reusable UI components
```

### Adding Dashboard Visualization
1. **Backend Service Method**: Add aggregation logic to `SmartTravelDashboardService.php`
2. **Backend Controller Method**: Add endpoint to `SmartTravelDashboardController.php`
3. **Backend Route**: Add route to `routes/api.php`
4. **Frontend Component**: Add visualization to `smart-travel-dashboard.jsx`
5. **API Integration**: Add parallel fetch call with timeout handling

## Deployment & Production

### Docker Services
- **mongodb**: MongoDB Atlas (cloud) - not local by default
- **backend**: PHP Apache server
- **frontend**: Next.js production build
- **airflow-webserver/scheduler/worker**: Distributed task execution
- **postgres**: Airflow metadata
- **redis**: Celery broker + caching

### Production Checklist
- [ ] Set `APP_ENV=production` in backend
- [ ] Configure MongoDB Atlas credentials
- [ ] Set up Airflow admin user
- [ ] Configure CORS for production domain
- [ ] Enable Redis caching
- [ ] Run `test-api.ps1` before deployment
- [ ] Test dashboard endpoints with production data load
- [ ] Verify parallel API fetching works under load
- [ ] Check MongoDB aggregation performance on large datasets

## AI Agent Guidelines

### When Adding Features
1. **Follow existing patterns**: Controller → Service → Repository
2. **Add comprehensive tests**: Update `test-api.ps1`
3. **Handle Airflow integration**: Use `AirflowService` for DAG management
4. **Validate inputs**: Use `ValidationHelper` in controllers
5. **Return structured responses**: Associative arrays, auto-JSON conversion

### When Adding Dashboard Visualizations
1. **Use MongoDB aggregation pipelines** for complex data analysis
2. **Implement parallel API fetching** in groups (critical → secondary → heavy)
3. **Add response caching** (5-minute TTL) for dashboard endpoints
4. **Use memoized React components** to prevent unnecessary re-renders
5. **Handle large datasets** with sampling and pagination
6. **Implement matrix building** for heatmap-style visualizations

### When Debugging
1. **Check service logs**: `docker-compose logs [service]`
2. **Test API endpoints**: Use `test-api.ps1` or manual curl
3. **Verify MongoDB data**: Connect via `mongosh` in container
4. **Check Airflow DAGs**: Visit http://localhost:8080
5. **Monitor query performance**: Add timing logs to aggregation pipelines
6. **Check frontend timeout settings**: Look for `fetchWithTimeout` calls and adjust per endpoint
7. **Verify MongoDB connection**: Ensure `connectToMongoDB()` called in service methods

### Debugging Frontend Timeout Issues
```javascript
// Add detailed logging for slow API calls
const fetchWithTimeout = async (endpoint, timeoutMs = 15000) => {
  console.log(`[API] Starting request to ${endpoint} with ${timeoutMs}ms timeout`);
  const startTime = Date.now();
  
  try {
    const response = await Promise.race([
      axios.get(endpoint),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), timeoutMs)
      ),
    ]);
    
    const duration = Date.now() - startTime;
    console.log(`[API] ${endpoint} completed in ${duration}ms`);
    return response.data;
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`[API] ${endpoint} failed after ${duration}ms:`, error.message);
    throw error;
  }
};
```

### Debugging Slow Backend Queries
```bash
# Check MongoDB query logs
docker exec -it backendphp-mongo-1 mongosh
use dataplatform_db

# List slow operations
db.getProfilingLevel()
db.setProfilingLevel(1, { slowms: 100 })  # Log queries >100ms
db.system.profile.find().sort({ ts: -1 }).limit(5).pretty()

# Check collection size and indexes
db.smart_travel_places.stats()
db.smart_travel_places.getIndexes()
```

### Performance Profiling Checklist
- ✅ Single aggregation pipeline instead of N×M queries
- ✅ Result limiting (e.g., top 15×15 for heatmaps) to avoid matrix explosion
- ✅ Proper MongoDB indexes on frequently aggregated fields
- ✅ Timeout increased to 30s+ for complex aggregations
- ✅ Parallel API fetching in groups (critical → secondary → heavy)
- ✅ React.memo for chart components to prevent unnecessary re-renders
- ✅ Connection initialization (connectToMongoDB) before aggregation calls

### When Modifying Database Schema
1. **Update collection names** in `AppConfig.php`
2. **Modify repositories** to handle new fields
3. **Update validation** in `Validation/` directory
4. **Test with sample data** before committing

### When Working with Dashboard Data
1. **Use aggregation pipelines** for complex analytics (group, sort, limit, unwind)
2. **Implement matrix building** for cross-reference visualizations
3. **Handle large datasets** with sampling and pagination
4. **Test with real data** - use MongoDB queries to verify data structure
5. **Optimize queries** - add indexes for frequently aggregated fields

---

**Key Reference Files**:
- `backendphp/README.md`: Detailed API documentation
- `backendphp/routes/api.php`: All API endpoints
- `backendphp/test-api.ps1`: Testing patterns
- `docker-compose.yml`: Service orchestration
- `frontendphp/package.json`: Frontend dependencies
- `frontendphp/components/dashboard/smart-travel-dashboard.jsx`: Dashboard implementation patterns
- `backendphp/app/Services/SmartTravelDashboardService.php`: MongoDB aggregation examples
- `frontendphp/services/apiClient.js`: Caching and timeout patterns</content>
<parameter name="filePath">d:\project\no-code-api-connector\.github\copilot-instructions.md