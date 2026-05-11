#!/usr/bin/env python3
"""
Enrich Google Raw Data
======================
Thêm google_raw vào POIs đã có osm_raw trong bronze_pois.
Hoặc tạo mới POI chỉ có google_raw (Google-only).
Dùng RapidAPI với key rotation từ storage/configs/rapidapi_keys.json.

Usage:
    python enrich_google_raw.py          # Enrich OSM POIs đã có
    python enrich_google_raw.py hanoi    # Enrich chỉ 1 city
    python enrich_google_raw.py only     # Collect Google-only POIs mới
"""
import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
)

# RapidAPI config
RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
NEARBY_SEARCH_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/details/json"

# Load keys từ file
_KEYS_FILE = Path(__file__).parent / "storage" / "configs" / "rapidapi_keys.json"
try:
    with open(_KEYS_FILE, "r") as f:
        RAPIDAPI_KEYS = json.load(f)
except Exception:
    RAPIDAPI_KEYS = []

_key_index = 0


def _get_next_key():
    """Round-robin key rotation"""
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
    "hanoi": {"name": "Hà Nội", "lat": 21.0278, "lon": 105.8342},
    "hcm": {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
    "danang": {"name": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022},
    "cantho": {"name": "Cần Thơ", "lat": 10.0282, "lon": 105.7851},
    "haiphong": {"name": "Hải Phòng", "lat": 20.8449, "lon": 106.6881},
    "hue": {"name": "Huế", "lat": 16.4637, "lon": 107.5909},
    "nhatrang": {"name": "Nha Trang", "lat": 12.2588, "lon": 109.1967},
    "dalat": {"name": "Đà Lạt", "lat": 11.9404, "lon": 108.4453},
    "vungtau": {"name": "Vũng Tàu", "lat": 10.2441, "lon": 107.0708},
}


def search_nearby(lat, lon, radius=100, type_filter=None):
    """Nearby Search qua RapidAPI Google Map Places"""
    import requests

    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "language": "vi"
    }
    if type_filter:
        params["type"] = type_filter

    response = requests.get(
        NEARBY_SEARCH_URL,
        headers=_rapidapi_headers(),
        params=params,
        timeout=30
    )
    return response.json()


def get_place_details(place_id):
    """Place Details qua RapidAPI Google Map Places"""
    import requests

    params = {
        "place_id": place_id,
        "fields": "all",
        "language": "vi"
    }

    response = requests.get(
        PLACE_DETAILS_URL,
        headers=_rapidapi_headers(),
        params=params,
        timeout=30
    )
    return response.json()


def enrich_google_raw(limit=100, city=None):
    """
    Enrich OSM POIs đã có trong bronze_pois với Google raw data.
    Chỉ xử lý POIs chưa có google_raw (has_google_data=False).
    Chạy lại an toàn - tự bỏ qua POIs đã enrich rồi.
    """
    print("=" * 70)
    print("🔍 ENRICH GOOGLE RAW DATA")
    print("=" * 70)

    if not RAPIDAPI_KEYS:
        print(f"❌ No RapidAPI keys found in {_KEYS_FILE}")
        return
    print(f"🔑 Loaded {len(RAPIDAPI_KEYS)} RapidAPI keys")

    client = MongoClient(MONGODB_URI)
    db = client.smart_travel_platform
    bronze = db.bronze_pois

    # Chỉ lấy POIs chưa có Google data
    query = {
        "has_osm_data": True,
        "has_google_data": False,
        "location": {"$exists": True}
    }
    if city:
        query["city"] = city

    total_pending = bronze.count_documents(query)
    pois_to_enrich = list(bronze.find(query).limit(limit))

    print(f"📍 Pending (no Google data): {total_pending}")
    print(f"📋 Processing this run: {len(pois_to_enrich)}")
    if city:
        print(f"🏙️  City filter: {city}")

    enriched = 0
    not_found = 0
    errors = 0

    for poi in pois_to_enrich:
        try:
            loc = poi["location"]
            lat, lon = loc["lat"], loc["lon"]
            name = poi.get("name", "Unknown")

            # Search nearby (radius nhỏ để khớp đúng POI tại tọa độ đó)
            search_result = search_nearby(lat, lon, radius=100)
            status = search_result.get("status")

            if status in ("REQUEST_DENIED", "INVALID_REQUEST"):
                print(f"\n❌ RapidAPI error: {status}. Stopping.")
                client.close()
                return

            if status != "OK":
                not_found += 1
                continue

            results = search_result.get("results", [])
            if not results:
                not_found += 1
                continue

            # Lấy kết quả gần nhất
            closest = results[0]
            place_id = closest.get("place_id")

            # Get full details
            details = get_place_details(place_id)

            # google_raw - chỉ lưu 1 place (closest), không lưu toàn bộ results list
            google_raw = {
                "place": closest,          # Raw place object từ nearby search
                "place_details": details,  # Full details response
                "place_id": place_id,
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }

            # Update ngay từng POI
            bronze.update_one(
                {"_id": poi["_id"]},
                {
                    "$set": {
                        "google_raw": google_raw,
                        "has_google_data": True,
                        "google_place_id": place_id,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$addToSet": {
                        "data_sources": "google"
                    }
                }
            )

            enriched += 1
            print(f"   ✅ [{enriched}] {name}")

            time.sleep(1)  # Rate limit

        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "space" in err.lower():
                print(f"\n❌ MongoDB quota exceeded! Stopping.")
                client.close()
                return
            print(f"   ⚠️  Error ({poi.get('name', '?')}): {err[:60]}")
            errors += 1
            continue

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   Enriched this run : {enriched}")
    print(f"   Not found (Google): {not_found}")
    print(f"   Errors             : {errors}")
    print(f"   Still pending      : {total_pending - enriched}")

    total_google = bronze.count_documents({"has_google_data": True})
    both = bronze.count_documents({"has_osm_data": True, "has_google_data": True})
    print(f"\n   Total with Google  : {total_google}")
    print(f"   Total with both    : {both}")

    client.close()
    print("\n✅ Done!")


