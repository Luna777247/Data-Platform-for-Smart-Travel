"""
Pipelines Package
==================
Data processing pipelines cho Smart Tourism Data Platform

Cấu trúc pipeline:
- ingestion: Data ingestion từ various sources (OSM, Google, etc.)
- bronze: Bronze layer processing - raw data cleaning
- silver: Silver layer processing - deduplication, normalization
- gold: Gold layer processing - enrichment, aggregation
- validators: Data validation và quality checks
- shared: Shared components, schemas, utilities
- enrichment: Data enrichment services
- orchestration: Pipeline orchestration và scheduling
- monitoring: Pipeline monitoring và alerting

Pipeline Layers:
    ┌─────────────┐
    │   Sources   │  ← OSM, Google Places, TripAdvisor
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Bronze    │  ← Raw data ingestion
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Silver    │  ← Cleaned, normalized
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │    Gold     │  ← Enriched, aggregated
    └─────────────┘

Example Usage:
    from pipelines.ingestion.osm_ingestion import OSMIngestionEngine
    
    engine = OSMIngestionEngine()
    await engine.run_ingestion(city="tokyo", category="hotel")
"""

__version__ = "1.0.0"
__author__ = "Smart Tourism Team"

from .shared.utils import setup_logging, make_ukey

__all__ = [
    "setup_logging",
    "make_ukey",
]
