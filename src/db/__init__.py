"""
Database Package
================
Database layer cho Smart Tourism Data Platform

Components:
- models: MongoDB ODM models (Beanie documents)
- repositories: Data access layer (Repository Pattern)
- client: Database client singletons
- migrations: Database migration scripts

Supported Databases:
- MongoDB: Primary data store (POI, pipeline data)
- Redis: Caching và session storage

Example:
    from src.db.models import POI, PipelineExecution
    from src.db import get_database
    
    db = get_database()
    poi = await POI.find_one(POI.name == "Tokyo Tower")
"""

from .client import get_database, get_redis_pool

__all__ = [
    "get_database",
    "get_redis_pool",
]
