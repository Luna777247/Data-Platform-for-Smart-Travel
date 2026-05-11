"""
Pipeline API với MinIO + MongoDB
================================
API endpoints cho Bronze (MinIO) → Silver/Gold (MongoDB) pipeline
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.api.dependencies.database import get_database
from src.core.logging import get_logger
from src.core.minio_client import get_bronze_storage
from src.services.bronze_pipeline import BronzePipeline
from src.services.silver_gold_pipeline import SilverGoldPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline MinIO"])

# Default city configs
CITIES_TIER1 = {
    "hanoi": {"lat": 21.0278, "lng": 105.8342},
    "hcm": {"lat": 10.8231, "lng": 106.6297},
    "danang": {"lat": 16.0544, "lng": 108.2022},
    "haiphong": {"lat": 20.8449, "lng": 106.6881},
    "cantho": {"lat": 10.0452, "lng": 105.7469},
    "nhatrang": {"lat": 12.2388, "lng": 109.1967},
    "dalat": {"lat": 11.9404, "lng": 108.4583},
    "hue": {"lat": 16.4637, "lng": 107.5909},
}

CATEGORIES = [
    "restaurant", "cafe", "bar", "hotel", "tourist_attraction",
    "shopping_mall", "supermarket", "spa", "gym", "museum"
]


@router.post("/bronze/collect", summary="Collect Bronze data to MinIO")
async def collect_bronze(
    background_tasks: BackgroundTasks,
    city: str = Query(..., description="City name"),
    category: str = Query(..., description="Category to collect"),
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(default=2000, description="Search radius in meters"),
):
    """
    Thu thập POIs và lưu raw data vào MinIO (Bronze layer)
    
    - Lưu JSON gốc từ Google Places API
    - Path: bronze/google/{city}/{category}/{timestamp}_{hash}.json
    """
    try:
        pipeline = BronzePipeline()
        
        result = await pipeline.collect_city_category(
            city=city,
            lat=lat,
            lng=lng,
            category=category,
            radius=radius
        )
        
        return {
            "status": "success",
            "saved_to_minio": result["saved"],
            "paths": result["paths"],
            "errors": len(result["errors"]),
            "city": city,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bronze collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bronze/mass-collect", summary="Mass collection to MinIO")
async def mass_collect_bronze(
    background_tasks: BackgroundTasks,
    cities: List[str] = Query(default=["hanoi", "hcm"], description="Cities to collect"),
    categories: List[str] = Query(default=["restaurant", "cafe"], description="Categories"),
    grid_points: int = Query(default=4, description="Grid points per city (1-25)"),
):
    """
    Mass collection cho nhiều cities và categories
    Lưu tất cả vào MinIO Bronze layer
    """
    try:
        # Validate cities
        city_list = []
        for c in cities:
            if c in CITIES_TIER1:
                city_list.append({
                    "name": c,
                    **CITIES_TIER1[c]
                })
        
        if not city_list:
            raise HTTPException(status_code=400, detail="No valid cities provided")
        
        pipeline = BronzePipeline()
        
        # Run in background for long operation
        result = await pipeline.run_mass_collection(
            cities=city_list,
            categories=categories,
            grid_points=grid_points
        )
        
        return {
            "status": "success",
            "total_saved": result["total_bronze_saved"],
            "cities_processed": result["cities_processed"],
            "categories": categories,
            "by_city": {k: v["total_saved"] for k, v in result["by_city"].items()},
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mass collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bronze/list", summary="List Bronze records in MinIO")
async def list_bronze(
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Liệt kê Bronze records trong MinIO"""
    try:
        storage = get_bronze_storage()
        records = storage.list_bronze_records(
            city=city,
            source="google",
            category=category
        )
        
        return {
            "total": len(records),
            "records": records[:limit],
            "filters": {"city": city, "category": category}
        }
        
    except Exception as e:
        logger.error(f"Failed to list bronze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bronze/stats", summary="Bronze layer statistics")
