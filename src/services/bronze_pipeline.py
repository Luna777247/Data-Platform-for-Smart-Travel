"""
Bronze Pipeline Service
=======================
Thu thập Google Places data → lưu vào bronze_pois với google_raw schema.
Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu google_place_id đã tồn tại).
Dùng RapidAPI keys từ .env với quota guard.
"""
import asyncio
import hashlib
import json
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.db.client import get_database
from src.core.logging import get_logger

logger = get_logger(__name__)

# ==========================================
# RapidAPI config
# ==========================================
_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/details/json"

from src.core.config import settings

_RAPIDAPI_KEYS = settings.rapid_api_keys

_key_index = 0


def _get_next_key() -> str:
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError("No RapidAPI keys found in settings/env")
    key = _RAPIDAPI_KEYS[_key_index % len(_RAPIDAPI_KEYS)]
    _key_index += 1
    return key


def _rapidapi_headers() -> Dict[str, str]:
    return {
        "x-rapidapi-key": _get_next_key(),
        "x-rapidapi-host": _RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }


def _call_rapidapi(url: str, params: Dict) -> Dict:
    """Gọi RapidAPI với auto-rotate key khi gặp quota exceeded."""
    for _ in range(len(_RAPIDAPI_KEYS)):
        try:
            resp = requests.get(url, headers=_rapidapi_headers(), params=params, timeout=30)
            data = resp.json()
            msg = data.get("message", "")
            if "quota" in msg.lower() or "exceeded" in msg.lower() or "limit" in msg.lower():
                continue
            return data
        except Exception as e:
            logger.warning(f"RapidAPI call error: {e}")
            continue
    return {"status": "QUOTA_EXCEEDED_ALL_KEYS"}


