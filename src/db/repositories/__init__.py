"""
Database Repositories Package
=============================
Data access layer implementing Repository Pattern

Repositories:
- pipeline_repository: Pipeline CRUD operations
- poi_repository: POI CRUD operations
- monitoring_repository: Metrics và logs storage
- quality_repository: Data quality reports

Mỗi repository cung cấp abstract interface cho database operations,
cho phép dễ dàng thay đổi underlying data store nếu cần.

Example:
    from src.db.repositories import POIRepository
    
    repo = POIRepository()
    pois = await repo.find_by_city("tokyo")
    count = await repo.count_by_category("hotel")
"""

from src.db.repositories.poi_repository import POIRepository
from src.db.repositories.pipeline_repository import PipelineRepository
from src.db.repositories.monitoring_repository import MonitoringRepository
from src.db.repositories.quality_repository import QualityRepository

__all__ = [
    "POIRepository",
    "PipelineRepository",
    "MonitoringRepository",
    "QualityRepository",
]