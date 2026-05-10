"""
Collect Real OSM Data
=====================

Collect real POI data from OpenStreetMap cho Hanoi và HCM.
Lưu vào bronze_records collection.
"""

import requests
import json
import time
from datetime import datetime
from pymongo import MongoClient


def overpass_query(lat, lng, radius, amenity_type):
    """Build Overpass API query."""
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="{amenity_type}"](around:{radius},{lat},{lng});
      way["amenity"="{amenity_type}"](around:{radius},{lat},{lng});
    );
    out center body 100;
    """
    return query.strip()


def collect_osm_data():
    """Collect real OSM data for cities."""
    print("🚀 Collecting Real OSM Data...")
    print("=" * 50)
    
    # Connect to MongoDB
    mongo_uri = "mongodb://admin:admin123@localhost:27017/smart_travel?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client.smart_travel
    
    # Cities configuration
    cities = {
        "hanoi": {"lat": 21.0278, "lng": 105.8342, "radius": 10000},
        "hcm": {"lat": 10.8231, "lng": 106.6297, "radius": 10000}
    }
    
    # Amenity types to collect
    amenities = [
        "restaurant",
        "cafe",
        "hotel",
        "bar",
        "fast_food",
        "bank",
        "atm",
        "pharmacy",
        "hospital",
        "school"
    ]
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    total_collected = 0
    
    for city_name, coords in cities.items():
        print(f"\n📍 Collecting for {city_name.upper()}...")
        
        city_records = []
        
        for amenity in amenities:
            print(f"   🔍 {amenity}...", end=" ")
            
            try:
                # Build and send query
                query = overpass_query(
                    coords["lat"],
                    coords["lng"],
                    coords["radius"],
                    amenity
                )
                
                response = requests.post(
                    overpass_url,
                    data={"data": query},
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get("elements", [])
                    
                    for element in elements:
                        # Get coordinates
                        if element["type"] == "node":
                            lat = element.get("lat")
                            lon = element.get("lon")
                        else:  # way
                            center = element.get("center", {})
                            lat = center.get("lat")
                            lon = center.get("lon")
                        
                        if lat is None or lon is None:
                            continue
                        
                        tags = element.get("tags", {})
                        
                        record = {
                            "poi_id": f"osm_{element['type']}_{element['id']}",
                            "name": tags.get("name", f"Unnamed {amenity}"),
                            "name_en": tags.get("name:en"),
                            "category": amenity,
                            "city": city_name,
                            "country": "VN",
                            "location": {"lat": lat, "lng": lon},
                            "address": tags.get("addr:street", ""),
                            "phone": tags.get("phone"),
                            "website": tags.get("website"),
                            "opening_hours": tags.get("opening_hours"),
                            "osm_tags": tags,
                            "osm_id": element["id"],
                            "osm_type": element["type"],
                            "_ingestion_timestamp": datetime.utcnow().isoformat(),
                            "_city": city_name,
                            "_category": amenity,
                            "_source": "osm_real",
                            "_layer": "bronze"
                        }
                        
                        city_records.append(record)
                    
                    print(f"✅ {len(elements)}")
                else:
                    print(f"❌ HTTP {response.status_code}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:30]}")
                continue
        
        # Save to MongoDB
        if city_records:
            # Clear existing real OSM data for this city
            db.bronze_records.delete_many({
                "_city": city_name,
                "_source": "osm_real"
            })
            
            # Insert new records
            result = db.bronze_records.insert_many(city_records)
            inserted = len(result.inserted_ids)
            total_collected += inserted
            print(f"   💾 Saved {inserted} records to bronze")
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 OSM COLLECTION COMPLETE")
    print(f"   Total real OSM records: {total_collected}")
    
    # Verify
    for city in cities.keys():
        count = db.bronze_records.count_documents({
            "_city": city,
            "_source": "osm_real"
        })
        print(f"   - {city}: {count} records")
    
    client.close()
    print("\n✅ Real OSM data collection finished!")


if __name__ == "__main__":
    collect_osm_data()
