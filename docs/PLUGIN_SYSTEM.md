# Plugin System Architecture
## Hệ Thống Plugin cho Smart Tourism Data Platform

**Version:** 1.0  
**Created:** May 10, 2026  
**Status:** Implementation Ready

---

## 🎯 Mục tiêu

Biến hệ thống từ **hardcoded sources** → **truly dynamic plugin architecture**:

- ✅ Thêm nguồn dữ liệu mới **không cần code**
- ✅ Đăng ký collector qua **API**
- ✅ Load pipeline từ **metadata/JSON**
- ✅ Hot-swap collectors **runtime**

---

## 🏗️ Kiến trúc Plugin

```
┌─────────────────────────────────────────────────────────────┐
│                    PLUGIN REGISTRY                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Source Plugins                                         │ │
│  │  ├─ google_places → GooglePlacesCollector               │ │
│  │  ├─ osm → OSMCollector                                  │ │
│  │  ├─ tripadvisor → TripAdvisorCollector (NEW)           │ │
│  │  └─ yelp → YelpCollector (NEW)                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Transformer Plugins                                  │ │
│  │  ├─ rating_enricher → RatingEnricher                  │ │
│  │  ├─ category_mapper → CategoryEnricher                │ │
│  │  └─ custom_transform → UserDefinedTransformer        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Register / Load
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PLUGIN LOADER                              │
│  - Load from MongoDB (plugin_registry collection)           │
│  - Load from local filesystem (plugins/)                    │
│  - Hot-reload support                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Execute
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                PIPELINE EXECUTION                            │
│  Source → Collect → Transform → Store                       │
│     ↑                                   ↑                   │
│  Plugin                               Plugin                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Plugin Types

### 1. Source Plugins (Collectors)

```python
# Interface cho data sources
class BaseCollector(ABC):
    @abstractmethod
    async def collect(self, city: str, category: str, **kwargs) -> List[Dict]:
        """Thu thập dữ liệu từ nguồn"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict) -> bool:
        """Validate plugin configuration"""
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Tên nguồn (unique identifier)"""
        pass
```

**Ví dụ Implementations:**
- `GooglePlacesCollector` - Google Places API
- `OSMCollector` - OpenStreetMap Overpass API
- `TripAdvisorCollector` - TripAdvisor Content API
- `YelpCollector` - Yelp Fusion API

### 2. Transformer Plugins (Enrichers)

```python
# Interface cho data transformers
class BaseTransformer(ABC):
    @abstractmethod
    async def transform(self, data: List[Dict], **kwargs) -> List[Dict]:
        """Transform dữ liệu"""
        pass
    
    @property
    @abstractmethod
    def transformer_name(self) -> str:
        """Tên transformer"""
        pass
```

---

## 🗄️ Plugin Registry (MongoDB)

### Collection: `plugin_registry`

```javascript
{
  "_id": ObjectId,
  "plugin_id": "google_places_collector",
  "plugin_type": "source",  // "source" | "transformer"
  "name": "Google Places Collector",
  "version": "1.0.0",
  "description": "Collect POI data from Google Places API",
  "class_path": "src.collectors.google_places_collector.GooglePlacesCollector",
  "config_schema": {
    "api_key": {"type": "string", "required": true},
    "rate_limit": {"type": "integer", "default": 100},
    "timeout": {"type": "integer", "default": 30}
  },
  "default_config": {
    "rate_limit": 100,
    "timeout": 30
  },
  "enabled": true,
  "created_at": ISODate("2026-05-10T10:00:00Z"),
  "updated_at": ISODate("2026-05-10T10:00:00Z"),
  "created_by": "system"
}
```

### Collection: `source_configs`

```javascript
{
  "_id": ObjectId,
  "source_id": "tripadvisor_hanoi",
  "plugin_id": "tripadvisor_collector",
  "name": "TripAdvisor Hanoi",
  "config": {
    "api_key": "ta_api_key_here",
    "city": "hanoi",
    "language": "vi"
  },
  "enabled": true,
  "created_at": ISODate("2026-05-10T10:00:00Z")
}
```

---

## 🔌 API Endpoints

### Plugin Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/plugins` | List all plugins |
| `GET` | `/api/v1/plugins/{id}` | Get plugin details |
| `POST` | `/api/v1/plugins` | Register new plugin |
| `PUT` | `/api/v1/plugins/{id}` | Update plugin config |
| `DELETE` | `/api/v1/plugins/{id}` | Disable/remove plugin |
| `POST` | `/api/v1/plugins/{id}/test` | Test plugin connection |

