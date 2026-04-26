# backend/app/api/places.py
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.db.repository import PlaceRepository

router = APIRouter()
repo = PlaceRepository()

@router.get("/")
async def get_places(
    city: Optional[str] = None,
    type: Optional[str] = None,
    rating: Optional[float] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return await repo.get_all(city=city, place_type=type, rating_min=rating, limit=limit, offset=offset)

@router.get("/stats")
async def get_stats():
    return await repo.get_stats()

@router.get("/top-rated")
async def get_top_rated(limit: int = 10):
    return await repo.get_top_rated(limit=limit)

@router.get("/cities")
async def get_cities():
    stats = await repo.get_stats()
    return list(stats["by_city"].keys())

@router.get("/types")
async def get_types():
    stats = await repo.get_stats()
    return list(stats["by_type"].keys())

@router.get("/{id}")
async def get_place(id: str):
    place = await repo.get_by_id(id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
