"""
OSM Data Ingestion Engine - Bronze Layer Implementation
=======================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/ingestion/ section
Kế thừa pattern từ BaseIngestionEngine

Mục đích:
- Thu thập raw POI data từ OpenStreetMap qua Overpass API
- Transform raw OSM elements thành standardized BronzeRecords
- Lưu trữ vào Bronze layer (raw JSON files)
- Hỗ trợ multi-city, multi-category batch ingestion

Architecture:
- OSMIngestionEngine: Main engine class
- fetch_osm_data(): Overpass API communication
- create_bronze_record(): Data transformation
- ingest_city_category(): Orchestrate single job
- ingest_all(): Batch processing orchestration

Data Flow:
  Overpass API → Raw OSM Elements → BronzeRecord → JSON File (Bronze Layer)

Usage:
    >>> engine = OSMIngestionEngine()
    >>> await engine.ingest_city_category("tokyo", POICategory.RESTAURANT)
    ✅ Saved 1500 records to storage/bronze/osm/tokyo/restaurant/
    
    >>> await engine.ingest_all(
    ...     cities=["tokyo", "osaka"],
    ...     categories=[POICategory.RESTAURANT, POICategory.HOTEL]
    ... )
    ✅ Batch ingestion complete: 4 jobs, 5000 total records
"""

# Import asyncio cho async operations (HTTP requests)
import asyncio

# Import logging để ghi lại ingestion process
import logging

# Import json cho serialization
import json

# Import os cho filesystem operations
import os

# Import datetime classes cho timestamps
# datetime: Tạo timestamp objects
# timezone: Xử lý UTC timestamps
from datetime import datetime, timezone

# Import type hints cho type checking và documentation
from typing import List, Dict, Any, Optional

# Import Path từ pathlib cho cross-platform path handling
from pathlib import Path

# Import httpx cho async HTTP requests
# Httpx: Modern async HTTP client, thay thế aiohttp và requests
import httpx

# Import data schemas từ pipelines.shared
# BronzeRecord: Standardized format cho raw data
# BronzeMetadata: Metadata wrapper cho Bronze records
# SourceType: Enum cho data sources (OSM, Google, etc.)
# POICategory: Enum cho POI categories
# ProcessingStatus: Enum cho processing states
from pipelines.shared.schemas import (
    BronzeRecord, BronzeMetadata, SourceType, POICategory, ProcessingStatus
)

# Import utility functions
# make_ukey: Tạo unique keys
# setup_logging: Cấu hình logging
from pipelines.shared.utils import make_ukey, setup_logging

# ============================================
# LOGGER SETUP
# ============================================
# Khởi tạo logger cho module này
# Logs sẽ có format JSON với correlation ID
logger = setup_logging(__name__)


