"""
Data Ingestion Package
======================
Data ingestion layer cho Smart Tourism Data Platform

This package handles collection of raw POI data from external sources
và chuyển đổi thành bronze layer records.

Modules:
- base_ingestion: Abstract base class cho all ingestion engines
- osm_ingestion: OpenStreetMap data ingestion implementation
- google_places_ingestion: Google Places API via RapidAPI

Data Sources:
1. OpenStreetMap (OSM): Free, community-driven, high coverage
2. Google Places (RapidAPI): Rich data, reviews, photos, via 18 API keys

Architecture:
    External APIs (OSM, Google Places via RapidAPI)
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
    >>> from pipelines.ingestion import OSMIngestionEngine, GooglePlacesIngestionEngine
    >>> 
    >>> # OSM Ingestion (Free)
    >>> osm_engine = OSMIngestionEngine()
    >>> await osm_engine.run_ingestion(city="tokyo", category="hotel")
    
    >>> # Google Places via RapidAPI (Rich data)
    >>> google_engine = GooglePlacesIngestionEngine()
    >>> await google_engine.ingest_city("tokyo", ["restaurant", "hotel"])
"""

from .base_ingestion import BaseIngestionEngine
from .osm_ingestion import OSMIngestionEngine
from .google_places_ingestion import GooglePlacesIngestionEngine

__all__ = [
    "BaseIngestionEngine",
    "OSMIngestionEngine",
    "GooglePlacesIngestionEngine",
]