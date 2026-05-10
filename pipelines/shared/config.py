"""
Shared Configuration
====================

Shared configuration cho pipelines.
Theo RECOMMENDED_STRUCTURE.md - pipelines/shared/config.py
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class PipelineConfig:
    """
    Shared pipeline configuration.
    
    Loads và provides access to:
    - Pipeline settings
    - City configurations
    - POI type configurations
    - Source configurations
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "pipelines/config")
        self._config: Dict[str, Any] = {}
        self._cities: Dict[str, Any] = {}
        self._poi_types: Dict[str, Any] = {}
        self._sources: Dict[str, Any] = {}
        self._load_all()
    
    def _load_all(self):
        """Load tất cả configuration files."""
        self._load_pipeline_config()
        self._load_cities()
        self._load_poi_types()
        self._load_sources()
    
    def _load_pipeline_config(self):
        """Load pipeline_config.json."""
        path = self.config_dir / "pipeline_config.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
    
    def _load_cities(self):
        """Load cities.json."""
        path = self.config_dir / "cities.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self._cities = json.load(f)
    
    def _load_poi_types(self):
        """Load poi_types.json."""
        path = self.config_dir / "poi_types.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self._poi_types = json.load(f)
    
    def _load_sources(self):
        """Load sources.json."""
        path = self.config_dir / "sources.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self._sources = json.load(f)
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get pipeline configuration."""
        return self._config
    
    @property
    def cities(self) -> Dict[str, Any]:
        """Get cities configuration."""
        return self._cities
    
    @property
    def poi_types(self) -> Dict[str, Any]:
        """Get POI types configuration."""
        return self._poi_types
    
    @property
    def sources(self) -> Dict[str, Any]:
        """Get sources configuration."""
        return self._sources
    
    def get_city_config(self, city: str) -> Dict[str, Any]:
        """Get configuration cho một city."""
        return self._cities.get(city, {})
    
    def get_poi_type_config(self, poi_type: str) -> Dict[str, Any]:
        """Get configuration cho một POI type."""
        return self._poi_types.get(poi_type, {})
    
    def get_source_config(self, source: str) -> Dict[str, Any]:
        """Get configuration cho một source."""
        return self._sources.get(source, {})
    
    def get_processing_config(self, layer: str) -> Dict[str, Any]:
        """Get processing configuration cho một layer."""
        return self._config.get("processing", {}).get(layer, {})


# Global config instance
_shared_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get shared pipeline configuration."""
    global _shared_config
    if _shared_config is None:
        _shared_config = PipelineConfig()
    return _shared_config


def reload_config():
    """Reload configuration from disk."""
    global _shared_config
    _shared_config = PipelineConfig()
