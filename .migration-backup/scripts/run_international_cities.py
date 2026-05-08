"""
Script to collect data for 20 International Cities (2026 Tourism Destinations)
Collects POI data from OpenStreetMap for major Asian cities using coordinates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
import yaml
import httpx
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("InternationalCitiesCollector")

# International cities configuration
INTERNATIONAL_CITIES = {
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "country": "China", "radius_km": 15},
    "bangkok": {"lat": 13.7563, "lon": 100.5018, "country": "Thailand", "radius_km": 15},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "country": "South Korea", "radius_km": 15},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan", "radius_km": 15},
    "hongkong": {"lat": 22.3193, "lon": 114.1694, "country": "China", "radius_km": 10},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "country": "Singapore", "radius_km": 12},
    "beijing": {"lat": 39.9042, "lon": 116.4074, "country": "China", "radius_km": 15},
    "chiangmai": {"lat": 18.7883, "lon": 98.9853, "country": "Thailand", "radius_km": 12},
    "osaka": {"lat": 34.6937, "lon": 135.5023, "country": "Japan", "radius_km": 12},
    "kyoto": {"lat": 35.0116, "lon": 135.7681, "country": "Japan", "radius_km": 10},
    "bali": {"lat": -8.3405, "lon": 115.0920, "country": "Indonesia", "radius_km": 15},
    "kualalumpur": {"lat": 3.1390, "lon": 101.6869, "country": "Malaysia", "radius_km": 12},
    "penang": {"lat": 5.4164, "lon": 100.3327, "country": "Malaysia", "radius_km": 10},
    "siemreap": {"lat": 13.3671, "lon": 103.8448, "country": "Cambodia", "radius_km": 10},
    "kathmandu": {"lat": 27.7172, "lon": 85.3240, "country": "Nepal", "radius_km": 10},
    "taipei": {"lat": 25.0330, "lon": 121.5654, "country": "Taiwan", "radius_km": 12},
    "agra": {"lat": 27.1767, "lon": 78.0081, "country": "India", "radius_km": 8},
}

# POI Categories to collect
CATEGORIES = {
    "attraction": 'node["tourism"="attraction"]',
    "restaurant": 'node["amenity"="restaurant"]',
    "hotel": 'node["tourism"="hotel"]',
    "cafe": 'node["amenity"="cafe"]',
    "museum": 'node["tourism"="museum"]',
    "viewpoint": 'node["tourism"="viewpoint"]',
    "park": 'node["leisure"="park"]',
}

def convert_to_approximate_radius_meters(km: int) -> int:
    """Convert km to approximate meters for bbox calculation"""
    return km * 1000

def create_osm_query(lat: float, lon: float, radius_km: int, category_query: str) -> str:
    """Create Overpass API query using bbox around coordinates"""
    # Approximate conversion: 1 degree ≈ 111 km
    lat_offset = (radius_km / 111.0)
    lon_offset = (radius_km / (111.0 * 0.8))  # Rough adjustment for latitude effect
    
    bbox_south = lat - lat_offset
    bbox_north = lat + lat_offset
    bbox_west = lon - lon_offset
    bbox_east = lon + lon_offset
    
    query = f"""
    [out:json][timeout:30];
    (
        {category_query}(bbox:{bbox_south},{bbox_west},{bbox_north},{bbox_east});
    );
    out center meta;
    """
    return query

async def fetch_osm_data(
    city: str,
    lat: float,
    lon: float,
    radius_km: int,
    category: str,
    category_query: str,
    overpass_url: str = "https://lz4.overpass-api.de/api/interpreter"
) -> List[Dict[str, Any]]:
    """Fetch POI data from OpenStreetMap for a given city and category"""
    
    query = create_osm_query(lat, lon, radius_km, category_query)
    
    try:
        headers = {
            'User-Agent': 'Smart-Travel-Data-Platform/1.0 (Python Data Collector)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"🔄 Fetching {category} data for {city}...")
            response = await client.post(
                overpass_url,
                data={'data': query},
                headers=headers,
                follow_redirects=True
            )
            response.raise_for_status()
            data = response.json()
            
            elements = data.get('elements', [])
            logger.info(f"✅ {city} | {category}: Found {len(elements)} POIs")
            
            return elements[:100]  # Limit to 100 per category to avoid too much data
            
    except httpx.RequestError as e:
        logger.error(f"❌ Request failed for {city}-{category}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error fetching data for {city}-{category}: {e}")
        return []

async def save_osm_data(city: str, category: str, data: List[Dict[str, Any]], base_path: str = "storage/bronze/osm") -> bool:
    """Save raw OSM data to JSON files"""
    try:
        city_path = os.path.join(base_path, city)
        os.makedirs(city_path, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(city_path, f"{category}_{timestamp}.json")
        
        output = {
            "city": city,
            "category": category,
            "timestamp": timestamp,
            "count": len(data),
            "elements": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Saved {len(data)} records to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving data for {city}-{category}: {e}")
        return False

async def collect_international_cities_data():
    """Main function to collect data from all international cities"""
    
    logger.info("=" * 80)
    logger.info("🌍 STARTING INTERNATIONAL CITIES DATA COLLECTION (2026 Destinations)")
    logger.info("=" * 80)
    
    total_collected = 0
    successful_cities = 0
    
    for city_key, city_config in INTERNATIONAL_CITIES.items():
        city_name = city_config.get("country", "Unknown")
        lat = city_config["lat"]
        lon = city_config["lon"]
        radius_km = city_config["radius_km"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏙️  COLLECTING: {city_key.upper()} ({city_name})")
        logger.info(f"📍 Coordinates: {lat}, {lon} | Radius: {radius_km}km")
        logger.info(f"{'='*60}")
        
        city_total = 0
        city_success = False
        
        for category, query in CATEGORIES.items():
            try:
                # Fetch data from OSM
                elements = await fetch_osm_data(
                    city_key,
                    lat,
                    lon,
                    radius_km,
                    category,
                    query
                )
                
                if elements:
                    # Save to local storage
                    saved = await save_osm_data(city_key, category, elements)
                    if saved:
                        city_total += len(elements)
                        city_success = True
                
                # Rate limiting: wait between requests to avoid overwhelming Overpass API
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Error processing {category} for {city_key}: {e}")
                continue
        
        if city_success:
            successful_cities += 1
            total_collected += city_total
            logger.info(f"✅ {city_key}: Collected {city_total} total POIs")
        else:
            logger.warning(f"⚠️  {city_key}: No data collected")
        
        # Long pause between cities to be respectful to Overpass API
        await asyncio.sleep(5)
    
    logger.info("\n" + "=" * 80)
    logger.info("🏆 INTERNATIONAL CITIES DATA COLLECTION COMPLETED")
    logger.info("=" * 80)
    logger.info(f"📊 Summary:")
    logger.info(f"   - Total Cities: {len(INTERNATIONAL_CITIES)}")
    logger.info(f"   - Successful Cities: {successful_cities}")
    logger.info(f"   - Total POIs Collected: {total_collected}")
    logger.info("=" * 80)
    
    return total_collected > 0

if __name__ == "__main__":
    try:
        result = asyncio.run(collect_international_cities_data())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Collection interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
