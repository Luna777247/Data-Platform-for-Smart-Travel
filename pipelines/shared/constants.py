"""
Shared Constants
===============

Constants used across pipelines.
Theo RECOMMENDED_STRUCTURE.md - pipelines/shared/constants.py
"""

from enum import Enum


class PipelineStage(Enum):
    """Pipeline stages."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class DataSource(Enum):
    """Data sources."""
    OSM = "osm"
    GOOGLE_PLACES = "google"
    TRIPADVISOR = "tripadvisor"
    MANUAL = "manual"


class POICategory(Enum):
    """POI categories."""
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    ATTRACTION = "tourist_attraction"
    CAFE = "cafe"
    SHOPPING = "shopping_mall"
    PARK = "park"
    CINEMA = "cinema"
    MUSEUM = "museum"


class ProcessingStatus(Enum):
    """Processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Default configuration values
DEFAULT_BATCH_SIZE = 1000
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_QUALITY_THRESHOLD = 0.8

# Coordinate constants
MAX_LATITUDE = 90.0
MIN_LATITUDE = -90.0
MAX_LONGITUDE = 180.0
MIN_LONGITUDE = -180.0

# Quality score weights
COMPLETENESS_WEIGHT = 0.25
ACCURACY_WEIGHT = 0.25
CONSISTENCY_WEIGHT = 0.2
TIMELINESS_WEIGHT = 0.15
UNIQUENESS_WEIGHT = 0.15

# Pipeline config keys
CONFIG_BATCH_SIZE = "batch_size"
CONFIG_MAX_RETRIES = "max_retries"
CONFIG_TIMEOUT = "timeout_seconds"
CONFIG_QUALITY_THRESHOLD = "quality_threshold"
CONFIG_ENABLE_VALIDATION = "enable_validation"
CONFIG_ENABLE_DEDUPLICATION = "enable_deduplication"
CONFIG_ENABLE_ENRICHMENT = "enable_enrichment"

# File formats
FORMAT_JSON = "json"
FORMAT_PARQUET = "parquet"
FORMAT_CSV = "csv"

# Collection names
COLLECTION_BRONZE = "bronze_pois"
COLLECTION_SILVER = "silver_pois"
COLLECTION_GOLD = "gold_pois"
COLLECTION_PIPELINE_LOGS = "pipeline_logs"

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
