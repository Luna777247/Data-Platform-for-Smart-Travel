"""
Plugin Management API Routes
==============================
API endpoints cho plugin system.

Provides:
- Plugin registration/management
- Source configuration
- Dynamic pipeline creation
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_mongo_client, get_database
from src.plugins import plugin_registry, BaseCollector
from src.plugins.loader import PluginLoader
from src.core.logging import get_logger

logger = get_logger(__name__)

async def ensure_plugin_loaded(plugin_id: str, mongo_client=None):
    """Đảm bảo plugin được nạp vào registry (kiểm tra memory, fallback sang DB)"""
    if plugin_registry.is_registered(plugin_id):
        return True
    
    # Fallback 1: Try PluginLoader.load_from_database
    try:
        loader = PluginLoader()
        info = await loader.load_from_database(plugin_id)
        if info:
            if info["plugin_type"] == "source":
                plugin_registry.register_collector(
                    name=plugin_id,
                    collector_class=info["class"],
                    config_schema=info.get("config_schema", {}),
                    default_config=info.get("default_config", {}),
                    description=info.get("name", ""),
                    version=info.get("version", "1.0.0")
                )
                return True
    except Exception as e:
        logger.warning(f"PluginLoader.load_from_database failed for {plugin_id}: {e}")
    
    # Fallback 2: Try direct class load from DB class_path record
    if mongo_client:
        try:
            db = mongo_client.smart_travel
            plugin_doc = await db.plugin_registry.find_one({"plugin_id": plugin_id})
            if plugin_doc and plugin_doc.get("class_path"):
                loader = PluginLoader()
                parts = plugin_doc["class_path"].rsplit(".", 1)
                if len(parts) == 2:
                    plugin_class = loader.load_from_module(parts[0], parts[1])
                    if plugin_class:
                        plugin_registry.register_collector(
                            name=plugin_id,
                            collector_class=plugin_class,
                            config_schema=plugin_doc.get("config_schema", {}),
                            default_config=plugin_doc.get("default_config", {}),
                            description=plugin_doc.get("description", ""),
                            version=plugin_doc.get("version", "1.0.0")
                        )
                        logger.info(f"✅ Loaded plugin '{plugin_id}' via direct class import")
                        return True
        except Exception as e:
            logger.error(f"Direct class load failed for {plugin_id}: {e}")
    
    return False

router = APIRouter(
    prefix="/api/v1/plugins",
    tags=["Plugin Management"]
)


# ============================================
# Pydantic Models
# ============================================

class PluginRegistrationRequest(BaseModel):
    """Request model cho plugin registration"""
    plugin_id: str = Field(..., description="Unique plugin identifier")
    plugin_type: str = Field(..., description="'source' | 'transformer' | 'enricher'")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Plugin description")
    version: str = Field(default="1.0.0", description="Semantic version")
    class_path: str = Field(..., description="Module path (e.g., 'src.collectors.xxx.MyCollector')")
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="Config JSON schema")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="Default config values")
    enabled: bool = Field(default=True)


class SourceConfigRequest(BaseModel):
    """Request model cho source configuration"""
    source_id: str = Field(..., description="Unique source instance ID")
    plugin_id: str = Field(..., description="Plugin to use")
    name: str = Field(..., description="Display name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Source-specific config")
    enabled: bool = Field(default=True)


class PluginResponse(BaseModel):
    """Response model cho plugin info"""
    plugin_id: str
    plugin_type: str
    name: str
    description: str
    version: str
    enabled: bool
    registered_at: Optional[str] = None


class SourceResponse(BaseModel):
    """Response model cho source info"""
    source_id: str
    plugin_id: str
    name: str
    config: Dict[str, Any]
    enabled: bool


# ============================================
# Plugin Management Endpoints
# ============================================

@router.get("/", response_model=List[PluginResponse])
async def list_plugins(
    plugin_type: Optional[str] = Query(None, description="Filter by type: source/transformer"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    List all registered plugins.
    
    Returns plugins từ cả in-memory registry và database.
    """
    try:
        # Get from registry
        plugins = plugin_registry.list_all()
        
        # Filter by type
        if plugin_type:
            plugins = [p for p in plugins if p.get("type") == plugin_type]
        
        return [
            PluginResponse(
                plugin_id=p["name"],
                plugin_type=p["type"],
                name=p["name"],
                description=p.get("description", ""),
                version=p.get("version", "1.0.0"),
                enabled=True,
                registered_at=p.get("registered_at")
            )
            for p in plugins
        ]
        
    except Exception as e:
        logger.error(f"❌ Error listing plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_id}", response_model=Dict[str, Any])
