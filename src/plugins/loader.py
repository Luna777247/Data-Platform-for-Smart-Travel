"""
Plugin Loader
=============
Dynamic loading và instantiation của plugins.

Support:
- Load from Python modules
- Load from configuration (MongoDB)
- Hot-reloading
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Type
from src.core.logging import get_logger
from src.core.database import mongodb_manager

logger = get_logger(__name__)


class PluginLoader:
    """
    Dynamic plugin loader.
    
    Load plugin classes from:
    1. Existing modules (e.g., src.collectors.xxx)
    2. Custom plugin files
    3. MongoDB configuration
    """
    
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = plugins_dir or "src/plugins/custom"
    
    def load_from_module(
        self, 
        module_path: str, 
        class_name: str
    ) -> Optional[Type]:
        """
        Load a class from Python module.
        
        Args:
            module_path: Dot-separated path (e.g., "src.collectors.google_places_collector")
            class_name: Class name trong module
            
        Returns:
            Class object hoặc None
            
        Example:
            cls = loader.load_from_module(
                "src.collectors.google_places_collector",
                "GooglePlacesCollector"
            )
        """
        try:
            module = importlib.import_module(module_path)
            class_obj = getattr(module, class_name)
            logger.debug(f"✅ Loaded class {class_name} from {module_path}")
            return class_obj
            
        except ImportError as e:
            logger.error(f"❌ Failed to import module {module_path}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"❌ Class {class_name} not found in {module_path}: {e}")
            return None
    
    def load_from_file(
        self, 
        file_path: str, 
        class_name: str
    ) -> Optional[Type]:
        """
        Load a class from Python file.
        
        Args:
            file_path: Path to .py file
            class_name: Class name trong file
            
        Returns:
            Class object hoặc None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"❌ Plugin file not found: {file_path}")
                return None
            
            # Load module from file
            spec = importlib.util.spec_from_file_location(
                path.stem, 
                path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            class_obj = getattr(module, class_name)
            logger.info(f"✅ Loaded plugin from file: {file_path}#{class_name}")
            return class_obj
            
        except Exception as e:
            logger.error(f"❌ Failed to load from file {file_path}: {e}")
            return None
    
    async def load_from_database(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Load plugin configuration từ MongoDB.
        
        Args:
            plugin_id: Plugin identifier trong database
            
        Returns:
            Plugin config dict hoặc None
        """
        try:
            db = mongodb_manager.get_database()
            plugin_doc = await db.plugin_registry.find_one({"plugin_id": plugin_id})
            
            if not plugin_doc:
                logger.warning(f"⚠️ Plugin {plugin_id} not found in database")
                return None
            
            # Load class from specified path
            class_path = plugin_doc.get("class_path")
            if class_path:
                parts = class_path.rsplit(".", 1)
                if len(parts) == 2:
                    module_path, class_name = parts
                    plugin_class = self.load_from_module(module_path, class_name)
                    
                    if plugin_class:
                        return {
                            "plugin_id": plugin_doc["plugin_id"],
                            "plugin_type": plugin_doc.get("plugin_type", "source"),
                            "name": plugin_doc.get("name"),
                            "class": plugin_class,
                            "config_schema": plugin_doc.get("config_schema", {}),
                            "default_config": plugin_doc.get("default_config", {}),
                            "version": plugin_doc.get("version", "1.0.0")
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {plugin_id} from database: {e}")
            return None
    
    async def load_all_from_database(self) -> list:
        """
        Load all enabled plugins từ database.
        
        Returns:
            List of plugin configs
        """
        plugins = []
        
        try:
            db = mongodb_manager.get_database()
            cursor = db.plugin_registry.find({"enabled": True})
            
            async for doc in cursor:
                try:
                    plugin_info = await self.load_from_database(doc["plugin_id"])
                    if plugin_info:
                        plugins.append(plugin_info)
                except Exception as e:
                    logger.error(f"❌ Failed to load plugin {doc.get('plugin_id')}: {e}")
                    continue
            
            logger.info(f"✅ Loaded {len(plugins)} plugins from database")
            return plugins
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugins from database: {e}")
            return []


__all__ = ['PluginLoader']
