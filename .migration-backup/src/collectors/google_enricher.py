import httpx
from typing import List, Dict, Any
from datetime import datetime
from src.shared.data_contracts import BronzePlace


class GoogleEnricher:
    def __init__(self, city: str, api_key: str):
        self.city = city
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self._load_city_config()

    def _load_city_config(self):
        from src.shared.path_manager import ROOT_DIR
        import json
        import os
        
        config_path = os.path.join(ROOT_DIR, "storage", "configs", "cities.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.city_config = json.load(f)
        except Exception:
            self.city_config = {}

    async def enrich(self) -> List[BronzePlace]:
        city_data = self.city_config.get(self.city, {})
        city_name = city_data.get("name", self.city)
        country = city_data.get("country", "")
        
        query = f"tourist attractions in {city_name} {country}".strip()

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
