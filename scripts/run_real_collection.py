"""
Run Real Collection → bronze_pois
====================================
Thu thập dữ liệu thật từ:
  1. OSM (Overpass API) → osm_raw schema
  2. Google Places (RapidAPI) → google_raw schema
Lưu vào MongoDB bronze_pois, insert từng POI, resume-safe.
Multi-endpoint Overpass fallback + RapidAPI quota guard.
"""

import os
import sys
import json
import time
import hashlib
import random
import requests
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient


# ==========================================
# CONFIG
# ==========================================

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/details/json"

_KEYS_FILE = Path(__file__).parent.parent / "storage" / "configs" / "rapidapi_keys.json"
try:
    with open(_KEYS_FILE, "r") as _f:
        _RAPIDAPI_KEYS = json.load(_f)
except Exception:
    _RAPIDAPI_KEYS = []

_key_index = 0

CITIES = {
    "hanoi":  {"name": "Hà Nội",      "lat": 21.0278, "lon": 105.8342, "radius_m": 5000, "country": "Vietnam"},
    "hcm":    {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "radius_m": 5000, "country": "Vietnam"},
    "danang": {"name": "Đà Nẵng",     "lat": 16.0544, "lon": 108.2022, "radius_m": 4000, "country": "Vietnam"},
}

OSM_CATEGORIES = {
    "restaurant": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "cafe":       [("amenity", "cafe")],
    "hotel":      [("tourism", "hotel"), ("tourism", "guest_house"), ("tourism", "hostel")],
    "attraction": [("tourism", "attraction"), ("tourism", "museum"), ("tourism", "viewpoint")],
    "bar":        [("amenity", "bar"), ("amenity", "pub")],
}

GOOGLE_CATEGORIES = ["restaurant", "cafe", "lodging", "tourist_attraction", "bar"]


# ==========================================
# HELPERS
# ==========================================

def _get_next_key():
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError(f"No RapidAPI keys found in {_KEYS_FILE}")
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


def _try_overpass(query, timeout=180):
    headers = {"User-Agent": "SmartTravel-RealCollection/1.0", "Accept": "application/json"}
    endpoints = OVERPASS_ENDPOINTS.copy()
    random.shuffle(endpoints)
    for endpoint in endpoints:
        try:
            resp = requests.get(endpoint, params={"data": query}, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
        except Exception:
            continue
    raise Exception("All Overpass endpoints failed")


def _overpass_query(lat, lon, radius_m, tags):
    parts = []
    for key, value in tags:
        parts += [
            f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});',
            f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});',
        ]
    body = "\n  ".join(parts)
    return f"[out:json][timeout:180];\n(\n  {body}\n);\nout body center tags meta;"


def _safe_loc(element):
    lat = element.get("lat")
    lon = element.get("lon")
    if lat and lon:
        return lat, lon
    c = element.get("center", {})
    return c.get("lat"), c.get("lon")


# ==========================================
# COLLECTORS
# ==========================================

def collect_osm_city(bronze, city_code, city_cfg):
    """Thu thập OSM data cho 1 city → bronze_pois. Return (inserted, skipped)."""
    lat, lon = city_cfg["lat"], city_cfg["lon"]
    radius_m = city_cfg["radius_m"]
    inserted = skipped = 0
    seen = set()

    for category, tags in OSM_CATEGORIES.items():
        print(f"   [OSM] {category}...", end=" ", flush=True)
        try:
            query = _overpass_query(lat, lon, radius_m, tags)
            resp = _try_overpass(query)
            elements = resp.json().get("elements", [])
            cat_count = 0

            for element in elements:
                osm_id = element.get("id")
                osm_type = element.get("type")
                key = f"{city_code}_{osm_type}_{osm_id}"
                if key in seen:
                    skipped += 1
                    continue
                seen.add(key)

                u_key = hashlib.md5(key.encode()).hexdigest()[:16]
                if bronze.find_one({"u_key": u_key}, {"_id": 1}):
                    skipped += 1
                    continue

                item_lat, item_lon = _safe_loc(element)
                if not item_lat or not item_lon:
                    continue

                tags_data = element.get("tags", {})
                name = (tags_data.get("name") or tags_data.get("name:en")
                        or tags_data.get("official_name"))
                if not name:
                    continue

                doc = {
                    "u_key": u_key,
                    "poi_id": f"osm_{osm_type}_{osm_id}",
                    "osm_raw": {
                        "element": element,
                        "endpoint": "overpass",
                        "fetched_at": datetime.now(timezone.utc).isoformat()
                    },
                    "google_raw": None,
                    "has_osm_data": True,
                    "has_google_data": False,
                    "data_sources": ["osm"],
                    "name": name,
                    "city": city_code,
                    "city_name": city_cfg["name"],
                    "country": city_cfg.get("country", "Vietnam"),
                    "category": category,
                    "location": {"lat": item_lat, "lon": item_lon},
                    "osm_id": osm_id,
                    "osm_type": osm_type,
                    "google_place_id": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "_layer": "bronze",
                    "_source": "run_real_collection"
                }

                try:
                    bronze.insert_one(doc)
                    cat_count += 1
                    inserted += 1
                except Exception as ie:
                    err = str(ie)
                    if "quota" in err.lower() or "space" in err.lower():
                        print(f"\n❌ MongoDB quota exceeded!")
                        return inserted, skipped, True
                    skipped += 1

            print(f"✅ +{cat_count}")
            time.sleep(1.5)

        except Exception as e:
            print(f"❌ {str(e)[:50]}")

    return inserted, skipped, False


