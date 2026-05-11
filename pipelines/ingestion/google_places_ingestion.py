"""
Google Places Data Ingestion Engine → bronze_pois
==================================================
Thu thập POI data từ Google Places API (RapidAPI) → lưu vào MongoDB bronze_pois.
Schema: google_raw { place, place_details, place_id, fetched_at }
Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu google_place_id đã tồn tại).
Quota guard: tự rotate key, dừng ngay nếu tất cả keys hết quota.

Usage:
    >>> engine = GooglePlacesIngestionEngine()
    >>> result = await engine.ingest_city("hanoi", "hcm", ["restaurant", "hotel"])
    >>> await engine.ingest_all(cities={...}, categories=[...])
"""

import asyncio
import json
import os
import hashlib
import requests
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from pymongo import MongoClient
from pipelines.shared.utils import setup_logging

logger = setup_logging(__name__)

# ==========================================
# RapidAPI config
# ==========================================
_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/details/json"

_KEYS_FILE = Path(__file__).parent.parent.parent / "storage" / "configs" / "rapidapi_keys.json"
try:
    with open(_KEYS_FILE, "r") as _f:
        _RAPIDAPI_KEYS: List[str] = json.load(_f)
except Exception:
    _RAPIDAPI_KEYS = []

_key_index = 0


def _get_next_key() -> str:
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError(f"No RapidAPI keys found in {_KEYS_FILE}")
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
    for _ in range(len(_RAPIDAPI_KEYS) or 1):
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


# =============================================================================
# GOOGLE PLACES INGESTION ENGINE
# =============================================================================

