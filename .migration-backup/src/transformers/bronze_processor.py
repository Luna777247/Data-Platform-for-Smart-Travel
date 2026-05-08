from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from src.shared.data_contracts import BronzePlace


class BronzeProcessor:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.collection = mongo_client.smart_travel.places_bronze

    async def process(self, places: List[BronzePlace]) -> int:
        """Insert raw data into bronze collection."""
        documents = [place.model_dump() for place in places]

        if documents:
            result = await self.collection.insert_many(documents)
            return len(result.inserted_ids)

        return 0

    async def get_raw_places(self, city: str, limit: int = 1000) -> List[dict]:
        cursor = self.collection.find({"city": city}).limit(limit)
        return await cursor.to_list(length=limit)