def collect_google_city(bronze, city_code, city_cfg):
    """Thu thập Google Places data cho 1 city → bronze_pois. Return (inserted, skipped, quota_stopped)."""
    if not _RAPIDAPI_KEYS:
        print(f"   ⚠️  No RapidAPI keys – skipping Google")
        return 0, 0, False

    lat, lon = city_cfg["lat"], city_cfg["lon"]
    radius_m = city_cfg["radius_m"]
    inserted = skipped = 0

    for category in GOOGLE_CATEGORIES:
        print(f"   [Google] {category}...", end=" ", flush=True)

        data = _call_rapidapi(_NEARBY_SEARCH_URL, {
            "location": f"{lat},{lon}",
            "radius": radius_m,
            "type": category,
            "language": "vi"
        })

        status = data.get("status")
        if status == "QUOTA_EXCEEDED_ALL_KEYS":
            print(f"\n❌ All {len(_RAPIDAPI_KEYS)} RapidAPI keys exceeded quota. Stopping Google collection.")
            return inserted, skipped, True

        places = data.get("results", [])
        cat_count = 0

        for place in places:
            place_id = place.get("place_id")
            if not place_id:
                continue

            if bronze.find_one({"google_place_id": place_id}, {"_id": 1}):
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
                "city_name": city_cfg["name"],
                "country": city_cfg.get("country", "Vietnam"),
                "category": category,
                "location": {"lat": geo.get("lat"), "lon": geo.get("lng")},
                "osm_id": None,
                "osm_type": None,
                "google_place_id": place_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "_layer": "bronze",
                "_source": "run_real_collection"
            }

            try:
                bronze.insert_one(doc)
                cat_count += 1
                inserted += 1
            except Exception as ie:
                err = str(ie)
                if "quota" in err.lower() or "space" in err.lower():
                    print(f"\n❌ MongoDB quota exceeded!")
                    return inserted, skipped, True
                skipped += 1

            time.sleep(0.5)

        print(f"✅ +{cat_count}")
        time.sleep(1)

    return inserted, skipped, False


# ==========================================
# MAIN
# ==========================================

def main():
    print("=" * 60)
    print("🚀 REAL DATA COLLECTION → bronze_pois (OSM + Google)")
    print("=" * 60)
    print(f"🔑 RapidAPI keys: {len(_RAPIDAPI_KEYS)}")
    print(f"🏙️  Cities: {', '.join(CITIES.keys())}")

    client = MongoClient(MONGODB_URI)
    bronze = client.smart_travel_platform.bronze_pois
    print("✅ Connected to MongoDB Atlas\n")

    total_osm_ins = total_google_ins = 0

    for city_code, city_cfg in CITIES.items():
        print(f"\n{'='*60}")
        print(f"📍 {city_cfg['name'].upper()}")
        print(f"{'='*60}")

        # --- OSM ---
        osm_ins, osm_skp, mongo_stopped = collect_osm_city(bronze, city_code, city_cfg)
        total_osm_ins += osm_ins
        print(f"   OSM: inserted={osm_ins}, skipped={osm_skp}")
        if mongo_stopped:
            break

        # --- Google ---
        g_ins, g_skp, quota_stopped = collect_google_city(bronze, city_code, city_cfg)
        total_google_ins += g_ins
        print(f"   Google: inserted={g_ins}, skipped={g_skp}")
        if quota_stopped:
            print("   ⚠️  Google collection stopped (quota). OSM continues tomorrow.")
            break

    print("\n" + "=" * 60)
    print("📊 COLLECTION COMPLETE")
    print("=" * 60)
    print(f"   OSM inserted    : {total_osm_ins:,}")
    print(f"   Google inserted : {total_google_ins:,}")

    total = bronze.count_documents({})
    osm_c = bronze.count_documents({"has_osm_data": True})
    google_c = bronze.count_documents({"has_google_data": True})
    both_c = bronze.count_documents({"has_osm_data": True, "has_google_data": True})
    print(f"\n   bronze_pois total : {total:,}")
    print(f"   OSM only          : {osm_c - both_c:,}")
    print(f"   Google only       : {google_c - both_c:,}")
    print(f"   Both sources      : {both_c:,}")

    client.close()
    print("\n✅ Done! Next: python enrich_google_raw.py")


if __name__ == "__main__":
    main()