class GooglePlacesIngestionEngine:
    """
    Engine thu thập Google Places data → lưu vào MongoDB bronze_pois.
    Schema: google_raw { place, place_details, place_id, fetched_at }
    Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu google_place_id đã tồn tại).
    Quota guard: dừng ngay nếu tất cả RapidAPI keys hết quota.
    """

    DEFAULT_CITIES = {
        "hanoi":    {"name": "Hà Nội",      "lat": 21.0278, "lon": 105.8342, "country": "Vietnam"},
        "hcm":      {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "country": "Vietnam"},
        "danang":   {"name": "Đà Nẵng",     "lat": 16.0544, "lon": 108.2022, "country": "Vietnam"},
        "cantho":   {"name": "Cần Thơ",     "lat": 10.0282, "lon": 105.7851, "country": "Vietnam"},
        "haiphong": {"name": "Hải Phòng",   "lat": 20.8449, "lon": 106.6881, "country": "Vietnam"},
        "hue":      {"name": "Huế",         "lat": 16.4637, "lon": 107.5909, "country": "Vietnam"},
        "nhatrang": {"name": "Nha Trang",   "lat": 12.2588, "lon": 109.1967, "country": "Vietnam"},
        "dalat":    {"name": "Đà Lạt",      "lat": 11.9404, "lon": 108.4453, "country": "Vietnam"},
        "vungtau":  {"name": "Vũng Tàu",    "lat": 10.2441, "lon": 107.0708, "country": "Vietnam"},
    }

    DEFAULT_CATEGORIES = [
        "restaurant", "cafe", "bar", "lodging",
        "tourist_attraction", "museum", "park", "shopping_mall"
    ]

    def __init__(self, mongo_uri: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self._client = MongoClient(self.mongo_uri)
        self._bronze = self._client.smart_travel_platform.bronze_pois
        logger.info(f"GooglePlacesIngestionEngine initialized with {len(_RAPIDAPI_KEYS)} RapidAPI keys")

    async def ingest_city_category(
        self,
        city_code: str,
        city_cfg: Dict[str, Any],
        category: str,
        radius: int = 3000
    ) -> Dict[str, Any]:
        """
        Ingest 1 city + 1 category → bronze_pois. Resume-safe.

        Returns:
            {"inserted": int, "skipped": int, "stopped": bool}
        """
        lat, lon = city_cfg["lat"], city_cfg["lon"]
        logger.info(f"Ingesting {category} in {city_cfg['name']}")

        search_result = _call_rapidapi(_NEARBY_SEARCH_URL, {
            "location": f"{lat},{lon}",
            "radius": radius,
            "type": category,
            "language": "vi"
        })

        status = search_result.get("status")

        if status == "QUOTA_EXCEEDED_ALL_KEYS":
            logger.error(f"All {len(_RAPIDAPI_KEYS)} RapidAPI keys exceeded daily quota. Stopping.")
            return {"inserted": 0, "skipped": 0, "stopped": True}

        if status in ("REQUEST_DENIED", "INVALID_REQUEST"):
            logger.error(f"RapidAPI error: {status}")
            return {"inserted": 0, "skipped": 0, "stopped": True}

        places = search_result.get("results", [])
        inserted = skipped = 0

        for place in places:
            place_id = place.get("place_id")
            if not place_id:
                continue

            if self._bronze.find_one({"google_place_id": place_id}, {"_id": 1}):
                skipped += 1
                continue

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
                "city_name": city_cfg.get("name", city_code),
                "country": city_cfg.get("country", "Vietnam"),
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
                "_source": "google_places_ingestion"
            }

            try:
                self._bronze.insert_one(doc)
                inserted += 1
            except Exception as ie:
                err = str(ie)
                if "quota" in err.lower() or "space" in err.lower():
                    logger.error("MongoDB quota exceeded! Stopping.")
                    return {"inserted": inserted, "skipped": skipped, "stopped": True}
                skipped += 1

            await asyncio.sleep(0.5)

        logger.info(f"✅ {city_cfg['name']}/{category}: inserted={inserted}, skipped={skipped}")
        return {"inserted": inserted, "skipped": skipped, "stopped": False}

    async def ingest_city(
        self,
        city_code: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest tất cả categories cho 1 city.

        Args:
            city_code: Key trong DEFAULT_CITIES
            categories: Danh sách category (mặc định: DEFAULT_CATEGORIES)
        """
        city_cfg = self.DEFAULT_CITIES.get(city_code)
        if not city_cfg:
            logger.error(f"City '{city_code}' not found in DEFAULT_CITIES")
            return {"inserted": 0, "skipped": 0, "stopped": False}

        cats = categories or self.DEFAULT_CATEGORIES
        total_inserted = total_skipped = 0

        for cat in cats:
            result = await self.ingest_city_category(city_code, city_cfg, cat)
            total_inserted += result["inserted"]
            total_skipped += result["skipped"]
            if result.get("stopped"):
                return {"city": city_code, "inserted": total_inserted, "skipped": total_skipped, "stopped": True}
            await asyncio.sleep(1)

        return {"city": city_code, "inserted": total_inserted, "skipped": total_skipped, "stopped": False}

    async def ingest_all(
        self,
        cities: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ingest tất cả cities × categories → bronze_pois.

        Args:
            cities: Dict city_code → config (mặc định: DEFAULT_CITIES)
            categories: Danh sách category (mặc định: DEFAULT_CATEGORIES)
        """
        target_cities = cities or self.DEFAULT_CITIES
        cats = categories or self.DEFAULT_CATEGORIES

        total_inserted = total_skipped = 0
        results_by_city: Dict[str, Any] = {}

        for city_code, city_cfg in target_cities.items():
            logger.info(f"=== {city_cfg['name']} ===")
            city_inserted = city_skipped = 0

            for cat in cats:
                result = await self.ingest_city_category(city_code, city_cfg, cat)
                city_inserted += result["inserted"]
                city_skipped += result["skipped"]
                if result.get("stopped"):
                    self._client.close()
                    return {
                        "total_inserted": total_inserted + city_inserted,
                        "total_skipped": total_skipped + city_skipped,
                        "by_city": results_by_city,
                        "stopped": True
                    }
                await asyncio.sleep(1)

            total_inserted += city_inserted
            total_skipped += city_skipped
            results_by_city[city_code] = {"inserted": city_inserted, "skipped": city_skipped}

        self._client.close()
        logger.info(f"🎉 Ingest complete: inserted={total_inserted}, skipped={total_skipped}")
        return {
            "total_inserted": total_inserted,
            "total_skipped": total_skipped,
            "by_city": results_by_city,
            "cities_processed": len(target_cities),
            "categories": cats
        }

    def close(self):
        self._client.close()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    import sys
    engine = GooglePlacesIngestionEngine()

    if len(sys.argv) >= 2:
        city_code = sys.argv[1]
        cats = sys.argv[2].split(",") if len(sys.argv) > 2 else None
        result = await engine.ingest_city(city_code, cats)
    else:
        result = await engine.ingest_all()

    print(f"\n✅ Done!")
    print(f"   Inserted : {result.get('total_inserted', result.get('inserted', 0)):,}")
    print(f"   Skipped  : {result.get('total_skipped', result.get('skipped', 0)):,}")
    if result.get("stopped"):
        print("   ⚠️  Stopped early (quota exceeded)")


if __name__ == "__main__":
    asyncio.run(main())
