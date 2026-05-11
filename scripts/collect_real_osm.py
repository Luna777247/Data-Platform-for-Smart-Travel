"""
Collect Real OSM Data
=====================

Collect real POI data from OpenStreetMap.
Lưu raw data đầy đủ vào bronze_records, sau đó transform sang silver và gold.
"""

import os
import requests
import json
import time
import math
import hashlib
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load env for MongoDB URI
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# =========================================================
# CONFIG
# =========================================================

# Multiple Overpass API endpoints for failover
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",      # Main instance (Germany)
    "https://overpass.kumi.systems/api/interpreter", # Alternative (Finland)
    "https://overpass.openstreetmap.ru/api/interpreter", # Russia mirror
    "https://overpass.openstreetmap.fr/api/interpreter", # French instance
]

# =========================================================
# CITY CONFIG - Vietnam Cities
# =========================================================

CITIES = {
    # Tier 1: Major cities (High density)
    "hanoi": {"name": "Thành phố Hà Nội", "lat": 21.0278, "lon": 105.8342, "radius_km": 30, "country": "Vietnam"},
    "hochiminh": {"name": "Thành phố Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297, "radius_km": 30, "country": "Vietnam"},
    "danang": {"name": "Thành phố Đà Nẵng", "lat": 16.0544, "lon": 108.2022, "radius_km": 25, "country": "Vietnam"},
    
    # Tier 2: Large cities
    "haiphong": {"name": "Thành phố Hải Phòng", "lat": 20.8449, "lon": 106.6881, "radius_km": 22, "country": "Vietnam"},
    "cantho": {"name": "Thành phố Cần Thơ", "lat": 10.0452, "lon": 105.7469, "radius_km": 20, "country": "Vietnam"},
    "nhatrang": {"name": "Thành phố Nha Trang", "lat": 12.2388, "lon": 109.1967, "radius_km": 18, "country": "Vietnam"},
    "dalat": {"name": "Thành phố Đà Lạt", "lat": 11.9404, "lon": 108.4583, "radius_km": 15, "country": "Vietnam"},
    "vungtau": {"name": "Thành phố Vũng Tàu", "lat": 10.3460, "lon": 107.0843, "radius_km": 15, "country": "Vietnam"},
    "hue": {"name": "Thành phố Huế", "lat": 16.4637, "lon": 107.5909, "radius_km": 18, "country": "Vietnam"},
    
    # Tier 3: Provincial cities (Northern)
    "thainguyen": {"name": "Thái Nguyên", "lat": 21.5942, "lon": 105.8482, "radius_km": 15, "country": "Vietnam"},
    "vinh": {"name": "Vinh", "lat": 18.6796, "lon": 105.6813, "radius_km": 15, "country": "Vietnam"},
    "thanhhoa": {"name": "Thanh Hóa", "lat": 19.8067, "lon": 105.7852, "radius_km": 15, "country": "Vietnam"},
    "haiduong": {"name": "Hải Dương", "lat": 20.9386, "lon": 106.3207, "radius_km": 12, "country": "Vietnam"},
    "bacninh": {"name": "Bắc Ninh", "lat": 21.1861, "lon": 106.0763, "radius_km": 12, "country": "Vietnam"},
    "quangninh": {"name": "Hạ Long", "lat": 20.9508, "lon": 107.0732, "radius_km": 18, "country": "Vietnam"},
    "langson": {"name": "Lạng Sơn", "lat": 21.8535, "lon": 106.7616, "radius_km": 12, "country": "Vietnam"},
    "caobang": {"name": "Cao Bằng", "lat": 22.6652, "lon": 106.2570, "radius_km": 10, "country": "Vietnam"},
    
    # Tier 4: Provincial cities (Central)
    "quangnam": {"name": "Hội An", "lat": 15.8801, "lon": 108.3380, "radius_km": 12, "country": "Vietnam"},
    "quangngai": {"name": "Quảng Ngãi", "lat": 15.1205, "lon": 108.7923, "radius_km": 15, "country": "Vietnam"},
    "binhdinh": {"name": "Quy Nhơn", "lat": 13.7820, "lon": 109.2198, "radius_km": 15, "country": "Vietnam"},
    "phuyen": {"name": "Tuy Hòa", "lat": 13.0908, "lon": 109.3009, "radius_km": 12, "country": "Vietnam"},
    "khanhhoa": {"name": "Cam Ranh", "lat": 11.9214, "lon": 109.1591, "radius_km": 12, "country": "Vietnam"},
    "binhthuan": {"name": "Phan Thiết", "lat": 10.9805, "lon": 108.2615, "radius_km": 15, "country": "Vietnam"},
    "lamdong": {"name": "Bảo Lộc", "lat": 11.5478, "lon": 107.8016, "radius_km": 10, "country": "Vietnam"},
    "gialai": {"name": "Pleiku", "lat": 13.7712, "lon": 108.2278, "radius_km": 12, "country": "Vietnam"},
    "daklak": {"name": "Buôn Ma Thuột", "lat": 12.6666, "lon": 108.0389, "radius_km": 12, "country": "Vietnam"},
    "kontum": {"name": "Kon Tum", "lat": 14.3492, "lon": 108.0009, "radius_km": 10, "country": "Vietnam"},
    
    # Tier 5: Provincial cities (Southern)
    "longan": {"name": "Tân An", "lat": 10.5363, "lon": 106.4043, "radius_km": 10, "country": "Vietnam"},
    "tiengiang": {"name": "Mỹ Tho", "lat": 10.3600, "lon": 106.3600, "radius_km": 12, "country": "Vietnam"},
    "bentre": {"name": "Bến Tre", "lat": 10.2433, "lon": 106.3756, "radius_km": 10, "country": "Vietnam"},
    "travinh": {"name": "Trà Vinh", "lat": 9.9369, "lon": 106.3452, "radius_km": 10, "country": "Vietnam"},
    "vinhlong": {"name": "Vĩnh Long", "lat": 10.2537, "lon": 105.9722, "radius_km": 10, "country": "Vietnam"},
    "dongthap": {"name": "Cao Lãnh", "lat": 10.4603, "lon": 105.6321, "radius_km": 10, "country": "Vietnam"},
    "angiang": {"name": "Long Xuyên", "lat": 10.3863, "lon": 105.4351, "radius_km": 12, "country": "Vietnam"},
    "kiengiang": {"name": "Rạch Giá", "lat": 10.0125, "lon": 105.0809, "radius_km": 12, "country": "Vietnam"},
    "camau": {"name": "Cà Mau", "lat": 9.1768, "lon": 105.1524, "radius_km": 12, "country": "Vietnam"},
    "soctrang": {"name": "Sóc Trăng", "lat": 9.6025, "lon": 105.9739, "radius_km": 10, "country": "Vietnam"},
    "baclieu": {"name": "Bạc Liêu", "lat": 9.2941, "lon": 105.7216, "radius_km": 10, "country": "Vietnam"},
    
    # Tier 6: Industrial zones & suburbs
    "dongnai": {"name": "Biên Hòa", "lat": 10.9574, "lon": 106.8426, "radius_km": 15, "country": "Vietnam"},
    "binhduong": {"name": "Thủ Dầu Một", "lat": 11.0067, "lon": 106.6537, "radius_km": 15, "country": "Vietnam"},
    "tayninh": {"name": "Tây Ninh", "lat": 11.3082, "lon": 106.0979, "radius_km": 12, "country": "Vietnam"},
    "binhphuoc": {"name": "Đồng Xoài", "lat": 11.5347, "lon": 106.8832, "radius_km": 10, "country": "Vietnam"},
    "ninhthuan": {"name": "Phan Rang", "lat": 11.5643, "lon": 108.9886, "radius_km": 12, "country": "Vietnam"},
}

# =========================================================
# CATEGORY CONFIG - Expanded for 20K POIs
# =========================================================

CATEGORIES = {
    # Food & Drink
    "restaurant": {
        "osm_tags": [
            ('amenity', 'restaurant'),
            ('amenity', 'fast_food'),
            ('amenity', 'food_court')
        ],
        "radius_km": 20
    },
    "cafe": {
        "osm_tags": [
            ('amenity', 'cafe'),
            ('amenity', 'coffee_shop')
        ],
        "radius_km": 15
    },
    "bar": {
        "osm_tags": [
            ('amenity', 'bar'),
            ('amenity', 'pub')
        ],
        "radius_km": 15
    },
    
    # Accommodation
    "hotel": {
        "osm_tags": [
            ('tourism', 'hotel'),
            ('tourism', 'guest_house'),
            ('tourism', 'hostel'),
            ('tourism', 'motel')
        ],
        "radius_km": 25
    },
    
    # Shopping
    "shop": {
        "osm_tags": [
            ('shop', 'supermarket'),
            ('shop', 'convenience'),
            ('shop', 'mall')
        ],
        "radius_km": 20
    },
    "shop_general": {
        "osm_tags": [
            ('shop', 'general'),
            ('shop', 'department_store'),
            ('shop', 'wholesale')
        ],
        "radius_km": 18
    },
    "shop_food": {
        "osm_tags": [
            ('shop', 'bakery'),
            ('shop', 'butcher'),
            ('shop', 'greengrocer'),
            ('shop', 'seafood')
        ],
        "radius_km": 15
    },
    "shop_health": {
        "osm_tags": [
            ('shop', 'pharmacy'),
            ('shop', 'chemist'),
            ('shop', 'hairdresser'),
            ('shop', 'beauty')
        ],
        "radius_km": 15
    },
    
    # Attractions & Leisure
    "attraction": {
        "osm_tags": [
            ('tourism', 'attraction'),
            ('tourism', 'museum'),
            ('tourism', 'viewpoint'),
            ('tourism', 'zoo')
        ],
        "radius_km": 30
    },
    "park": {
        "osm_tags": [
            ('leisure', 'park'),
            ('leisure', 'garden'),
            ('leisure', 'nature_reserve')
        ],
        "radius_km": 25
    },
    "sports": {
        "osm_tags": [
            ('leisure', 'sports_centre'),
            ('leisure', 'fitness_centre'),
            ('leisure', 'swimming_pool'),
            ('leisure', 'stadium')
        ],
        "radius_km": 20
    },
    "beach": {
        "osm_tags": [
            ('natural', 'beach'),
            ('leisure', 'beach_resort')
        ],
        "radius_km": 25
    },
    
    # Services
    "bank": {
        "osm_tags": [
            ('amenity', 'bank'),
            ('amenity', 'atm')
        ],
        "radius_km": 20
    },
    "healthcare": {
        "osm_tags": [
            ('amenity', 'hospital'),
            ('amenity', 'clinic'),
            ('amenity', 'pharmacy'),
            ('amenity', 'doctors')
        ],
        "radius_km": 20
    },
    "fuel": {
        "osm_tags": [
            ('amenity', 'fuel'),
            ('amenity', 'charging_station')
        ],
        "radius_km": 20
    },
    "post": {
        "osm_tags": [
            ('amenity', 'post_office'),
            ('amenity', 'post_box')
        ],
        "radius_km": 18
    },
    "entertainment": {
        "osm_tags": [
            ('amenity', 'cinema'),
            ('amenity', 'theatre'),
            ('amenity', 'nightclub'),
            ('amenity', 'karaoke_box')
        ],
        "radius_km": 20
    },
    "education": {
        "osm_tags": [
            ('amenity', 'school'),
            ('amenity', 'university'),
            ('amenity', 'college'),
            ('amenity', 'kindergarten')
        ],
        "radius_km": 20
    },
    "place_of_worship": {
        "osm_tags": [
            ('amenity', 'place_of_worship')
        ],
        "radius_km": 20
    }
}

# =========================================================
# QUERY BUILDER
# =========================================================

def create_overpass_query(lat, lon, radius_m, tags):
    """Create Overpass API query for multiple tags."""
    query_parts = []
    
    for key, value in tags:
        if value == "*":
            query_parts.extend([
                f'node["{key}"](around:{radius_m},{lat},{lon});',
                f'way["{key}"](around:{radius_m},{lat},{lon});',
                f'relation["{key}"](around:{radius_m},{lat},{lon});'
            ])
        else:
            query_parts.extend([
                f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});',
                f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});',
                f'relation["{key}"="{value}"](around:{radius_m},{lat},{lon});'
            ])
    
    query_body = "\n        ".join(query_parts)
    
    return f"""
[out:json][timeout:180];
(
    {query_body}
);
out body center tags meta;
"""