class OSMIngestionEngine:
    """Engine thu thập OSM data → lưu vào MongoDB bronze_pois với osm_raw schema.
    Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu u_key đã tồn tại).
    """

    OVERPASS_ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.openstreetmap.fr/api/interpreter",
    ]

    # Tags mặc định theo category
    CATEGORY_TAGS: Dict[str, List[tuple]] = {
        "restaurant":  [("amenity", "restaurant"), ("amenity", "fast_food")],
        "cafe":        [("amenity", "cafe")],
        "bar":         [("amenity", "bar"), ("amenity", "pub")],
        "hotel":       [("tourism", "hotel"), ("tourism", "guest_house"), ("tourism", "hostel")],
        "shop":        [("shop", "supermarket"), ("shop", "convenience"), ("shop", "mall")],
        "attraction":  [("tourism", "attraction"), ("tourism", "museum"), ("tourism", "viewpoint")],
        "park":        [("leisure", "park"), ("leisure", "garden")],
        "bank":        [("amenity", "bank"), ("amenity", "atm")],
        "healthcare":  [("amenity", "hospital"), ("amenity", "clinic"), ("amenity", "pharmacy")],
        "entertainment": [("amenity", "cinema"), ("amenity", "theatre"), ("amenity", "nightclub")],
    }

    def __init__(self, mongo_uri: Optional[str] = None):
        import os
        from pymongo import MongoClient

        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self._client = MongoClient(self.mongo_uri)
        self._bronze = self._client.smart_travel_platform.bronze_pois
        logger.info("✅ OSMIngestionEngine connected to MongoDB (bronze_pois)")

    def _create_overpass_query(self, lat: float, lon: float, radius_m: int, tags: List[tuple]) -> str:
        parts = []
        for key, value in tags:
            parts += [
                f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});',
                f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});',
            ]
        body = "\n  ".join(parts)
        return f"[out:json][timeout:180];\n(\n  {body}\n);\nout body center tags meta;"

    def _safe_location(self, element: Dict) -> tuple:
        lat = element.get("lat")
        lon = element.get("lon")
        if lat and lon:
            return lat, lon
        center = element.get("center", {})
        return center.get("lat"), center.get("lon")

    async def _fetch_elements(self, query: str) -> List[Dict]:
        import random
        import httpx as _httpx

        headers = {"User-Agent": "SmartTravel-OSMIngestion/1.0", "Accept": "application/json"}
        endpoints = self.OVERPASS_ENDPOINTS.copy()
        random.shuffle(endpoints)

        async with _httpx.AsyncClient(timeout=180.0) as client:
            for url in endpoints:
                try:
                    resp = await client.get(url, params={"data": query}, headers=headers)
                    if resp.status_code == 200:
                        return resp.json().get("elements", [])
                except Exception as e:
                    logger.warning(f"⚠️ Overpass {url.split('/')[2]} failed: {e}")
                    continue

        logger.error("❌ All Overpass endpoints failed")
        return []

    async def ingest_city_category(
        self,
        city_code: str,
        city_config: Dict[str, Any],
        category: str,
        radius_m: Optional[int] = None
    ) -> Dict[str, int]:
        """Ingest 1 city + 1 category → bronze_pois. Resume-safe."""
        import hashlib as _hashlib

        lat = city_config["lat"]
        lon = city_config["lon"]
        r = radius_m or int(city_config.get("radius_km", 15) * 1000)
        tags = self.CATEGORY_TAGS.get(category, [])

        if not tags:
            logger.warning(f"⚠️ No tags for category '{category}'")
            return {"inserted": 0, "skipped": 0}

        query = self._create_overpass_query(lat, lon, r, tags)
        elements = await self._fetch_elements(query)

        inserted = 0
        skipped = 0
        seen: set = set()

        for element in elements:
            osm_id = element.get("id")
            osm_type = element.get("type")
            session_key = f"{city_code}_{osm_type}_{osm_id}"

            if session_key in seen:
                skipped += 1
                continue
            seen.add(session_key)

            u_key = _hashlib.md5(session_key.encode()).hexdigest()[:16]
            if self._bronze.find_one({"u_key": u_key}, {"_id": 1}):
                skipped += 1
                continue

            item_lat, item_lon = self._safe_location(element)
            if not item_lat or not item_lon:
                continue

            tags_data = element.get("tags", {})
            name = tags_data.get("name") or tags_data.get("name:en") or tags_data.get("official_name")
            if not name:
                continue

            doc = {
                "u_key": u_key,
                "poi_id": f"osm_{osm_type}_{osm_id}",

                # === RAW DATA ===
                "osm_raw": {
                    "element": element,
                    "endpoint": "overpass",
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                },
                "google_raw": None,

                # === FLAGS ===
                "has_osm_data": True,
                "has_google_data": False,
                "data_sources": ["osm"],

                # === BASIC INFO ===
                "name": name,
                "city": city_code,
                "city_name": city_config.get("name", city_code),
                "country": city_config.get("country", "Vietnam"),
                "category": category,
                "location": {"lat": item_lat, "lon": item_lon},

                # === IDS ===
                "osm_id": osm_id,
                "osm_type": osm_type,
                "google_place_id": None,

                # === METADATA ===
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "_layer": "bronze",
                "_source": "osm_ingestion_engine"
            }

            try:
                self._bronze.insert_one(doc)
                inserted += 1
            except Exception as ie:
                err = str(ie)
                if "quota" in err.lower() or "space" in err.lower():
                    logger.error("❌ MongoDB quota exceeded! Stopping.")
                    self._client.close()
                    raise RuntimeError("MongoDB quota exceeded")
                skipped += 1

        logger.info(f"✅ {city_code}/{category}: inserted={inserted}, skipped={skipped}")
        return {"inserted": inserted, "skipped": skipped}

    async def ingest_all(
        self,
        cities: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Ingest tất cả cities × categories → bronze_pois."""
        import asyncio as _asyncio

        target_cities = cities or {
            "hanoi":    {"name": "Hà Nội",      "lat": 21.0278, "lon": 105.8342, "radius_km": 25},
            "hcm":      {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "radius_km": 25},
            "danang":   {"name": "Đà Nẵng",      "lat": 16.0544, "lon": 108.2022, "radius_km": 20},
            "haiphong": {"name": "Hải Phòng",    "lat": 20.8449, "lon": 106.6881, "radius_km": 15},
            "cantho":   {"name": "Cần Thơ",      "lat": 10.0282, "lon": 105.7851, "radius_km": 15},
            "hue":      {"name": "Huế",          "lat": 16.4637, "lon": 107.5909, "radius_km": 15},
            "nhatrang": {"name": "Nha Trang",    "lat": 12.2588, "lon": 109.1967, "radius_km": 15},
            "dalat":    {"name": "Đà Lạt",       "lat": 11.9404, "lon": 108.4453, "radius_km": 12},
            "vungtau":  {"name": "Vũng Tàu",     "lat": 10.2441, "lon": 107.0708, "radius_km": 12},
        }
        target_categories = categories or list(self.CATEGORY_TAGS.keys())

        total_inserted = 0
        total_skipped = 0
        errors = []

        for city_code, city_cfg in target_cities.items():
            logger.info(f"📍 {city_cfg['name']}")
            for cat in target_categories:
                try:
                    result = await self.ingest_city_category(city_code, city_cfg, cat)
                    total_inserted += result["inserted"]
                    total_skipped += result["skipped"]
                    await _asyncio.sleep(1.5)
                except RuntimeError:
                    return {"inserted": total_inserted, "skipped": total_skipped, "errors": errors, "stopped": "quota"}
                except Exception as e:
                    errors.append(f"{city_code}/{cat}: {e}")
                    continue

        self._client.close()
        logger.info(f"🎉 Ingest complete: inserted={total_inserted}, skipped={total_skipped}")
        return {"inserted": total_inserted, "skipped": total_skipped, "errors": errors}


async def main():
    """Main function để run ingestion"""
    engine = OSMIngestionEngine()
    results = await engine.ingest_all()

    logger.info("=" * 50)
    logger.info("📊 INGESTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Inserted : {results['inserted']}")
    logger.info(f"Skipped  : {results['skipped']}")
    if results.get("errors"):
        logger.warning(f"Errors   : {len(results['errors'])}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
