"""
Data Ingestion Package
======================
Data ingestion layer cho Smart Tourism Data Platform

This package handles collection of raw POI data from external sources
và chuyển đổi thành bronze layer records.

Modules:
- base_ingestion: Abstract base class cho all ingestion engines
- osm_ingestion: OpenStreetMap data ingestion implementation

Architecture:
    External APIs (OSM, Google Places)
           │
           ▼
    ┌─────────────────┐
    │ IngestionEngine │  ← Async data collection
    └─────────────────┘
           │
           ▼
    ┌─────────────────┐
    │ Bronze Records  │  ← Raw data với metadata
    └─────────────────┘

Example:
    from pipelines.ingestion import OSMIngestionEngine
    
    engine = OSMIngestionEngine()
    await engine.run_ingestion(city="tokyo", category="hotel")
"""

from .base_ingestion import BaseIngestionEngine
from .osm_ingestion import OSMIngestionEngine

__all__ = [
    "BaseIngestionEngine",
    "OSMIngestionEngine",
]