async def bronze_stats():
    """Thống kê Bronze layer trong MinIO"""
    try:
        pipeline = BronzePipeline()
        stats = await pipeline.get_bronze_stats()
        
        return {
            "layer": "bronze",
            "storage": "minio",
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get bronze stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bronze-to-silver", summary="Transform Bronze → Silver")
async def bronze_to_silver(
    city: Optional[str] = Query(None, description="City to process (all if None)"),
    category: Optional[str] = Query(None, description="Category to process"),
    batch_size: int = Query(default=100, ge=1, le=500),
):
    """
    Transform Bronze records từ MinIO → Silver trong MongoDB
    
    - Clean và normalize dữ liệu
    - Standardize location format
    - Unified categories
    """
    try:
        pipeline = SilverGoldPipeline()
        
        result = await pipeline.bronze_to_silver(
            city=city,
            category=category,
            batch_size=batch_size
        )
        
        return {
            "status": "success",
            "transformed": result["transformed"],
            "errors": len(result["errors"]),
            "total_bronze": result["total_bronze"],
            "from_layer": "bronze",
            "to_layer": "silver",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Transform failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/silver-to-gold", summary="Transform Silver → Gold")
async def silver_to_gold(
    city: Optional[str] = Query(None, description="City to process"),
    min_rating: float = Query(default=3.5, ge=0, le=5),
    batch_size: int = Query(default=100, ge=1, le=500),
):
    """
    Transform Silver → Gold (Master Data)
    
    - Enrich với quality scoring
    - Deduplicate
    - Production-ready
    """
    try:
        pipeline = SilverGoldPipeline()
        
        result = await pipeline.silver_to_gold(
            city=city,
            min_rating=min_rating,
            batch_size=batch_size
        )
        
        return {
            "status": "success",
            "enriched": result["enriched"],
            "errors": len(result["errors"]),
            "total_silver": result["total_silver"],
            "from_layer": "silver",
            "to_layer": "gold",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-full-pipeline", summary="Run complete pipeline")
async def run_full_pipeline(
    background_tasks: BackgroundTasks,
    cities: List[str] = Query(default=["hanoi"], description="Cities to process"),
    categories: List[str] = Query(default=["restaurant"], description="Categories"),
    grid_points: int = Query(default=4, ge=1, le=25),
):
    """
    Chạy full pipeline: Bronze → Silver → Gold
    
    1. Collect raw data to MinIO (Bronze)
    2. Transform to Silver (MongoDB)
    3. Enrich to Gold (MongoDB)
    """
    try:
        pipeline = SilverGoldPipeline()
        bronze_pipeline = BronzePipeline()
        
        # Step 1: Bronze collection
        city_list = [{"name": c, **CITIES_TIER1.get(c, {})} for c in cities if c in CITIES_TIER1]
        
        bronze_result = await bronze_pipeline.run_mass_collection(
            cities=city_list,
            categories=categories,
            grid_points=grid_points
        )
        
        # Step 2: Bronze → Silver
        silver_result = await pipeline.bronze_to_silver(
            batch_size=bronze_result["total_bronze_saved"]
        )
        
        # Step 3: Silver → Gold
        gold_result = await pipeline.silver_to_gold()
        
        return {
            "status": "complete",
            "pipeline": {
                "bronze": {
                    "saved_to_minio": bronze_result["total_bronze_saved"],
                    "cities": cities
                },
                "silver": {
                    "transformed": silver_result["transformed"]
                },
                "gold": {
                    "enriched": gold_result["enriched"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/stats", summary="All layers statistics")
async def layers_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Thống kê cả 3 layers"""
    try:
        bronze_storage = get_bronze_storage()
        pipeline = SilverGoldPipeline()
        
        # Get stats
        bronze_stats = bronze_storage.get_stats()
        silver_count = await db["silver_pois"].count_documents({})
        gold_count = await db["gold_master_pois"].count_documents({})
        
        return {
            "layers": {
                "bronze": {
                    "storage": "minio",
                    "total_objects": bronze_stats.get("total_objects", 0),
                    "total_size_mb": round(bronze_stats.get("total_size", 0) / (1024*1024), 2),
                    "by_source": bronze_stats.get("by_source", {}),
                    "by_city": bronze_stats.get("by_city", {})
                },
                "silver": {
                    "storage": "mongodb",
                    "total_documents": silver_count,
                    "collection": "silver_pois"
                },
                "gold": {
                    "storage": "mongodb", 
                    "total_documents": gold_count,
                    "collection": "gold_master_pois"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
