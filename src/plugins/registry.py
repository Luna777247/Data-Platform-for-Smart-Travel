"""
Plugin Registry
===============
Central registry cho quản lý plugins.

Lưu trữ và quản lý tất cả registered plugins.
Support both in-memory và MongoDB-backed storage.
"""

import importlib
from typing import Dict, Type, Any, Optional, List
from datetime import datetime
from src.core.logging import get_logger

logger = get_logger(__name__)


class PluginRegistry:
    """
    Central registry cho plugins.
    
    Quản lý registration, lookup, và lifecycle của plugins.
    
    Usage:
        from src.plugins.registry import plugin_registry
        
        # Register
        plugin_registry.register_collector(
            name="tripadvisor",
            collector_class=TripAdvisorCollector,
            config_schema={...}
        )
        
        # Lookup
        collector = plugin_registry.get_collector("tripadvisor")
    """
    
    def __init__(self):
        # In-memory storage
        self._collectors: Dict[str, Dict[str, Any]] = {}
        self._transformers: Dict[str, Dict[str, Any]] = {}
        self._plugins: Dict[str, Dict[str, Any]] = {}  # All plugins by ID
        
        # Loaded instances cache
        self._instances: Dict[str, Any] = {}
    
    def register_collector(
        self,
        name: str,
        collector_class: Type,
        config_schema: Optional[Dict[str, Any]] = None,
        default_config: Optional[Dict[str, Any]] = None,
        description: str = "",
        version: str = "1.0.0"
    ) -> bool:
        """
        Register a new collector plugin.
        
        Args:
            name: Unique plugin name (e.g., "google_places", "tripadvisor")
            collector_class: Class implementing BaseCollector
            config_schema: JSON schema for config validation
            default_config: Default configuration values
            description: Plugin description
            version: Semantic version string
            
        Returns:
            True if registered successfully
            
        Example:
            from src.collectors.google_places_collector import GooglePlacesCollector
            
            registry.register_collector(
                name="google_places",
                collector_class=GooglePlacesCollector,
                config_schema={
                    "api_key": {"type": "string", "required": True},
                    "rate_limit": {"type": "integer", "default": 100}
                },
                default_config={"rate_limit": 100}
            )
        """
        try:
            if name in self._collectors:
                logger.warning(f"⚠️ Collector '{name}' already registered. Overwriting.")
            
            self._collectors[name] = {
                "name": name,
                "class": collector_class,
                "type": "source",
                "config_schema": config_schema or {},
                "default_config": default_config or {},
                "description": description,
                "version": version,
                "registered_at": datetime.now().isoformat()
            }
            
            self._plugins[name] = self._collectors[name]
            
            logger.info(f"✅ Registered collector: {name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register collector {name}: {e}")
            return False
    
    def register_transformer(
        self,
        name: str,
        transformer_class: Type,
        config_schema: Optional[Dict[str, Any]] = None,
        default_config: Optional[Dict[str, Any]] = None,
        description: str = "",
        version: str = "1.0.0"
    ) -> bool:
        """Register a transformer plugin."""
        try:
            if name in self._transformers:
                logger.warning(f"⚠️ Transformer '{name}' already registered. Overwriting.")
            
            self._transformers[name] = {
                "name": name,
                "class": transformer_class,
                "type": "transformer",
                "config_schema": config_schema or {},
                "default_config": default_config or {},
                "description": description,
                "version": version,
                "registered_at": datetime.now().isoformat()
            }
            
            self._plugins[name] = self._transformers[name]
            
            logger.info(f"✅ Registered transformer: {name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register transformer {name}: {e}")
            return False
    
    def get_collector(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get a collector instance by name.

        Args:
            name: Plugin name
            config: Optional configuration override

        Returns:
            Collector instance or None if not found

        Example:
            collector = registry.get_collector("google_places", config={"api_key": "xxx"})
            data = await collector.collect(city="hanoi", category="restaurant")
        """
        try:
            if name not in self._collectors:
                logger.error(f"❌ Collector '{name}' not found in registry")
                return None

            # Create instance
            plugin_info = self._collectors[name]
            collector_class = plugin_info["class"]

            # Merge configs
            final_config = {**plugin_info.get("default_config", {}), **(config or {})}

            # Instantiate - try with config kwarg first, fall back to no args
            try:
                instance = collector_class(config=final_config)
            except TypeError:
                # If class doesn't accept config kwarg, try without it
                try:
                    instance = collector_class()
                except Exception as e2:
                    logger.error(f"❌ Failed to instantiate {name} without config: {e2}")
                    return None

            logger.debug(f"🔧 Created collector instance: {name}")
            return instance

        except Exception as e:
            logger.error(f"❌ Failed to create collector {name}: {str(e)}", exc_info=True)
            return None
    
    def get_transformer(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get a transformer instance by name."""
        try:
            if name not in self._transformers:
                logger.error(f"❌ Transformer '{name}' not found")
                return None
            
            plugin_info = self._transformers[name]
            transformer_class = plugin_info["class"]
            
            final_config = {**plugin_info.get("default_config", {}), **(config or {})}
            instance = transformer_class(config=final_config)
            
            return instance
            
        except Exception as e:
            logger.error(f"❌ Failed to create transformer {name}: {e}")
            return None
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name to remove
            
        Returns:
            True if removed
        """
        if name in self._collectors:
            del self._collectors[name]
            del self._plugins[name]
            logger.info(f"🗑️ Unregistered collector: {name}")
            return True
            
        if name in self._transformers:
            del self._transformers[name]
            del self._plugins[name]
            logger.info(f"🗑️ Unregistered transformer: {name}")
            return True
            
        logger.warning(f"⚠️ Plugin '{name}' not found for unregister")
        return False
    
    def list_collectors(self) -> List[Dict[str, Any]]:
        """List all registered collectors."""
        return [
            {
                "name": info["name"],
                "type": info["type"],
                "version": info["version"],
                "description": info["description"],
                "registered_at": info["registered_at"]
            }
            for info in self._collectors.values()
        ]
    
    def list_transformers(self) -> List[Dict[str, Any]]:
        """List all registered transformers."""
        return [
            {
                "name": info["name"],
                "type": info["type"],
                "version": info["version"],
                "description": info["description"]
            }
            for info in self._transformers.values()
        ]
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered plugins."""
        return self.list_collectors() + self.list_transformers()
    
    def is_registered(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugins
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin metadata without instantiating."""
        if name in self._plugins:
            info = self._plugins[name].copy()
            info.pop("class", None)  # Remove class reference
            return info
        return None
    
    def get_config_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get config schema for a plugin."""
        info = self._plugins.get(name)
        return info.get("config_schema") if info else None


# Global registry instance
plugin_registry = PluginRegistry()


async def initialize_plugins():
    """
    Initialize plugin system - register built-in plugins.
    
    Called at application startup.
    """
    logger.info("🔌 Initializing plugin system...")
    
    # Import and register built-in collectors
    try:
        from src.collectors.google_places_collector import GooglePlacesCollector
        from src.collectors.osm_collector import OSMCollector
        
        # Register Google Places
        plugin_registry.register_collector(
            name="google_places",
            collector_class=GooglePlacesCollector,
            description="Google Places API collector with 18 rotating keys",
            config_schema={
                "api_keys": {"type": "array", "required": True},
                "rate_limit_per_key": {"type": "integer", "default": 100},
                "timeout": {"type": "integer", "default": 30}
            },
            default_config={"rate_limit_per_key": 100, "timeout": 30}
        )
        
        # Register OSM
        plugin_registry.register_collector(
            name="osm",
            collector_class=OSMCollector,
            description="OpenStreetMap Overpass API collector",
            config_schema={
                "overpass_url": {"type": "string", "default": "https://overpass-api.de/api/interpreter"},
                "timeout": {"type": "integer", "default": 60}
            },
            default_config={"timeout": 60}
        )
        
        logger.info(f"✅ Registered {len(plugin_registry.list_collectors())} collectors")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize plugins: {e}")
        raise


__all__ = ['PluginRegistry', 'plugin_registry', 'initialize_plugins']
