#!/usr/bin/env python
"""
Collect Google Places Only → bronze_pois
=========================================
Thu thập POIs chỉ từ Google Places API (qua RapidAPI).
Lưu vào bronze_pois với google_raw schema.
Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu đã tồn tại).

Usage:
    python collect_google_only.py
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
# CONFIG
# ==========================================

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
)

RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
NEARBY_SEARCH_URL = f"https://{RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = f"https://{RAPIDAPI_HOST}/maps/api/place/details/json"

_KEYS_FILE = Path(__file__).parent.parent / "storage" / "configs" / "rapidapi_keys.json"
try:
    with open(_KEYS_FILE, "r") as f:
        RAPIDAPI_KEYS = json.load(f)
except Exception:
    RAPIDAPI_KEYS = []

_key_index = 0


def _get_next_key():
    global _key_index
    if not RAPIDAPI_KEYS:
        raise RuntimeError(f"No RapidAPI keys found in {_KEYS_FILE}")
    key = RAPIDAPI_KEYS[_key_index % len(RAPIDAPI_KEYS)]
    _key_index += 1
    return key


def _rapidapi_headers():
    return {
        "x-rapidapi-key": _get_next_key(),
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }


CITIES = {
    "hanoi":    {"name": "Hà Nội",        "lat": 21.0278, "lon": 105.8342, "country": "Vietnam"},
    "hcm":      {"name": "Hồ Chí Minh",   "lat": 10.8231, "lon": 106.6297, "country": "Vietnam"},
    "danang":   {"name": "Đà Nẵng",        "lat": 16.0544, "lon": 108.2022, "country": "Vietnam"},
    "cantho":   {"name": "Cần Thơ",        "lat": 10.0282, "lon": 105.7851, "country": "Vietnam"},
    "haiphong": {"name": "Hải Phòng",      "lat": 20.8449, "lon": 106.6881, "country": "Vietnam"},
    "hue":      {"name": "Huế",            "lat": 16.4637, "lon": 107.5909, "country": "Vietnam"},
    "nhatrang": {"name": "Nha Trang",      "lat": 12.2588, "lon": 109.1967, "country": "Vietnam"},
    "dalat":    {"name": "Đà Lạt",         "lat": 11.9404, "lon": 108.4453, "country": "Vietnam"},
    "vungtau":  {"name": "Vũng Tàu",       "lat": 10.2441, "lon": 107.0708, "country": "Vietnam"},
}

CATEGORIES = ["restaurant", "cafe", "hotel", "tourist_attraction"]


def get_place_details(place_id):
    """Lấy chi tiết POI từ RapidAPI."""
    params = {"place_id": place_id, "fields": "all", "language": "vi"}
    try:
        resp = requests.get(PLACE_DETAILS_URL, headers=_rapidapi_headers(), params=params, timeout=30)
        return resp.json()
    except Exception:
        return {}


def collect_google_only():
    """Thu thập Google-only POIs → bronze_pois, resume-safe."""
    print("=" * 70)
    print("🚀 COLLECT GOOGLE PLACES → bronze_pois")
    print("=" * 70)

    if not RAPIDAPI_KEYS:
        print(f"❌ No RapidAPI keys found in {_KEYS_FILE}")
        return

    print(f"🔑 Loaded {len(RAPIDAPI_KEYS)} RapidAPI keys")

    client = MongoClient(MONGODB_URI)
    db = client.smart_travel_platform
    bronze = db.bronze_pois

    total_inserted = 0
    total_skipped = 0

    for city_code, city_cfg in CITIES.items():
        print(f"\n📍 {city_cfg['name'].upper()}")
        lat, lon = city_cfg["lat"], city_cfg["lon"]

        for category in CATEGORIES:
            print(f"   🔍 {category}...", end=" ", flush=True)

            try:
                params = {
                    "location": f"{lat},{lon}",
                    "radius": 3000,
                    "type": category,
                    "language": "vi"
                }
                resp = requests.get(
                    NEARBY_SEARCH_URL,
                    headers=_rapidapi_headers(),
                    params=params,
                    timeout=30
                )
                data = resp.json()
                status = data.get("status")

                if status in ("REQUEST_DENIED", "INVALID_REQUEST"):
                    print(f"\n❌ RapidAPI error: {status}. Stopping.")
                    client.close()
                    return

                results = data.get("results", [])
                cat_inserted = 0
                cat_skipped = 0

                for place in results:
                    place_id = place.get("place_id")
                    if not place_id:
                        continue

                    # Bỏ qua nếu đã tồn tại
                    if bronze.find_one({"google_place_id": place_id}, {"_id": 1}):
                        cat_skipped += 1
                        continue

                    details = get_place_details(place_id)
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
                        "city_name": city_cfg["name"],
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
                        "_source": "google_collector"
                    }

                    try:
                        bronze.insert_one(doc)
                        cat_inserted += 1
                    except Exception as ie:
                        err = str(ie)
                        if "quota" in err.lower() or "space" in err.lower():
                            print(f"\n❌ MongoDB quota exceeded! Stopping.")
                            client.close()
                            return
                        cat_skipped += 1

                    time.sleep(0.5)

                print(f"✅ +{cat_inserted} (skip {cat_skipped})")
                total_inserted += cat_inserted
                total_skipped += cat_skipped
                time.sleep(1)

            except Exception as e:
                print(f"❌ {str(e)[:60]}")
                continue

    print("\n" + "=" * 70)
    print("📊 COLLECTION COMPLETE")
    print("=" * 70)
    print(f"   Inserted this run : {total_inserted:,}")
    print(f"   Skipped (exists)  : {total_skipped:,}")

    total_db = bronze.count_documents({"has_google_data": True, "has_osm_data": False})
    print(f"   Total Google-only in bronze_pois: {total_db:,}")

    client.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    collect_google_only()
