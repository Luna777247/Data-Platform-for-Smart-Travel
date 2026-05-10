# Frontend Admin Dashboard - Design Document

## 📋 Tổng Quan

**Mục tiêu:** Xây dựng giao diện quản trị thông minh cho Smart Tourism Platform  
**Người dùng:** Admin, Data Operators, System Managers  
**Tech Stack:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui  
**API Backend:** Sử dụng toàn bộ 41 API endpoints có sẵn (không cần sửa backend)

---

## 🏗️ Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────┐
│                    ADMIN DASHBOARD                           │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  Sidebar Navigation    │    Main Content Area     │     │
│  │  - Dashboard            │    - Dynamic Content     │     │
│  │  - Pipeline Control     │    - Forms & Tables      │     │
│  │  - POI Management       │    - Charts & Maps        │     │
│  │  - Analytics            │                         │     │
│  │  - System Settings      │                         │     │
│  └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│  • 41 API Endpoints (100% Working)                          │
│  • JWT Authentication                                        │
│  • Rate Limiting: 60 req/min                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Layout Structure

### 1. Admin Layout
```typescript
interface AdminLayoutProps {
  sidebar: React.ReactNode;
  header: React.ReactNode;
  content: React.ReactNode;
  footer?: React.ReactNode;
}

// Breakpoints
const BREAKPOINTS = {
  mobile: '640px',   // Sidebar collapses to drawer
  tablet: '768px',   // Sidebar mini version
  desktop: '1024px', // Full sidebar
  wide: '1280px',    // Extra content space
};
```

### 2. Navigation Structure
```typescript
const NAV_ITEMS = [
  {
    path: '/admin/dashboard',
    label: 'Dashboard',
    icon: 'LayoutDashboard',
    apiEndpoints: ['/api/v1/data/stats', '/api/v1/pipeline/dashboard'],
  },
  {
    path: '/admin/pipeline',
    label: 'Pipeline Control',
    icon: 'PlayCircle',
    apiEndpoints: ['/api/v1/pipeline/*'],
  },
  {
    path: '/admin/pois',
    label: 'POI Management',
    icon: 'MapPin',
    apiEndpoints: ['/api/v1/data/pois/*'],
  },
  {
    path: '/admin/analytics',
    label: 'Analytics',
    icon: 'BarChart3',
    apiEndpoints: ['/api/v1/data/stats', '/api/v1/pipeline/metrics'],
  },
  {
    path: '/admin/system',
    label: 'System',
    icon: 'Settings',
    apiEndpoints: ['/api/v1/admin/*', '/api/v1/monitoring/*'],
  },
];
```

---

## 🎨 Design System

### Colors
```typescript
const COLORS = {
  // Primary
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
  // Semantic
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  // Neutral
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    800: '#1f2937',
    900: '#111827',
  },
};
```

### Typography
```typescript
const TYPOGRAPHY = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
  sizes: {
    xs: '0.75rem',    // 12px - labels, captions
    sm: '0.875rem',   // 14px - body small
    base: '1rem',     // 16px - body
    lg: '1.125rem',   // 18px - lead
    xl: '1.25rem',    // 20px - h4
    '2xl': '1.5rem',  // 24px - h3
    '3xl': '1.875rem',// 30px - h2
    '4xl': '2.25rem', // 36px - h1
  };
};
```

### Spacing
```typescript
const SPACING = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
  '3xl': '4rem',   // 64px
};
```

---

## 🔌 API Integration Mapping

### Module 1: Authentication
| Feature | Component | API Endpoint | Method |
|---------|-----------|--------------|--------|
| Login | `LoginForm` | `/api/v1/auth/login` | POST |
| Get Profile | `UserProfile` | `/api/v1/auth/me` | GET |
| Refresh Token | `AuthProvider` | `/api/v1/auth/refresh` | POST |
| Logout | `LogoutButton` | `/api/v1/auth/logout` | POST |

### Module 2: Dashboard
| Feature | Component | API Endpoint | Polling |
|---------|-----------|--------------|---------|
| Stats Cards | `StatCards` | `/api/v1/data/stats` | 30s |
| Pipeline Status | `PipelineStatusWidget` | `/api/v1/pipeline/dashboard` | 5s |
| System Health | `HealthWidget` | `/health`, `/ready` | 30s |
| Data Layers | `DataLayersWidget` | `/api/v1/data/layers` | 60s |

