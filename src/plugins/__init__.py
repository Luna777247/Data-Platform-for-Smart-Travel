"""
Plugin System for Smart Tourism Data Platform
===============================================

Dynamic plugin architecture cho data collectors và transformers.

Usage:
    from src.plugins import plugin_registry, BaseCollector
    
    # Register plugin
    plugin_registry.register_collector(
        name="tripadvisor",
        collector_class=TripAdvisorCollector
    )
    
    # Load and use
    collector = plugin_registry.get_collector("tripadvisor")
    data = await collector.collect(city="hanoi", category="restaurant")

Components:
- BaseCollector: Interface cho data collectors
- BaseTransformer: Interface cho data transformers  
- PluginRegistry: Quản lý plugin registration và loading
- PluginLoader: Dynamic import và instantiation
"""

from .base import BaseCollector, BaseTransformer
from .registry import PluginRegistry, plugin_registry
from .loader import PluginLoader

__all__ = [
    'BaseCollector',
    'BaseTransformer', 
    'PluginRegistry',
    'plugin_registry',
    'PluginLoader'
]
