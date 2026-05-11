"""
Collect Real OSM Data → bronze_pois
=====================================
Thu thập OSM POI data cho các thành phố, lưu vào bronze_pois với osm_raw schema.
Insert từng POI ngay lập tức, resume-safe (bỏ qua nếu u_key đã tồn tại).
Multi-endpoint Overpass fallback + quota guard.
"""

import os
import sys
import hashlib
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from pymongo import MongoClient


MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

CITIES = {
    "hanoi":  {"name": "Hà Nội",      "lat": 21.0278, "lon": 105.8342, "radius_m": 8000, "country": "Vietnam"},
    "hcm":    {"name": "Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "radius_m": 8000, "country": "Vietnam"},
    "danang": {"name": "Đà Nẵng",     "lat": 16.0544, "lon": 108.2022, "radius_m": 6000, "country": "Vietnam"},
}

CATEGORIES = {
    "restaurant": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "cafe":       [("amenity", "cafe")],
    "hotel":      [("tourism", "hotel"), ("tourism", "guest_house"), ("tourism", "hostel")],
    "attraction": [("tourism", "attraction"), ("tourism", "museum"), ("tourism", "viewpoint")],
    "bar":        [("amenity", "bar"), ("amenity", "pub")],
    "pharmacy":   [("amenity", "pharmacy")],
}


def _create_overpass_query(lat, lon, radius_m, tags):
    parts = []
    for key, value in tags:
        parts += [
            f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});',
            f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});',
        ]
    body = "\n  ".join(parts)
    return f"[out:json][timeout:180];\n(\n  {body}\n);\nout body center tags meta;"


def _try_overpass_query(query, timeout=180):
    import random
    headers = {"User-Agent": "SmartTravel-RealCollector/1.0", "Accept": "application/json"}
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


def _safe_location(element):
    lat = element.get("lat")
    lon = element.get("lon")
    if lat and lon:
        return lat, lon
    c = element.get("center", {})
    return c.get("lat"), c.get("lon")


def collect_real_data():
    """Thu thập OSM data → bronze_pois, resume-safe."""
    print("🚀 Collecting Real OSM Data → bronze_pois")
    print("=" * 60)

    client = MongoClient(MONGODB_URI)
    bronze = client.smart_travel_platform.bronze_pois
    print("✅ Connected to MongoDB Atlas")

    total_inserted = 0
    total_skipped = 0

    for city_code, city_cfg in CITIES.items():
        lat, lon = city_cfg["lat"], city_cfg["lon"]
        radius_m = city_cfg["radius_m"]
        print(f"\n📍 {city_cfg['name'].upper()} (radius {radius_m}m)")

        city_inserted = city_skipped = 0
        seen = set()

        for category, tags in CATEGORIES.items():
            print(f"   🔍 {category}...", end=" ", flush=True)
            try:
                query = _create_overpass_query(lat, lon, radius_m, tags)
                resp = _try_overpass_query(query)
                elements = resp.json().get("elements", [])
                cat_inserted = 0

                for element in elements:
                    osm_id = element.get("id")
                    osm_type = element.get("type")
                    session_key = f"{city_code}_{osm_type}_{osm_id}"

                    if session_key in seen:
                        city_skipped += 1
                        continue
                    seen.add(session_key)

                    u_key = hashlib.md5(session_key.encode()).hexdigest()[:16]
                    if bronze.find_one({"u_key": u_key}, {"_id": 1}):
                        city_skipped += 1
                        continue

                    item_lat, item_lon = _safe_location(element)
                    if not item_lat or not item_lon:
                        continue

                    tags_data = element.get("tags", {})
                    name = tags_data.get("name") or tags_data.get("name:en") or tags_data.get("official_name")
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
                        "_source": "collect_real_data"
                    }

                    try:
                        bronze.insert_one(doc)
                        cat_inserted += 1
                        city_inserted += 1
                    except Exception as ie:
                        err = str(ie)
                        if "quota" in err.lower() or "space" in err.lower():
                            print(f"\n❌ MongoDB quota exceeded! Stopping.")
                            client.close()
                            return
                        city_skipped += 1

                print(f"✅ +{cat_inserted}")
                time.sleep(1.5)

            except Exception as e:
                print(f"❌ {str(e)[:50]}")
                continue

        total_inserted += city_inserted
        total_skipped += city_skipped
        print(f"   💾 {city_cfg['name']}: inserted={city_inserted}, skipped={city_skipped}")

    print("\n" + "=" * 60)
    print("📈 COLLECTION COMPLETE")
    print(f"   Inserted this run : {total_inserted:,}")
    print(f"   Skipped (exists)  : {total_skipped:,}")

    for city_code in CITIES:
        count = bronze.count_documents({"city": city_code, "has_osm_data": True})
        print(f"   - {city_code}: {count:,} in bronze_pois")

    client.close()
    print("\n✅ Done! Next: python enrich_google_raw.py")


if __name__ == "__main__":
    collect_real_data()