### Module 3: Pipeline Control
| Feature | Component | API Endpoint | Real-time |
|---------|-----------|--------------|-----------|
| Start Pipeline | `PipelineStarter` | `/api/v1/pipeline/start` | - |
| Stop/Pause | `PipelineControls` | `/api/v1/pipeline/{action}/{id}` | - |
| Active List | `ActivePipelines` | `/api/v1/pipeline/active` | 5s polling |
| History | `PipelineHistory` | `/api/v1/pipeline/history` | Manual refresh |
| Metrics | `PipelineMetrics` | `/api/v1/pipeline/metrics` | 30s |
| Data Quality | `QualityReport` | `/api/v1/pipeline/data-quality` | Manual |
| Errors | `ErrorLog` | `/api/v1/pipeline/errors` | 10s |

### Module 4: POI Management
| Feature | Component | API Endpoint | Notes |
|---------|-----------|--------------|-------|
| POI List | `POIDataTable` | `/api/v1/data/pois` | Pagination |
| Search | `POISearch` | `/api/v1/data/pois/search` | Debounced |
| Detail | `POIDetailPanel` | `/api/v1/data/pois/{id}` | - |
| Nearby | `NearbyPOIMap` | `/api/v1/data/pois/nearby` | Map view |
| Cities Filter | `CityFilter` | `/api/v1/data/cities` | Cached |
| Categories Filter | `CategoryFilter` | `/api/v1/data/categories` | Cached |

### Module 5: Analytics
| Feature | Component | API Endpoint | Cache |
|---------|-----------|--------------|-------|
| Data Stats | `DataStatsChart` | `/api/v1/data/stats` | 5min |
| Pipeline Metrics | `PipelineMetricsChart` | `/api/v1/pipeline/metrics` | 5min |
| Quality Report | `QualityBreakdown` | `/api/v1/pipeline/data-quality` | 5min |
| Geographic | `GeographicStats` | `/api/v1/data/pois?city=*` | Aggregated |

### Module 6: System
| Feature | Component | API Endpoint | Admin Only |
|---------|-----------|--------------|------------|
| User List | `UserManagement` | `/api/v1/admin/users` | ✅ |
| Create User | `CreateUserDialog` | `/api/v1/admin/users` | ✅ |
| Delete User | `DeleteUserButton` | `/api/v1/admin/users/{id}` | ✅ |
| System Logs | `SystemLogs` | `/api/v1/admin/logs` | ✅ |
| Maintenance | `MaintenanceToggle` | `/api/v1/admin/maintenance` | ✅ |
| Cleanup | `CleanupButton` | `/api/v1/admin/cleanup` | ✅ |
| Dependencies | `DependenciesStatus` | `/api/v1/monitoring/dependencies` | - |
| Version Info | `VersionInfo` | `/api/v1/monitoring/version` | - |

---

## 🧩 Component Architecture

### 1. Layout Components
```typescript
// components/layout/AdminLayout.tsx
interface AdminLayoutProps {
  children: React.ReactNode;
}

// components/layout/Sidebar.tsx
interface SidebarProps {
  items: NavItem[];
  collapsed?: boolean;
  onToggle?: () => void;
}

// components/layout/Header.tsx
interface HeaderProps {
  title: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  user?: UserProfile;
}
```

### 2. Dashboard Components
```typescript
// components/admin/Dashboard/StatCards.tsx
interface StatCardsProps {
  stats: {
    totalPOIs: number;
    totalCities: number;
    activePipelines: number;
    dataQuality: number;
  };
  trend?: 'up' | 'down' | 'neutral';
}

// components/admin/Dashboard/PipelineStatus.tsx
interface PipelineStatusProps {
  pipelines: Pipeline[];
  onRefresh: () => void;
}

// components/admin/Dashboard/RecentActivity.tsx
interface RecentActivityProps {
  activities: Activity[];
  maxItems?: number;
}
```

### 3. Pipeline Components
```typescript
// components/admin/Pipeline/PipelineControl.tsx
interface PipelineControlProps {
  onStart: (type: PipelineType, config: any) => void;
  onStop: (id: string) => void;
  disabled?: boolean;
}

// components/admin/Pipeline/ActivePipelineList.tsx
interface ActivePipelineListProps {
  pipelines: ActivePipeline[];
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onStop: (id: string) => void;
}

// components/admin/Pipeline/PipelineHistoryTable.tsx
interface PipelineHistoryTableProps {
  history: PipelineExecution[];
  pagination: Pagination;
  onPageChange: (page: number) => void;
}
```

