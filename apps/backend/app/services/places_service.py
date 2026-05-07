"""
Fix #3: PlacesService — dùng injected mongo_client thay vì tạo mới mỗi request.
Loại bỏ hoàn toàn AsyncIOMotorClient() trong constructor.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import json
import logging

from app.api.schemas.places import PlaceFilter, PlaceResponse
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

    async def get_places(self, filter_params: PlaceFilter) -> List[dict]:
        query = {}
        if filter_params.city:
            query["city"] = filter_params.city
        if filter_params.category:
            query["categories"] = {"$in": [filter_params.category]}

        cursor = (
            self.collection.find(query)
            .skip(filter_params.offset)
            .limit(filter_params.limit)
        )

        places = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # serialize ObjectId
            places.append(doc)

        return places

    async def get_place_by_id(self, place_id: str) -> Optional[dict]:
        from bson import ObjectId

        # Try ObjectId first, fallback to string
        query = (
            {"_id": ObjectId(place_id)}
            if ObjectId.is_valid(place_id)
            else {"_id": place_id}
        )
        doc = await self.collection.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        return None