"""
Core Package
============
Core infrastructure components cho Smart Tourism Data Platform

Modules:
- config: Configuration management
- database: Database connections (MongoDB, Redis)
- logging: Structured logging
"""

from .config import settings, get_settings
from .database import mongodb_manager, redis_manager, get_database, get_redis_pool
from .logging import setup_logging, get_logger, set_correlation_id

__all__ = [
    "settings",
    "get_settings",
    "mongodb_manager",
    "redis_manager",
    "get_database",
    "get_redis_pool",
    "setup_logging",
    "get_logger",
    "set_correlation_id",
]