class BronzePipeline:
    """
    Pipeline cho Bronze layer:
    - Thu thập Google Places data qua RapidAPI
    - Lưu vào MongoDB bronze_pois với google_raw schema
    - Insert từng POI ngay lập tức, resume-safe
    - Collection: bronze_pois
    """

    def __init__(self):
        self.collection_name = "bronze_pois"

    @property
    def db(self):
        from src.api.dependencies.database import mongo_client
        from src.core.config import settings
        return mongo_client[settings.mongodb_database]

    async def collect_city_category(
        self,
        city: str,
        city_code: str,
        lat: float,
        lng: float,
        category: str,
        radius: int = 3000,
        country: str = "Vietnam"
    ) -> Dict[str, Any]:
        """
        Thu thập Google-only POIs cho 1 city + category → bronze_pois.
        Resume-safe: bỏ qua nếu google_place_id đã tồn tại.

        Returns:
            {"inserted": int, "skipped": int, "stopped": bool}
        """
        logger.info(f"Collecting {category} in {city}...")

        if not _RAPIDAPI_KEYS:
            logger.error("No RapidAPI keys found in settings/env")
            return {"inserted": 0, "skipped": 0, "stopped": True}

        collection = self.db[self.collection_name]
        search_result = _call_rapidapi(_NEARBY_SEARCH_URL, {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": category,
            "language": "vi"
        })

        status = search_result.get("status")

        if status == "QUOTA_EXCEEDED_ALL_KEYS":
            logger.error("All RapidAPI keys exceeded daily quota")
            return {"inserted": 0, "skipped": 0, "stopped": True}

        if status not in ("OK", None) and "results" not in search_result:
            logger.warning(f"Search failed for {city}/{category}: {status}")
            return {"inserted": 0, "skipped": 0, "stopped": False}

        places = search_result.get("results", [])
        inserted = 0
        skipped = 0

        for place in places:
            place_id = place.get("place_id")
            if not place_id:
                continue

            # Bỏ qua nếu đã tồn tại
            existing = await collection.find_one({"google_place_id": place_id}, {"_id": 1})
            if existing:
                skipped += 1
                continue

            # Lấy place details
            details = _call_rapidapi(_PLACE_DETAILS_URL, {
                "place_id": place_id,
                "fields": "all",
                "language": "vi"
            })

            u_key = hashlib.md5(f"google_{place_id}".encode()).hexdigest()[:16]
            geo = place.get("geometry", {}).get("location", {})

            doc = {
                "u_key": u_key,
                "poi_id": f"google_{place_id}",

                # === RAW DATA ===
                "osm_raw": None,
                "google_raw": {
                    "place": place,
                    "place_details": details,
                    "place_id": place_id,
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                },

                # === FLAGS ===
                "has_osm_data": False,
                "has_google_data": True,
                "data_sources": ["google"],

                # === BASIC INFO ===
                "name": place.get("name", "Unknown"),
                "city": city_code,
                "city_name": city,
                "country": country,
                "category": category,
                "location": {
                    "lat": geo.get("lat"),
                    "lon": geo.get("lng")
                },

                # === IDS ===
                "osm_id": None,
                "osm_type": None,
                "google_place_id": place_id,

                # === METADATA ===
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "_layer": "bronze",
                "_source": "bronze_pipeline"
            }

            try:
                await collection.insert_one(doc)
                inserted += 1
            except Exception as ie:
                err = str(ie)
                if "quota" in err.lower() or "space" in err.lower():
                    logger.error("MongoDB quota exceeded! Stopping.")
                    return {"inserted": inserted, "skipped": skipped, "stopped": True}
                skipped += 1

            await asyncio.sleep(0.5)

        logger.info(f"Saved {inserted} bronze records for {city}/{category} (skipped {skipped})")
        return {"inserted": inserted, "skipped": skipped, "stopped": False}

    async def run_mass_collection(
        self,
        cities: List[Dict[str, Any]],
        categories: List[str]
    ) -> Dict[str, Any]:
        """
        Mass collection cho nhiều cities và categories → bronze_pois.

        Args:
            cities: List of {"name": str, "code": str, "lat": float, "lng": float, "country": str}
            categories: List of category strings

        Returns:
            Collection summary
        """
        total_inserted = 0
        total_skipped = 0
        results_by_city = {}

        for city_data in cities:
            city_name = city_data["name"]
            city_code = city_data.get("code", city_name.lower())
            lat = city_data["lat"]
            lng = city_data["lng"]
            country = city_data.get("country", "Vietnam")

            logger.info(f"=== Processing city: {city_name} ===")
            city_inserted = 0
            city_skipped = 0

            for category in categories:
                result = await self.collect_city_category(
                    city=city_name,
                    city_code=city_code,
                    lat=lat,
                    lng=lng,
                    category=category,
                    country=country
                )
                city_inserted += result["inserted"]
                city_skipped += result["skipped"]

                if result.get("stopped"):
                    logger.error("Stopping mass collection due to quota/error.")
                    return {
                        "total_inserted": total_inserted + city_inserted,
                        "total_skipped": total_skipped + city_skipped,
                        "by_city": results_by_city,
                        "stopped": True
                    }

                await asyncio.sleep(1)

            total_inserted += city_inserted
            total_skipped += city_skipped
            results_by_city[city_name] = {"inserted": city_inserted, "skipped": city_skipped}

        return {
            "total_inserted": total_inserted,
            "total_skipped": total_skipped,
            "by_city": results_by_city,
            "cities_processed": len(cities),
            "categories": categories
        }

    async def get_bronze_stats(self) -> Dict[str, Any]:
        """Lấy thống kê bronze_pois từ MongoDB"""
        try:
            collection = self.db[self.collection_name]
            total = await collection.count_documents({})
            osm_only = await collection.count_documents({"has_osm_data": True, "has_google_data": False})
            google_only = await collection.count_documents({"has_osm_data": False, "has_google_data": True})
            both = await collection.count_documents({"has_osm_data": True, "has_google_data": True})
            by_city = await collection.aggregate([
                {"$group": {"_id": "$city", "count": {"$sum": 1}}}
            ]).to_list(100)

            return {
                "total": total,
                "osm_only": osm_only,
                "google_only": google_only,
                "both_sources": both,
                "by_city": {item["_id"]: item["count"] for item in by_city}
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total": 0}

    async def list_bronze_records(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Liệt kê bronze_pois từ MongoDB"""
        query: Dict[str, Any] = {"_layer": "bronze"}
        if city:
            query["city"] = city
        if category:
            query["category"] = category
        if source == "osm":
            query["has_osm_data"] = True
        elif source == "google":
            query["has_google_data"] = True

        cursor = self.db[self.collection_name].find(query).limit(limit)
        return await cursor.to_list(length=limit)
