"""
Fix #3 (tiếp): Route places inject mongo_client vào PlacesService.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import json
import logging

from app.api.dependencies.database import get_db, get_mongo_client, get_redis_client
from app.api.schemas.places import PlaceResponse, PlaceFilter
from app.services.places_service import PlacesService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/places")
async def get_places(
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    service = PlacesService(db, redis_client, mongo_client)
    filter_params = PlaceFilter(city=city, category=category, limit=limit, offset=offset)

    # Try cache first
    cache_key = f"places:{city}:{category}:{limit}:{offset}"
    try:
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
    except Exception:
        pass  # Redis down — skip cache

    # Get from database
    places = await service.get_places(filter_params)

    # Cache result for 5 minutes
    try:
        await redis_client.setex(cache_key, 300, json.dumps(places, default=str))
    except Exception:
        pass  # Redis down — skip cache

    return places


@router.get("/places/{place_id}")
async def get_place(
    place_id: str,
    db: AsyncSession = Depends(get_db),
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    service = PlacesService(db, redis_client, mongo_client)
    place = await service.get_place_by_id(place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place