### Source Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/sources` | List configured sources |
| `POST` | `/api/v1/sources` | Add new source instance |
| `PUT` | `/api/v1/sources/{id}` | Update source config |
| `DELETE` | `/api/v1/sources/{id}` | Remove source |
| `POST` | `/api/v1/sources/{id}/collect` | Trigger collection |

---

## 🚀 Usage Examples

### 1. Register New Plugin

```bash
# Register TripAdvisor collector
curl -X POST "http://localhost:8000/api/v1/plugins" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_id": "tripadvisor_collector",
    "plugin_type": "source",
    "name": "TripAdvisor Collector",
    "version": "1.0.0",
    "description": "Collect from TripAdvisor Content API",
    "class_path": "src.plugins.collectors.tripadvisor.TripAdvisorCollector",
    "config_schema": {
      "api_key": {"type": "string", "required": true},
      "base_url": {"type": "string", "default": "https://api.content.tripadvisor.com"}
    }
  }'
```

### 2. Configure Source Instance

```bash
# Create source instance
curl -X POST "http://localhost:8000/api/v1/sources" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "source_id": "tripadvisor_hanoi",
    "plugin_id": "tripadvisor_collector",
    "name": "TripAdvisor Hanoi",
    "config": {
      "api_key": "YOUR_API_KEY",
      "city": "hanoi"
    }
  }'
```

### 3. Create Dynamic Pipeline

```bash
# Create pipeline using registered sources
curl -X POST "http://localhost:8000/api/v1/pipelines" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "pipeline_name": "multi_source_pipeline",
    "sources": ["tripadvisor_hanoi", "google_places_hanoi"],
    "transformers": ["rating_enricher", "category_mapper"],
    "schedule": "0 2 * * *"
  }'
```

### 4. Run Collection

```bash
# Collect from specific source
curl -X POST "http://localhost:8000/api/v1/sources/tripadvisor_hanoi/collect" \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Plugin Development Guide

### 1. Create Custom Collector

```python
# src/plugins/collectors/custom_collector.py
from src.plugins.base import BaseCollector

class CustomCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "custom_source"
    
    async def validate_config(self, config: dict) -> bool:
        required = ["api_endpoint", "api_key"]
        return all(k in config for k in required)
    
    async def collect(self, city: str, category: str, **kwargs) -> list:
        # Implementation here
        data = await self._fetch_data(city, category)
        return self._normalize(data)
```

### 2. Register via Code

```python
from src.plugins.registry import plugin_registry

plugin_registry.register_collector(
    name="custom_source",
    collector_class=CustomCollector,
    config_schema={...}
)
```

---

## 🔄 Migration từ Hardcoded

### Bước 1: Convert existing collectors

```python
# Chuyển OSMCollector, GooglePlacesCollector → Plugin format
# (Không cần thay đổi code, chỉ cần register)
```

### Bước 2: Register vào database

```javascript
// Migration script sẽ tự động register existing collectors
db.plugin_registry.insertMany([
  {
    "plugin_id": "google_places_collector",
    "plugin_type": "source",
    "name": "Google Places Collector",
    "class_path": "src.collectors.google_places_collector.GooglePlacesCollector",
    "enabled": true
  },
  {
    "plugin_id": "osm_collector", 
    "plugin_type": "source",
    "name": "OSM Collector",
    "class_path": "src.collectors.osm_collector.OSMCollector",
    "enabled": true
  }
])
```

---

## 📊 Benefits

| Feature | Before | After |
|---------|--------|-------|
| Add new source | Code + Deploy | API call only |
| Configure source | .env file | Database + API |
| Source count | 2 (fixed) | Unlimited |
| Developer needed | Yes | No (for config) |
| Hot-swap | No | Yes |

---

## 🆚 So sánh: Before vs After

### Before (Hardcoded)
```python
# src/collectors/__init__.py
__all__ = ['OSMCollector', 'GooglePlacesCollector']
# Muốn thêm TripAdvisor? Cần sửa code!
```

### After (Plugin System)
```python
# src/plugins/registry.py
# Đăng ký qua API:
POST /api/v1/plugins
{"plugin_id": "tripadvisor_collector", ...}

# Tự động available!
collector = registry.get_collector("tripadvisor_collector")
```

---

## 🎯 Implementation Checklist

- [ ] Base interfaces (BaseCollector, BaseTransformer)
- [ ] Plugin Registry (MongoDB collection + Python class)
- [ ] Plugin Loader (dynamic import)
- [ ] API endpoints (plugins, sources)
- [ ] Migration (register existing collectors)
- [ ] Documentation
- [ ] Tests

---

## 🔗 Related Documents

- [SYSTEM_UPDATE_MAY2026.md](./SYSTEM_UPDATE_MAY2026.md) - Recent updates
- [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md) - API patterns

---

**Document Version:** 1.0  
**Last Updated:** May 10, 2026