def generate_grid_points(lat, lon, radius_km, grid_size=3):
    """Generate grid points for better coverage."""
    # Approximate: 1 degree = 111km
    lat_offset = radius_km / 111.0
    lon_offset = radius_km / (111.0 * abs(math.cos(math.radians(lat))))
    
    points = []
    for i in range(grid_size):
        for j in range(grid_size):
            lat_point = lat - lat_offset + (2 * lat_offset * i / (grid_size - 1))
            lon_point = lon - lon_offset + (2 * lon_offset * j / (grid_size - 1))
            points.append({"lat": lat_point, "lon": lon_point})
    
    return points


def safe_get_location(item):
    """Extract lat/lon from node or way/relation center."""
    lat = item.get("lat")
    lon = item.get("lon")
    
    if lat and lon:
        return lat, lon
    
    center = item.get("center", {})
    return center.get("lat"), center.get("lon")


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    R = 6371
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def try_overpass_query(query, headers, timeout=300, max_retries=3):
    """Try query on multiple Overpass endpoints with fallback."""
    import random
    
    # Shuffle endpoints to distribute load
    endpoints = OVERPASS_ENDPOINTS.copy()
    random.shuffle(endpoints)
    
    last_error = None
    
    for endpoint in endpoints:
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    endpoint,
                    params={"data": query},
                    headers=headers,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = (attempt + 1) * 5 + random.uniform(0, 2)
                    print(f"   ⏳ Rate limited on {endpoint.split('/')[2]}, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.ConnectionError as e:
                last_error = e
                wait_time = (attempt + 1) * 2 + random.uniform(0, 1)
                print(f"   ⚠️ Connection error to {endpoint.split('/')[2]}: {str(e)[:50]}...")
                time.sleep(wait_time)
                continue
            except requests.exceptions.Timeout as e:
                last_error = e
                wait_time = (attempt + 1) * 3
                print(f"   ⏱️ Timeout on {endpoint.split('/')[2]}, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            except Exception as e:
                last_error = e
                print(f"   ❌ Error on {endpoint.split('/')[2]}: {str(e)[:50]}")
                break  # Try next endpoint
    
    # All endpoints failed
    raise last_error if last_error else Exception("All Overpass endpoints failed")


def collect_osm_data():
    """Collect real OSM data for cities with enhanced coverage.
    Lưu raw data đầy đủ vào bronze_records collection.
    """
    print("🚀 Collecting Real OSM Data (Enhanced with Raw Data)")
    print("=" * 70)
    
    # Connect to MongoDB Atlas
    mongo_uri = os.getenv("MONGODB_URI", "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0")
    client = MongoClient(mongo_uri)
    db = client.smart_travel_platform
    
    print("✅ Connected to MongoDB Atlas")
    
    GRID_SIZE = 3  # 3x3 grid per city (9 points) - for 20K POIs target
    total_collected = 0
    
    headers = {
        'User-Agent': 'SmartTravel-Collector/1.0 (Data Platform)',
        'Accept': 'application/json'
    }
    
    for city_code, city_config in CITIES.items():
        print(f"\n📍 {city_config['name'].upper()}")
        
        lat = city_config["lat"]
        lon = city_config["lon"]
        city_radius_km = city_config["radius_km"]
        
        # Generate grid points
        grid_points = generate_grid_points(lat, lon, city_radius_km, GRID_SIZE)
        grid_radius_km = city_radius_km / GRID_SIZE * 1.5
        grid_radius_m = int(grid_radius_km * 1000)
        
        print(f"   Grid: {len(grid_points)} points, radius: {grid_radius_km:.1f}km")
        
        city_records = []
        seen_ids = set()
        
        for point_idx, point in enumerate(grid_points):
            point_lat = point["lat"]
            point_lon = point["lon"]
            
            for category, cat_config in CATEGORIES.items():
                try:
                    # Create query with all tags for this category
                    query = create_overpass_query(
                        lat=point_lat,
                        lon=point_lon,
                        radius_m=grid_radius_m,
                        tags=cat_config["osm_tags"]
                    )
                    
                    # API Call with multi-endpoint fallback
                    try:
                        response = try_overpass_query(query, headers, timeout=180)
                        data = response.json()
                    except Exception as e:
                        print(f"   ⚠️ {category} error: {str(e)[:60]}...")
                        continue
                    elements = data.get("elements", [])
                    
                    if elements:
                        print(f"   📦 {category}: {len(elements)} raw elements")
                    
                    # Process each element
                    for element in elements:
                        osm_id = element.get("id")
                        osm_type = element.get("type")
                        
                        # Skip if already seen
                        unique_key = f"{city_code}_{osm_type}_{osm_id}"
                        if unique_key in seen_ids:
                            continue
                        seen_ids.add(unique_key)
                        
                        # Get location
                        item_lat, item_lon = safe_get_location(element)
                        if not item_lat or not item_lon:
                            continue
                        
                        # Calculate distance from city center
                        distance_km = haversine(lat, lon, item_lat, item_lon)
                        
                        # Get tags
                        tags = element.get("tags", {})
                        name = tags.get("name") or tags.get("name:en") or tags.get("official_name")
                        if not name:
                            continue
                        
                        # Generate u_key
                        u_key = hashlib.md5(unique_key.encode()).hexdigest()[:16]
                        
                        # Build Bronze record with RAW DATA
                        record = {
                            # IDs
                            "u_key": u_key,
                            "poi_id": f"osm_{osm_type}_{osm_id}",
                            
                            # Basic info
                            "name": name,
                            "city": city_code,
                            "city_name": city_config["name"],
                            "country": city_config["country"],
                            "category": category,
                            
                            # Location
                            "location": {
                                "lat": item_lat,
                                "lon": item_lon
                            },
                            "distance_km": round(distance_km, 2),
                            
                            # OSM specific
                            "osm_id": osm_id,
                            "osm_type": osm_type,
                            "osm_tags": tags,
                            
                            # Address & contact
                            "address": tags.get("addr:street") or tags.get("addr:full"),
                            "phone": tags.get("phone"),
                            "website": tags.get("website"),
                            "opening_hours": tags.get("opening_hours"),
                            
                            # Metadata
                            "metadata": {
                                "version": element.get("version"),
                                "timestamp": element.get("timestamp"),
                                "changeset": element.get("changeset"),
                                "user": element.get("user"),
                                "uid": element.get("uid")
                            },
                            
                            # RAW DATA - Lưu toàn bộ
                            "raw_osm_element": element,
                            "raw_query": query,
                            "raw_response_meta": {
                                "grid_point": point_idx + 1,
                                "total_grid_points": len(grid_points),
                                "category": category,
                                "api_call_timestamp": datetime.now(timezone.utc).isoformat()
                            },
                            
                            # Layer info
                            "_source": "osm_real",
                            "_layer": "bronze",
                            "harvested_at": datetime.now(timezone.utc).isoformat(),
                            "ingestion_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        city_records.append(record)
                    
                    # Rate limiting - wait between calls
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"   ⚠️ {category} error: {str(e)[:60]}")
                    continue
            
            # Progress update
            if point_idx % 3 == 0 or point_idx == len(grid_points) - 1:
                print(f"   📍 Grid {point_idx+1}/{len(grid_points)}: {len(city_records)} POIs so far")
        
        # Save city records to MongoDB
        if city_records:
            batch_size = 500
            for i in range(0, len(city_records), batch_size):
                batch = city_records[i:i+batch_size]
                try:
                    db.bronze_records.insert_many(batch, ordered=False)
                except Exception as e:
                    print(f"   ⚠️ Insert error: {e}")
            
            total_collected += len(city_records)
            print(f"   💾 Saved {len(city_records)} records to bronze")
            
            # Show sample
            if city_records:
                sample = city_records[0]
                print(f"   📌 Sample: {sample['name']} ({sample['category']})")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📈 OSM COLLECTION COMPLETE")
    print("=" * 70)
    print(f"   Total collected: {total_collected:,} POIs")
    
    # Verify by city
    print("\n   By city:")
    for city_code in CITIES.keys():
        count = db.bronze_records.count_documents({
            "city": city_code,
            "_source": "osm_real"
        })
        print(f"      {city_code}: {count:,}")
    
    # Total in database
    total_db = db.bronze_records.count_documents({"_source": "osm_real"})
    print(f"\n   Total in database: {total_db:,} POIs")
    
    # Check raw data presence
    sample = db.bronze_records.find_one({"_source": "osm_real"})
    if sample:
        has_raw = "raw_osm_element" in sample
        print(f"   Raw data preserved: {has_raw}")
    
    client.close()
    print("\n✅ Real OSM data collection finished!")


if __name__ == "__main__":
    collect_osm_data()