### 4. POI Components
```typescript
// components/admin/POI/POIDataTable.tsx
interface POIDataTableProps {
  pois: POI[];
  loading?: boolean;
  pagination: Pagination;
  onPageChange: (page: number) => void;
  onSort: (field: string, direction: 'asc' | 'desc') => void;
  onRowClick?: (poi: POI) => void;
  selectedRows?: string[];
  onSelectionChange?: (ids: string[]) => void;
}

// components/admin/POI/POISearch.tsx
interface POISearchProps {
  onSearch: (query: string) => void;
  filters: POIFilters;
  onFilterChange: (filters: POIFilters) => void;
  cities: string[];
  categories: string[];
}

// components/admin/POI/POIDetailPanel.tsx
interface POIDetailPanelProps {
  poi: POI | null;
  onClose: () => void;
  onEdit?: (poi: POI) => void;
}
```

### 5. Analytics Components
```typescript
// components/admin/Analytics/DataQualityChart.tsx
interface DataQualityChartProps {
  data: QualityData;
  type?: 'pie' | 'bar' | 'line';
}

// components/admin/Analytics/GeographicDistribution.tsx
interface GeographicDistributionProps {
  cities: CityStats[];
  onCityClick?: (city: string) => void;
}

// components/admin/Analytics/TrendChart.tsx
interface TrendChartProps {
  data: TimeSeriesData[];
  metric: 'pois' | 'quality' | 'pipelines';
  period: 'day' | 'week' | 'month';
}
```

### 6. System Components
```typescript
// components/admin/System/UserManagement.tsx
interface UserManagementProps {
  users: User[];
  onCreate: (user: NewUser) => void;
  onDelete: (id: string) => void;
  onEdit?: (user: User) => void;
}

// components/admin/System/SystemLogs.tsx
interface SystemLogsProps {
  logs: LogEntry[];
  filters: LogFilters;
  onFilterChange: (filters: LogFilters) => void;
  onExport: () => void;
}

// components/admin/System/HealthStatus.tsx
interface HealthStatusProps {
  services: ServiceHealth[];
  lastChecked: Date;
  onRefresh: () => void;
}
```

---

## 🔄 State Management

### React Query Configuration
```typescript
// hooks/useQueryConfig.ts
export const queryConfig = {
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
};

// Specific query configurations
export const pipelineQueryConfig = {
  staleTime: 5000, // 5 seconds for real-time data
  refetchInterval: 5000,
};

export const statsQueryConfig = {
  staleTime: 30000, // 30 seconds
  refetchInterval: 30000,
};
```

### Auth State
```typescript
// hooks/useAuth.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: Error | null;
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}
```

---

## 🛡️ Error Handling

### Error Boundaries
```typescript
// components/ErrorBoundary.tsx
interface ErrorBoundaryProps {
  fallback: React.ReactNode;
  children: React.ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

// Error types
enum ErrorType {
  API_ERROR = 'API_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

interface AppError {
  type: ErrorType;
  message: string;
  code?: string;
  retry?: () => void;
}
```

### Toast Notifications
```typescript
interface ToastConfig {
  duration: number;
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

// Usage
showToast({
  type: 'success',
  title: 'Pipeline Started',
  message: 'Collection pipeline #1234 has been started successfully.',
});

showToast({
  type: 'error',
  title: 'API Error',
  message: 'Failed to fetch POIs. Please try again.',
  action: { label: 'Retry', onClick: retryFn },
});
```

---

## 📝 Form Validation

### Using Zod
```typescript
import { z } from 'zod';

// Login form schema
const loginSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

// Pipeline start schema
const pipelineStartSchema = z.object({
  type: z.enum(['bronze', 'silver', 'gold', 'collection']),
  cities: z.array(z.string()).min(1, 'Select at least one city'),
  radius: z.number().min(100).max(5000).optional(),
  workers: z.number().min(1).max(10).optional(),
});

// User creation schema
const createUserSchema = z.object({
  username: z.string().min(3).max(20),
  email: z.string().email(),
  password: z.string().min(8),
  role: z.enum(['admin', 'operator', 'viewer']),
});
```

---

## 🗺️ Routes

### Route Configuration
```typescript
// router/routes.tsx
const routes = [
  {
    path: '/login',
    element: <LoginPage />,
    public: true,
  },
  {
    path: '/admin',
    element: <AdminLayout />,
    protected: true,
    children: [
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'pipeline', element: <PipelinePage /> },
      { path: 'pois', element: <POIManagementPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'system', element: <SystemPage /> },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
];
```

