#!/usr/bin/env python
"""
Mass Collection System → bronze_pois
======================================
Thu thập Google Places POIs cho 8 cities × N categories với grid-based collection.
Lưu vào bronze_pois với google_raw schema.
Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu google_place_id đã tồn tại).
Dùng rapidapi_keys.json với quota guard (dừng ngay khi tất cả keys hết quota).
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient
import requests


# ==========================================
# CONFIGURATION
# ==========================================

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
)

_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/details/json"

from src.core.config import settings

_RAPIDAPI_KEYS = settings.rapid_api_keys

_key_index = 0


def _get_next_key():
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError("No RapidAPI keys found in settings/env")
    key = _RAPIDAPI_KEYS[_key_index % len(_RAPIDAPI_KEYS)]
    _key_index += 1
    return key


def _rapidapi_headers():
    return {
        "x-rapidapi-key": _get_next_key(),
        "x-rapidapi-host": _RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }


def _call_rapidapi(url, params):
    """Gọi RapidAPI với auto-rotate key khi gặp quota exceeded."""
    for _ in range(len(_RAPIDAPI_KEYS) or 1):
        try:
            resp = requests.get(url, headers=_rapidapi_headers(), params=params, timeout=30)
            data = resp.json()
            msg = data.get("message", "")
            if "quota" in msg.lower() or "exceeded" in msg.lower() or "limit" in msg.lower():
                continue
            return data
        except Exception:
            continue
    return {"status": "QUOTA_EXCEEDED_ALL_KEYS"}


CITIES_TIER1 = {
    "hanoi":    {"name": "Hà Nội",      "lat": 21.0278, "lon": 105.8342, "country": "Vietnam"},
    "hcm":      {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "country": "Vietnam"},
    "danang":   {"name": "Đà Nẵng",     "lat": 16.0544, "lon": 108.2022, "country": "Vietnam"},
    "haiphong": {"name": "Hải Phòng",   "lat": 20.8449, "lon": 106.6881, "country": "Vietnam"},
    "cantho":   {"name": "Cần Thơ",     "lat": 10.0452, "lon": 105.7469, "country": "Vietnam"},
    "nhatrang": {"name": "Nha Trang",   "lat": 12.2388, "lon": 109.1967, "country": "Vietnam"},
    "dalat":    {"name": "Đà Lạt",      "lat": 11.9404, "lon": 108.4583, "country": "Vietnam"},
    "hue":      {"name": "Huế",         "lat": 16.4637, "lon": 107.5909, "country": "Vietnam"},
}

CATEGORIES = [
    "restaurant", "cafe", "hotel", "tourist_attraction",
    "shopping_mall", "supermarket", "bar", "spa", "gym"
]

GRID_POINTS_PER_CITY = 9
SEARCH_RADIUS = 2000


class MassCollector:
    """Mass collection system → bronze_pois, resume-safe, quota guard."""

    def __init__(self):
        self._client = MongoClient(MONGODB_URI)
        self._bronze = self._client.smart_travel_platform.bronze_pois
        self.job_id = f"mass_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {
            "inserted": 0,
            "skipped": 0,
            "failed_tasks": 0,
            "by_city": {},
            "by_category": {}
        }
        print(f"✅ Connected to MongoDB Atlas")
        print(f"🔑 Loaded {len(_RAPIDAPI_KEYS)} RapidAPI keys")

    def _create_grid(self, lat, lon, num_points=9):
        """3×3 grid xung quanh tâm city."""
        points = []
        spacing = 0.018  # ~2km
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                points.append({
                    "lat": round(lat + i * spacing, 6),
                    "lon": round(lon + j * spacing, 6),
                    "gi": i, "gj": j
                })
        return points[:num_points]

    def _collect_point(self, city_code, city_cfg, category, point):
        """Thu thập 1 grid point, insert ngay vào bronze_pois. Return (inserted, skipped, quota_exceeded)."""
        data = _call_rapidapi(_NEARBY_SEARCH_URL, {
            "location": f"{point['lat']},{point['lon']}",
            "radius": SEARCH_RADIUS,
            "type": category,
            "language": "vi"
        })

        status = data.get("status")
        if status == "QUOTA_EXCEEDED_ALL_KEYS":
            return 0, 0, True

        places = data.get("results", [])
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
            if details.get("status") == "QUOTA_EXCEEDED_ALL_KEYS":
                return inserted, skipped, True

            u_key = hashlib.md5(f"google_{place_id}".encode()).hexdigest()[:16]
            geo = place.get("geometry", {}).get("location", {})

            doc = {
                "u_key": u_key,
                "poi_id": f"google_{place_id}",
                "osm_raw": None,
                "google_raw": {
                    "place": place,
                    "place_details": details,
                    "place_id": place_id,
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                },
                "has_osm_data": False,
                "has_google_data": True,
                "data_sources": ["google"],
                "name": place.get("name", "Unknown"),
                "city": city_code,
                "city_name": city_cfg.get("name", city_code),
                "country": city_cfg.get("country", "Vietnam"),
                "category": category,
                "location": {"lat": geo.get("lat"), "lon": geo.get("lng")},
                "osm_id": None,
                "osm_type": None,
                "google_place_id": place_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "_layer": "bronze",
                "_source": "mass_collection",
                "_job_id": self.job_id,
                "_grid": f"{point['gi']},{point['gj']}"
            }

            try:
                self._bronze.insert_one(doc)
                inserted += 1
            except Exception as ie:
                err = str(ie)
                if "quota" in err.lower() or "space" in err.lower():
                    return inserted, skipped, True
                skipped += 1

        return inserted, skipped, False

    def run_collection(self):
        """Run mass collection tuần tự, dừng ngay khi quota exceeded."""
        if not _RAPIDAPI_KEYS:
            print("❌ No RapidAPI keys found in settings/env")
            return

        print("=" * 70)
        print("🚀 MASS COLLECTION → bronze_pois")
        print("=" * 70)
        print(f"🏙️  Cities    : {len(CITIES_TIER1)}")
        print(f"📁 Categories : {len(CATEGORIES)}")
        print(f"🔍 Grid points: {GRID_POINTS_PER_CITY}/city")
        print(f"📝 Job ID     : {self.job_id}")
        print("=" * 70)

        start_time = time.time()

        for city_code, city_cfg in CITIES_TIER1.items():
            print(f"\n📍 {city_cfg['name'].upper()}")
            grid = self._create_grid(city_cfg["lat"], city_cfg["lon"], GRID_POINTS_PER_CITY)
            city_inserted = city_skipped = 0

            for category in CATEGORIES:
                cat_inserted = cat_skipped = 0
                for point in grid:
                    ins, skp, quota_exceeded = self._collect_point(city_code, city_cfg, category, point)
                    cat_inserted += ins
                    cat_skipped += skp
                    if quota_exceeded:
                        print(f"\n❌ All {len(_RAPIDAPI_KEYS)} RapidAPI keys exceeded daily quota. Stopping.")
                        self._print_summary(start_time)
                        self._client.close()
                        return
                    time.sleep(0.5)

                city_inserted += cat_inserted
                city_skipped += cat_skipped
                self.stats["by_category"][category] = self.stats["by_category"].get(category, 0) + cat_inserted
                print(f"   {category}: +{cat_inserted} inserted (skip {cat_skipped})")
                time.sleep(1)

            self.stats["inserted"] += city_inserted
            self.stats["skipped"] += city_skipped
            self.stats["by_city"][city_code] = city_inserted
            print(f"   � {city_cfg['name']}: inserted={city_inserted}, skipped={city_skipped}")

        self._print_summary(start_time)
        self._client.close()

    def _print_summary(self, start_time):
        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print("✅ COLLECTION COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time      : {elapsed/60:.1f} min")
        print(f"📊 Inserted  : {self.stats['inserted']:,}")
        print(f"⏭️  Skipped   : {self.stats['skipped']:,}")
        total_db = self._bronze.count_documents({"has_google_data": True})
        print(f"� Total DB  : {total_db:,} Google POIs in bronze_pois")

        print("\n📍 By City:")
        for city, cnt in sorted(self.stats["by_city"].items(), key=lambda x: -x[1]):
            print(f"   {city}: {cnt}")

        print("\n📁 By Category:")
        for cat, cnt in sorted(self.stats["by_category"].items(), key=lambda x: -x[1]):
            print(f"   {cat}: {cnt}")

    def close(self):
        self._client.close()


def main():
    collector = MassCollector()
    try:
        collector.run_collection()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        collector.close()


if __name__ == "__main__":
    main()