async def get_plugin(
    plugin_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Get detailed information về một plugin.
    """
    try:
        # Ensure plugin is loaded (with DB fallback)
        await ensure_plugin_loaded(plugin_id, mongo_client)
        
        info = plugin_registry.get_plugin_info(plugin_id)
        
        if not info:
            # Final fallback: check DB directly for metadata
            db = mongo_client.smart_travel
            plugin_doc = await db.plugin_registry.find_one({"plugin_id": plugin_id})
            if plugin_doc:
                return {
                    "plugin_id": plugin_id,
                    "plugin_type": plugin_doc.get("plugin_type"),
                    "name": plugin_doc.get("name"),
                    "description": plugin_doc.get("description"),
                    "version": plugin_doc.get("version"),
                    "config_schema": plugin_doc.get("config_schema"),
                    "default_config": plugin_doc.get("default_config"),
                    "registered_at": plugin_doc.get("created_at")
                }
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
        
        return {
            "plugin_id": plugin_id,
            "plugin_type": info.get("type"),
            "name": info.get("name"),
            "description": info.get("description"),
            "version": info.get("version"),
            "config_schema": info.get("config_schema"),
            "default_config": info.get("default_config"),
            "registered_at": info.get("registered_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PluginResponse)
async def register_plugin(
    request: PluginRegistrationRequest,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Register a new plugin.
    
    Lưu vào database và load vào registry.
    """
    try:
        # Load class
        loader = PluginLoader()
        parts = request.class_path.rsplit(".", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid class_path format")
        
        module_path, class_name = parts
        plugin_class = loader.load_from_module(module_path, class_name)
        
        if not plugin_class:
            raise HTTPException(
                status_code=400, 
                detail=f"Could not load class from {request.class_path}"
            )
        
        # Save to database
        db = mongo_client.smart_travel
        plugin_doc = {
            "plugin_id": request.plugin_id,
            "plugin_type": request.plugin_type,
            "name": request.name,
            "description": request.description,
            "version": request.version,
            "class_path": request.class_path,
            "config_schema": request.config_schema,
            "default_config": request.default_config,
            "enabled": request.enabled,
            "created_at": datetime.now().isoformat(),
            "created_by": current_user
        }
        
        await db.plugin_registry.update_one(
            {"plugin_id": request.plugin_id},
            {"$set": plugin_doc},
            upsert=True
        )
        
        # Register in memory
        if request.plugin_type == "source":
            plugin_registry.register_collector(
                name=request.plugin_id,
                collector_class=plugin_class,
                config_schema=request.config_schema,
                default_config=request.default_config,
                description=request.description,
                version=request.version
            )
        
        logger.info(f"✅ Registered plugin: {request.plugin_id} by {current_user}")
        
        return PluginResponse(
            plugin_id=request.plugin_id,
            plugin_type=request.plugin_type,
            name=request.name,
            description=request.description,
            version=request.version,
            enabled=request.enabled,
            registered_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registering plugin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plugin_id}")
async def unregister_plugin(
    plugin_id: str,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Unregister/disable a plugin.
    """
    try:
        # Update database
        db = mongo_client.smart_travel
        await db.plugin_registry.update_one(
            {"plugin_id": plugin_id},
            {"$set": {"enabled": False, "disabled_at": datetime.now().isoformat()}}
        )
        
        # Remove from registry
        plugin_registry.unregister(plugin_id)
        
        logger.info(f"🗑️ Unregistered plugin: {plugin_id}")
        
        return {"message": f"Plugin '{plugin_id}' unregistered successfully"}
        
    except Exception as e:
        logger.error(f"❌ Error unregistering plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Source Management Endpoints
# ============================================

@router.get("/sources/", response_model=List[SourceResponse])
async def list_sources(
    plugin_id: Optional[str] = Query(None, description="Filter by plugin ID"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    List configured source instances.
    """
    try:
        db = mongo_client.smart_travel
        
        query = {}
        if plugin_id:
            query["plugin_id"] = plugin_id
        
        cursor = db.source_configs.find(query)
        sources = await cursor.to_list(length=None)
        
        return [
            SourceResponse(
                source_id=s["source_id"],
                plugin_id=s["plugin_id"],
                name=s.get("name", s["source_id"]),
                config=s.get("config", {}),
                enabled=s.get("enabled", True)
            )
            for s in sources
        ]
        
    except Exception as e:
        logger.error(f"❌ Error listing sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/", response_model=SourceResponse)
async def create_source(
    request: SourceConfigRequest,
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Create a new source instance.
    
    Configure một plugin cụ thể cho một city/use case.
    """
    try:
        # Verify plugin exists (ensuring it's loaded in memory, with DB fallback)
        if not await ensure_plugin_loaded(request.plugin_id, mongo_client):
            # Final check: plugin metadata may exist in DB even if class can't load
            db = mongo_client.smart_travel
            plugin_doc = await db.plugin_registry.find_one({"plugin_id": request.plugin_id})
            if not plugin_doc:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Plugin '{request.plugin_id}' not registered"
                )
        
        # Save to database
        db = mongo_client.smart_travel
        source_doc = {
            "source_id": request.source_id,
            "plugin_id": request.plugin_id,
            "name": request.name,
            "config": request.config,
            "enabled": request.enabled,
            "created_at": datetime.now().isoformat(),
            "created_by": current_user
        }
        
        await db.source_configs.update_one(
            {"source_id": request.source_id},
            {"$set": source_doc},
            upsert=True
        )
        
        logger.info(f"✅ Created source: {request.source_id} (plugin: {request.plugin_id})")
        
        return SourceResponse(
            source_id=request.source_id,
            plugin_id=request.plugin_id,
            name=request.name,
            config=request.config,
            enabled=request.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/collect")
async def collect_from_source(
    source_id: str,
    city: str = Query(..., description="City to collect"),
    category: str = Query(..., description="Category to collect"),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Trigger data collection từ một source.
    """
    try:
        # Get source config
        db = mongo_client.smart_travel
        source = await db.source_configs.find_one({"source_id": source_id})
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
        
        if not source.get("enabled", True):
            raise HTTPException(status_code=400, detail=f"Source '{source_id}' is disabled")
        
        # Get plugin and create instance
        plugin_id = source["plugin_id"]
        config = source.get("config", {})
        
        # Ensure plugin is loaded in memory registry
        await ensure_plugin_loaded(plugin_id)
        
        collector = plugin_registry.get_collector(plugin_id, config)
        
        # Fallback: nếu registry không instantiate được, 
        # load trực tiếp từ class_path trong DB
        if not collector:
            logger.warning(f"⚠️ Registry failed for '{plugin_id}', trying direct load from DB...")
            plugin_doc = await db.plugin_registry.find_one({"plugin_id": plugin_id})
            if plugin_doc and plugin_doc.get("class_path"):
                try:
                    loader = PluginLoader()
                    parts = plugin_doc["class_path"].rsplit(".", 1)
                    if len(parts) == 2:
                        plugin_class = loader.load_from_module(parts[0], parts[1])
                        if plugin_class:
                            try:
                                collector = plugin_class(config=config)
                            except TypeError:
                                collector = plugin_class()
                except Exception as e:
                    logger.error(f"Direct load fallback failed: {e}")
        
        if not collector:
            raise HTTPException(
                status_code=500, 
                detail=f"Could not instantiate collector for plugin '{plugin_id}'"
            )
        
        # Collect data
        logger.info(f"🚀 Collecting from source {source_id}: {city}/{category}")
        data = await collector.collect(city=city, category=category)
        
        return {
            "source_id": source_id,
            "plugin_id": plugin_id,
            "city": city,
            "category": category,
            "records_collected": len(data),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error collecting from source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Plugin Testing
# ============================================

@router.post("/{plugin_id}/test")
async def test_plugin(
    plugin_id: str,
    config: Optional[Dict[str, Any]] = Body(default=None),
    current_user: str = Depends(get_current_active_user),
    mongo_client = Depends(get_mongo_client)
):
    """
    Test plugin connection/configuration.
    """
    try:
        # Ensure loaded and Try to instantiate
        await ensure_plugin_loaded(plugin_id, mongo_client)
        info = plugin_registry.get_plugin_info(plugin_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found")
            
        test_config = config or info.get("default_config", {})
        instance = plugin_registry.get_collector(plugin_id, test_config)
        
        if not instance:
            return {
                "plugin_id": plugin_id,
                "status": "error",
                "message": "Could not create plugin instance"
            }
        
        # Try health check
        try:
            health = await instance.health_check()
            return {
                "plugin_id": plugin_id,
                "status": "success",
                "health": health,
                "message": "Plugin test successful"
            }
        except Exception as e:
            return {
                "plugin_id": plugin_id,
                "status": "warning",
                "message": f"Instance created but health check failed: {str(e)}"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing plugin {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
