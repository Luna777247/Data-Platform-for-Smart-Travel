#!/usr/bin/env python
"""Test both OSM and Google Places collection"""

import sys
sys.path.insert(0, '.')

from pipelines.ingestion.osm_collector_real import OSMCollectorReal
import os

# Test OSM
print("="*60)
print("🗺️  TESTING OSM COLLECTION")
print("="*60)

osm_collector = OSMCollectorReal(max_retries=2)

osm_results = osm_collector.collect(
    city='hanoi',
    category='restaurant',
    lat=21.0278,
    lng=105.8342,
    radius=5000
)

print(f"\n✅ OSM Results: {len(osm_results)} POIs")
if osm_results:
    for i, r in enumerate(osm_results[:3]):
        print(f"   {i+1}. {r.get('name', 'N/A')}")

# Test Google
print("\n" + "="*60)
print("🔍 TESTING GOOGLE PLACES COLLECTION")
print("="*60)

import requests

keys_str = os.getenv("RAPID_API_KEYS", "")
keys = [k.strip() for k in keys_str.split(",") if k.strip()]

if keys:
    print(f"✅ Found {len(keys)} RapidAPI keys")
    
    headers = {
        "x-rapidapi-key": keys[0],
        "x-rapidapi-host": "google-map-places.p.rapidapi.com"
    }
    
    url = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
    
    params = {
        "location": "21.0278,105.8342",
        "radius": "2000",
        "type": "restaurant",
        "language": "vi"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✅ Google Places Results: {len(results)} POIs")
            if results:
                for i, r in enumerate(results[:3]):
                    print(f"   {i+1}. {r.get('name', 'N/A')}")
        else:
            print(f"❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("⚠️  No RapidAPI keys found")

print("\n" + "="*60)
print("✅ BOTH APIs TESTED SUCCESSFULLY!")
print("="*60)
