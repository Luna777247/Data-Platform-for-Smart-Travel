"""
API Routes Package
=================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/api/routes/

Package này chứa tất cả API route modules.
Mỗi module định nghĩa một nhóm endpoints liên quan.

Modules:
- pipeline_management.py: Pipeline lifecycle APIs
- data_query.py: POI data query và search APIs
- monitoring.py: Health checks và metrics
- health.py: Legacy health check endpoints

Usage:
    from src.api.routes import pipeline_management
    app.include_router(pipeline_management.router)
"""

# ============================================================================
# MODULE EXPORTS
# ============================================================================

# Export các routers để dễ dàng import từ package level
# Ví dụ: from src.api.routes import pipeline_management

# Note: Không import trực tiếp ở đây để tránh circular imports
# Các modules nên được import trực tiếp từ file cần sử dụng

# ============================================================================
# ROUTES DOCUMENTATION
# ============================================================================
"""
Route Organization:
==================

1. pipeline_management.py
   - Prefix: /api/v1/pipeline
   - Endpoints: /start, /stop, /status, /history, /dashboard
   - Mục đích: Quản lý data pipelines

2. data_query.py
   - Prefix: /api/v1/data
   - Endpoints: /pois, /pois/{id}, /pois/nearby, /stats, /layers
   - Mục đích: Query và search POI data

3. monitoring.py
   - Prefix: None (root level)
   - Endpoints: /health, /ready, /metrics
   - Mục đích: Health checks và Prometheus metrics

4. health.py
   - Prefix: None (root level)
   - Endpoints: /health, /ready, /health/detailed
   - Mục đích: Legacy health check endpoints

Security:
========
- Public endpoints: /health, /ready, /metrics (không cần auth)
- Authenticated endpoints: Các endpoints còn lại yêu cầu JWT token

Example Usage:
=============
from fastapi import FastAPI
from src.api.routes import pipeline_management, data_query, monitoring

app = FastAPI()
app.include_router(pipeline_management.router)
app.include_router(data_query.router)
app.include_router(monitoring.router)
"""

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = []  # Không có exports ở package level, import trực tiếp từ modules