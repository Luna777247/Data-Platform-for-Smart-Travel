from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from src.shared.data_contracts import SilverPlace
import re


class SilverTransformer:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.mongo_client = mongo_client
        self.bronze_collection = mongo_client.smart_travel.places_bronze
        self.silver_collection = mongo_client.smart_travel.places_silver

    async def process(self, city: str) -> int:
        """Clean bronze data and insert into silver collection."""
        raw_places = await self.bronze_collection.find({"city": city}).to_list(length=None)

        cleaned_places = []
        for raw in raw_places:
            cleaned = self._clean_place_data(raw)
            if cleaned:
                cleaned_places.append(cleaned)

        # Deduplication
        deduplicated = self._deduplicate_places(cleaned_places)

        # Insert into silver
        if deduplicated:
            await self.silver_collection.insert_many(deduplicated)

        return len(deduplicated)

    def _clean_place_data(self, raw_place: dict) -> Optional[SilverPlace]:
        try:
            if raw_place["source"] == "osm":
                return self._clean_osm_place(raw_place)
            elif raw_place["source"] == "google":
                return self._clean_google_place(raw_place)
        except (KeyError, TypeError):
            return None

    def _clean_osm_place(self, raw: dict) -> SilverPlace:
        tags = raw["raw_data"]["tags"]
        center = raw["raw_data"].get("center", {})

        return SilverPlace(
            source_id=raw["source_id"],
            raw_data=raw["raw_data"],
            collected_at=raw["collected_at"],
            city=raw["city"],
            source=raw["source"],
            name=tags.get("name", "").strip(),
            address=self._build_osm_address(tags),
            latitude=center.get("lat", 0.0),
            longitude=center.get("lon", 0.0),
            categories=self._extract_osm_categories(tags),
            deduplication_key=self._generate_dedup_key(
                tags.get("name", ""),
                center.get("lat", 0.0),
                center.get("lon", 0.0),
            ),
        )

    def _clean_google_place(self, raw: dict) -> SilverPlace:
        result = raw["raw_data"]

        return SilverPlace(
            source_id=raw["source_id"],
            raw_data=raw["raw_data"],
            collected_at=raw["collected_at"],
            city=raw["city"],
            source=raw["source"],
            name=result.get("name", "").strip(),
            address=result.get("formatted_address", ""),
            latitude=result["geometry"]["location"]["lat"],
            longitude=result["geometry"]["location"]["lng"],
            categories=result.get("types", []),
            deduplication_key=self._generate_dedup_key(
                result.get("name", ""),
                result["geometry"]["location"]["lat"],
                result["geometry"]["location"]["lng"],
            ),
        )

    def _deduplicate_places(self, places: List[SilverPlace]) -> List[dict]:
        seen_keys = set()
        deduplicated = []

        for place in places:
            if place.deduplication_key not in seen_keys:
                seen_keys.add(place.deduplication_key)
                deduplicated.append(place.model_dump())

        return deduplicated

    def _build_osm_address(self, tags: dict) -> str:
        parts = []
        for key in ["addr:housenumber", "addr:street", "addr:city"]:
            if key in tags:
                parts.append(tags[key])
        return ", ".join(parts) if parts else ""

    def _extract_osm_categories(self, tags: dict) -> List[str]:
        categories = []
        if "tourism" in tags:
            categories.append(tags["tourism"])
        if "amenity" in tags:
            categories.append(tags["amenity"])
        return categories

    def _generate_dedup_key(self, name: str, lat: float, lng: float) -> str:
        normalized_name = re.sub(r"[^\w\s]", "", name.lower()).strip()
        lat_rounded = round(lat, 3)  # ~100m precision
        lng_rounded = round(lng, 3)
        return f"{normalized_name}_{lat_rounded}_{lng_rounded}"