def collect_google_only(city_code, city_config, category="restaurant", limit=50):
    """
    Collect Google-only POIs (không có OSM data).
    Insert từng POI ngay lập tức, bỏ qua nếu đã tồn tại.
    """
    print(f"\n📍 Collecting Google-only: {city_config['name']} / {category}")

    if not RAPIDAPI_KEYS:
        print(f"❌ No RapidAPI keys found in {_KEYS_FILE}")
        return

    client = MongoClient(MONGODB_URI)
    db = client.smart_travel_platform
    bronze = db.bronze_pois

    lat, lon = city_config["lat"], city_config["lon"]

    search_result = search_nearby(lat, lon, radius=5000, type_filter=category)
    status = search_result.get("status")

    if status != "OK":
        print(f"   ❌ Search failed: {status}")
        client.close()
        return

    results = search_result.get("results", [])[:limit]
    print(f"   📦 {len(results)} results from Google")

    inserted = 0
    skipped = 0

    for place in results:
        place_id = place.get("place_id")

        # Bỏ qua nếu đã tồn tại
        if bronze.find_one({"google_place_id": place_id}, {"_id": 1}):
            skipped += 1
            continue

        # Get full details
        details = get_place_details(place_id)

        u_key = hashlib.md5(f"google_{place_id}".encode()).hexdigest()[:16]

        doc = {
            "u_key": u_key,
            "poi_id": f"google_{place_id}",

            # === RAW DATA ===
            "osm_raw": None,
            "google_raw": {
                "place": place,            # Raw place từ nearby search
                "place_details": details,  # Full details
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
            "city_name": city_config["name"],
            "country": city_config.get("country", "Vietnam"),
            "category": category,
            "location": {
                "lat": place["geometry"]["location"]["lat"],
                "lon": place["geometry"]["location"]["lng"]
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

        # Insert ngay từng POI
        try:
            bronze.insert_one(doc)
            inserted += 1
            print(f"   ✅ [{inserted}] {place.get('name', '?')}")
        except Exception as ie:
            if "quota" in str(ie).lower() or "space" in str(ie).lower():
                print(f"   ❌ MongoDB quota exceeded! Stopping.")
                client.close()
                return
            skipped += 1

        time.sleep(0.5)

    print(f"   💾 Saved {inserted}, skipped {skipped}")
    client.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "only":
        # Collect Google-only POIs cho tất cả cities
        categories = ["restaurant", "hotel", "attraction"]
        for city_code, city_cfg in CITIES.items():
            for cat in categories:
                collect_google_only(city_code, city_cfg, category=cat, limit=20)
    else:
        # Enrich OSM POIs đã có với Google data
        # Có thể truyền city filter: python enrich_google_raw.py hanoi
        city_filter = sys.argv[1] if len(sys.argv) > 1 else None
        enrich_google_raw(limit=200, city=city_filter)
