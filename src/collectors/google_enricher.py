import httpx
from typing import List, Dict, Any
from datetime import datetime
from src.shared.data_contracts import BronzePlace


class GoogleEnricher:
    def __init__(self, city: str, api_key: str):
        self.city = city
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.city_queries = {
            "hanoi": "tourist attractions in Hanoi Vietnam",
            "hcm": "tourist attractions in Ho Chi Minh City Vietnam",
            "danang": "tourist attractions in Da Nang Vietnam",
        }

    async def enrich(self) -> List[BronzePlace]:
        query = self.city_queries.get(self.city)
        if not query:
            raise ValueError(f"Unsupported city: {self.city}")

        params = {
            "query": query,
            "key": self.api_key,
            "language": "en",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

        places = []
        for result in data.get("results", []):
            place = BronzePlace(
                source_id=result["place_id"],
                raw_data=result,
                collected_at=datetime.utcnow(),
                city=self.city,
                source="google",
            )
            places.append(place)

        return places