### Protected Route Logic
```typescript
// components/ProtectedRoute.tsx
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
```

---

## 🚀 Performance Optimization

### Code Splitting
```typescript
// Lazy load pages
const DashboardPage = lazy(() => import('./pages/admin/Dashboard'));
const PipelinePage = lazy(() => import('./pages/admin/Pipeline'));
const POIManagementPage = lazy(() => import('./pages/admin/POIs'));

// Preload on hover
const preloadPipelinePage = () => {
  const PipelinePage = import('./pages/admin/Pipeline');
};
```

### Virtualization
```typescript
// For large POI lists
import { Virtuoso } from 'react-virtuoso';

<Virtuoso
  style={{ height: '600px' }}
  data={pois}
  itemContent={(index, poi) => (
    <POICard poi={poi} index={index} />
  )}
  endReached={loadMore}
/>
```

### Memoization
```typescript
// Memoize expensive computations
const sortedPOIs = useMemo(() => {
  return [...pois].sort((a, b) => b.quality - a.quality);
}, [pois, sortConfig]);

// Memoize callbacks
const handleRowClick = useCallback((poi: POI) => {
  setSelectedPOI(poi);
}, []);
```

---

## 🧪 Testing Strategy

### Test Structure
```typescript
// Component tests
POIDataTable.test.tsx
PipelineControl.test.tsx
LoginForm.test.tsx

// Hook tests
usePipeline.test.tsx
useAuth.test.tsx
usePOIs.test.tsx

// Integration tests
Dashboard.integration.test.tsx
Pipeline.integration.test.tsx

// E2E tests
admin-flow.spec.ts
pipeline-management.spec.ts
```

### Mock Service Worker
```typescript
// mocks/handlers.ts
export const handlers = [
  rest.get('/api/v1/data/pois', (req, res, ctx) => {
    return res(ctx.json(mockPOIs));
  }),
  rest.post('/api/v1/auth/login', (req, res, ctx) => {
    return res(ctx.json({ token: 'mock-token', user: mockUser }));
  }),
];
```

---

## 📦 File Structure

```
frontend-admin/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── assets/
│   │   └── logo.svg
│   ├── components/
│   │   ├── admin/
│   │   │   ├── Dashboard/
│   │   │   ├── Pipeline/
│   │   │   ├── POI/
│   │   │   ├── Analytics/
│   │   │   └── System/
│   │   ├── ui/              # shadcn components
│   │   └── layout/
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePipeline.ts
│   │   ├── usePOIs.ts
│   │   └── useSystem.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── pages/
│   │   ├── admin/
│   │   └── auth/
│   ├── router/
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env
├── .env.example
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 📋 Implementation Checklist

### Phase 1: Setup (1 giờ)
- [ ] Initialize project with Vite + React + TypeScript
- [ ] Setup Tailwind CSS + shadcn/ui
- [ ] Configure React Query
- [ ] Setup React Router
- [ ] Create folder structure

### Phase 2: Auth & Layout (1 giờ)
- [ ] Login page
- [ ] Auth context + hooks
- [ ] Admin layout (sidebar, header)
- [ ] Protected routes
- [ ] Navigation

### Phase 3: Dashboard (1.5 giờ)
- [ ] Stat cards
- [ ] Pipeline status widget
- [ ] System health widget
- [ ] Data layers widget
- [ ] Auto-refresh logic

### Phase 4: Pipeline Control (2 giờ)
- [ ] Start pipeline form
- [ ] Active pipelines list
- [ ] Control buttons (stop/pause/resume)
- [ ] Progress indicators
- [ ] History table
- [ ] Error log

### Phase 5: POI Management (2 giờ)
- [ ] Data table with pagination
- [ ] Search with filters
- [ ] Detail panel
- [ ] Bulk actions
- [ ] Export functionality

### Phase 6: Analytics (1.5 giờ)
- [ ] Charts (Pie, Bar, Line)
- [ ] Quality metrics
- [ ] Geographic distribution
- [ ] Trend analysis

### Phase 7: System (1 giờ)
- [ ] User management
- [ ] System logs
- [ ] Health status
- [ ] Maintenance toggle

---

**Tổng thời gian ước tính: 10 giờ**

Bắt đầu triển khai? 🚀
