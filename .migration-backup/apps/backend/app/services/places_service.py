"""
Fix #3: PlacesService — dùng injected mongo_client thay vì tạo mới mỗi request.
Loại bỏ hoàn toàn AsyncIOMotorClient() trong constructor.
"""
from pathlib import Path
from typing import Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import json
import logging

from app.api.schemas.places import PlaceFilter
from app.core.config import settings

logger = logging.getLogger(__name__)


class PlacesService:
    def __init__(
        self,
        db: AsyncSession,
        redis_client: redis.Redis,
        mongo_client: AsyncIOMotorClient,
    ):
        self.db = db
        self.redis_client = redis_client
        # Dùng shared client, KHÔNG tạo mới
        self.collection = mongo_client[settings.mongodb_database]["places_gold"]
        self.local_data_path = (
            Path(__file__).resolve().parents[4] / "storage" / "data" / "pois.json"
        )

    def _serialize_place(self, doc: dict[str, Any]) -> dict[str, Any]:
        serialized = dict(doc)
        if "_id" in serialized:
            serialized["_id"] = str(serialized["_id"])
        else:
            serialized["_id"] = str(
                serialized.get("u_key")
                or serialized.get("place_id")
                or serialized.get("id")
                or serialized.get("name", "")
            )
        return serialized

    async def _get_places_from_json(self, filter_params: PlaceFilter) -> List[dict]:
        if not self.local_data_path.exists():
            return []

        try:
            with self.local_data_path.open("r", encoding="utf-8") as file:
                places = json.load(file)
        except Exception as exc:
            logger.warning("Local places fallback failed: %s", exc)
            return []

        if filter_params.city:
            city = filter_params.city.lower()
            places = [p for p in places if str(p.get("city", "")).lower() == city]
        if filter_params.category:
            category = filter_params.category.lower()
            places = [
                p
                for p in places
                if category == str(p.get("type", "")).lower()
                or category in [str(c).lower() for c in p.get("categories", [])]
            ]

        start = filter_params.offset
        end = start + filter_params.limit
        return [self._serialize_place(place) for place in places[start:end]]

    async def get_places(self, filter_params: PlaceFilter) -> List[dict]:
        query = {}
        if filter_params.city:
            query["city"] = filter_params.city
        if filter_params.category:
            query["$or"] = [
                {"categories": {"$in": [filter_params.category]}},
                {"type": filter_params.category},
            ]

        try:
            cursor = (
                self.collection.find(query)
                .skip(filter_params.offset)
                .limit(filter_params.limit)
            )

            places = []
            async for doc in cursor:
                places.append(self._serialize_place(doc))

            return places
        except Exception as exc:
            logger.warning("MongoDB places query failed, using local fallback: %s", exc)
            return await self._get_places_from_json(filter_params)

    async def get_place_by_id(self, place_id: str) -> Optional[dict]:
        from bson import ObjectId

        query = (
            {"_id": ObjectId(place_id)}
            if ObjectId.is_valid(place_id)
            else {"_id": place_id}
        )
        try:
            doc = await self.collection.find_one(query)
            if doc:
                return self._serialize_place(doc)
        except Exception as exc:
            logger.warning("MongoDB place lookup failed, using local fallback: %s", exc)

        places = await self._get_places_from_json(PlaceFilter(limit=1_000_000))
        return next(
            (
                place
                for place in places
                if place.get("_id") == place_id
                or place.get("u_key") == place_id
                or place.get("id") == place_id
            ),
            None,
        )

    async def get_stats(self) -> dict:
        try:
            total = await self.collection.count_documents({})
            city_stats = await self.collection.aggregate(
                [{"$group": {"_id": "$city", "count": {"$sum": 1}}}]
            ).to_list(None)
            type_stats = await self.collection.aggregate(
                [{"$group": {"_id": "$type", "count": {"$sum": 1}}}]
            ).to_list(None)
            rating_stats = await self.collection.aggregate(
                [{"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}]
            ).to_list(1)
            avg_rating = rating_stats[0].get("avg_rating") if rating_stats else 0
            return {
                "total_places": total,
                "avg_rating": round(avg_rating or 0, 2),
                "by_city": {s["_id"]: s["count"] for s in city_stats if s.get("_id")},
                "by_type": {s["_id"]: s["count"] for s in type_stats if s.get("_id")},
            }
        except Exception as exc:
            logger.warning("MongoDB stats query failed, using local fallback: %s", exc)

        places = await self._get_places_from_json(PlaceFilter(limit=1_000_000))
        by_city: dict[str, int] = {}
        by_type: dict[str, int] = {}
        rating_total = 0.0
        rating_count = 0
        for place in places:
            city = place.get("city") or "unknown"
            place_type = place.get("type") or "unknown"
            by_city[city] = by_city.get(city, 0) + 1
            by_type[place_type] = by_type.get(place_type, 0) + 1
            if place.get("rating") is not None:
                rating_total += float(place.get("rating") or 0)
                rating_count += 1
        return {
            "total_places": len(places),
            "avg_rating": round(rating_total / rating_count, 2) if rating_count else 0,
            "by_city": by_city,
            "by_type": by_type,
        }

    async def get_top_rated(self, limit: int = 10) -> List[dict]:
        try:
            cursor = (
                self.collection.find({"rating": {"$ne": None}})
                .sort("rating", -1)
                .limit(limit)
            )
            return [self._serialize_place(doc) async for doc in cursor]
        except Exception as exc:
            logger.warning("MongoDB top-rated query failed, using local fallback: %s", exc)

        places = await self._get_places_from_json(PlaceFilter(limit=1_000_000))
        return sorted(
            places,
            key=lambda place: float(place.get("rating") or 0),
            reverse=True,
        )[:limit]
