"""
Pipeline API - MongoDB Only
============================
API endpoints cho Bronze → Silver → Gold pipeline, lưu trữ hoàn toàn trên MongoDB.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.api.dependencies.database import get_database
from src.api.dependencies.auth import get_current_active_user, User
from src.core.logging import get_logger
from src.services.bronze_pipeline import BronzePipeline
from src.services.silver_gold_pipeline import SilverGoldPipeline

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])

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


@router.post("/bronze/collect", summary="Collect Bronze data to MongoDB")
async def collect_bronze(
    background_tasks: BackgroundTasks,
    city: str = Query(..., description="City name"),
    category: str = Query(..., description="Category to collect"),
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(default=2000, description="Search radius in meters"),
):
    """Thu thập POIs và lưu raw data vào MongoDB (Bronze layer - collection bronze_pois)"""
    try:
        pipeline = BronzePipeline()
        result = await pipeline.collect_city_category(
            city=city, city_code=city, lat=lat, lng=lng, category=category, radius=radius
        )
        return {
            "status": "success",
            "saved": result.get("saved", 0),
            "skipped": result.get("skipped", 0),
            "errors": len(result.get("errors", [])),
            "city": city,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Bronze collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bronze/mass-collect", summary="Mass collection to MongoDB")
async def mass_collect_bronze(
    background_tasks: BackgroundTasks,
    cities: List[str] = Query(default=["hanoi", "hcm"], description="Cities to collect"),
    categories: List[str] = Query(default=["restaurant", "cafe"], description="Categories"),
    grid_points: int = Query(default=4, description="Grid points per city (1-25)"),
):
    """Mass collection cho nhiều cities và categories, lưu vào MongoDB Bronze layer"""
    try:
        city_list = [{"name": c, **CITIES_TIER1[c]} for c in cities if c in CITIES_TIER1]
        if not city_list:
            raise HTTPException(status_code=400, detail="No valid cities provided")

        pipeline = BronzePipeline()
        result = await pipeline.run_mass_collection(
            cities=city_list, categories=categories
        )
        return {
            "status": "success",
            "total_saved": result.get("total_bronze_saved", 0),
            "cities_processed": result.get("cities_processed", 0),
            "categories": categories,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mass collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bronze/stats", summary="Bronze layer statistics")
async def bronze_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Thống kê Bronze layer trong MongoDB"""
    try:
        total = await db["bronze_pois"].count_documents({})
        osm_count = await db["bronze_pois"].count_documents({"osm_raw": {"$exists": True}})
        google_count = await db["bronze_pois"].count_documents({"google_raw": {"$exists": True}})
        enriched = await db["bronze_pois"].count_documents({"google_enriched": True})
        return {
            "layer": "bronze",
            "storage": "mongodb",
            "collection": "bronze_pois",
            "total_documents": total,
            "osm_raw_count": osm_count,
            "google_raw_count": google_count,
            "enriched_count": enriched,
            "timestamp": datetime.now().isoformat()
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
    """Transform Bronze records từ MongoDB bronze_pois → silver_pois"""
    try:
        pipeline = SilverGoldPipeline()
        result = await pipeline.bronze_to_silver(
            city=city, category=category, batch_size=batch_size
        )
        return {
            "status": "success",
            "transformed": result.get("transformed", 0),
            "errors": len(result.get("errors", [])),
            "total_bronze": result.get("total_bronze", 0),
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
    """Transform Silver → Gold (Master Data) trong MongoDB"""
    try:
        pipeline = SilverGoldPipeline()
        result = await pipeline.silver_to_gold(
            city=city, min_rating=min_rating, batch_size=batch_size
        )
        return {
            "status": "success",
            "enriched": result.get("enriched", 0),
            "errors": len(result.get("errors", [])),
            "total_silver": result.get("total_silver", 0),
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
    """Chạy full pipeline: Bronze → Silver → Gold (tất cả lưu trên MongoDB)"""
    try:
        city_list = [{"name": c, **CITIES_TIER1.get(c, {})} for c in cities if c in CITIES_TIER1]
        bronze_pipeline = BronzePipeline()
        silver_gold_pipeline = SilverGoldPipeline()

        bronze_result = await bronze_pipeline.run_mass_collection(
            cities=city_list, categories=categories
        )
        silver_result = await silver_gold_pipeline.bronze_to_silver(
            batch_size=bronze_result.get("total_bronze_saved", 100)
        )
        gold_result = await silver_gold_pipeline.silver_to_gold()

        return {
            "status": "complete",
            "pipeline": {
                "bronze": {"saved": bronze_result.get("total_bronze_saved", 0), "cities": cities},
                "silver": {"transformed": silver_result.get("transformed", 0)},
                "gold": {"enriched": gold_result.get("enriched", 0)}
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/stats", summary="All layers statistics")
async def layers_stats(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Thống kê cả 3 layers trong MongoDB"""
    try:
        bronze_total = await db["bronze_pois"].count_documents({})
        silver_total = await db["silver_pois"].count_documents({})
        gold_total = await db["gold_master_pois"].count_documents({})

        return {
            "layers": {
                "bronze": {
                    "storage": "mongodb",
                    "collection": "bronze_pois",
                    "total_documents": bronze_total,
                },
                "silver": {
                    "storage": "mongodb",
                    "collection": "silver_pois",
                    "total_documents": silver_total,
                },
                "gold": {
                    "storage": "mongodb",
                    "collection": "gold_master_pois",
                    "total_documents": gold_total,
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
