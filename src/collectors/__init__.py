"""
Collectors Package
==================
Data collectors cho Smart Tourism Data Platform

Collectors:
- OSMCollector: OpenStreetMap data collection
- GooglePlacesCollector: Google Places via RapidAPI (18 rotating keys)

Usage:
    from src.collectors import OSMCollector, GooglePlacesCollector
"""

from .osm_collector import OSMCollector
from .google_places_collector import GooglePlacesCollector

__all__ = ['OSMCollector', 'GooglePlacesCollector']
