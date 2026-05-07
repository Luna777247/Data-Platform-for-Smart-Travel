from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from src.shared.data_contracts import GoldPlace


class GoldProcessor:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.silver_collection = mongo_client.smart_travel.places_silver
        self.gold_collection = mongo_client.smart_travel.places_gold

    async def process(self, city: str) -> int:
        """Enrich silver data and insert into gold collection."""
        silver_places = await self.silver_collection.find({"city": city}).to_list(
            length=None
        )

        gold_places = []
        for place in silver_places:
            gold_place = await self._enrich_place_data(place)
            gold_places.append(gold_place.model_dump())

        if gold_places:
            await self.gold_collection.insert_many(gold_places)

        return len(gold_places)

    async def _enrich_place_data(self, place: dict) -> GoldPlace:
        quality_score = self._calculate_quality_score(place)
        business_metrics = await self._calculate_business_metrics(place)

        return GoldPlace(
            id=str(place["_id"]),
            source_id=place["source_id"],
            raw_data=place["raw_data"],
            collected_at=place["collected_at"],
            city=place["city"],
            source=place["source"],
            name=place["name"],
            address=place["address"],
            latitude=place["latitude"],
            longitude=place["longitude"],
            categories=place["categories"],
            rating=place.get("rating"),
            review_count=place.get("review_count"),
            deduplication_key=place["deduplication_key"],
            quality_score=quality_score,
            business_metrics=business_metrics,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def _calculate_quality_score(self, place: dict) -> float:
        score = 0.0
        if place.get("name"):
            score += 0.3
        if place.get("address"):
            score += 0.2
        if place.get("latitude") and place.get("longitude"):
            score += 0.2
        if place.get("categories"):
            score += 0.1
        if place.get("rating"):
            score += 0.2
        return min(score, 1.0)

    async def _calculate_business_metrics(self, place: dict) -> dict:
        return {
            "popularity_score": place.get("rating", 0)
            * (place.get("review_count", 0) / 100),
            "category_count": len(place.get("categories", [])),
            "data_completeness": self._calculate_quality_score(place),
        }
