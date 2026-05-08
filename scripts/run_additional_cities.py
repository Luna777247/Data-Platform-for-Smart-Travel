"""
Script to collect data for 12 Additional Cities (2026 Tourism Destinations - Phase 2)
Collects POI data from OpenStreetMap for additional international cities.
Targets: Mumbai, Delhi, Phuket, Chiang Rai, Jakarta, Manila, Rome, Paris, Barcelona, London, Dubai
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
import httpx
import random
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AdditionalCitiesCollector")

# Additional cities configuration (Phase 2)
ADDITIONAL_CITIES = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "country": "India", "radius_km": 12},
    "delhi": {"lat": 28.7041, "lon": 77.1025, "country": "India", "radius_km": 15},
    "phuket": {"lat": 7.8804, "lon": 98.3923, "country": "Thailand", "radius_km": 12},
    "chiangrai": {"lat": 19.9101, "lon": 99.8803, "country": "Thailand", "radius_km": 10},
    "jakarta": {"lat": -6.2088, "lon": 106.8456, "country": "Indonesia", "radius_km": 12},
    "manila": {"lat": 14.5995, "lon": 120.9842, "country": "Philippines", "radius_km": 12},
    "rome": {"lat": 41.9028, "lon": 12.4964, "country": "Italy", "radius_km": 12},
    "paris": {"lat": 48.8566, "lon": 2.3522, "country": "France", "radius_km": 12},
    "barcelona": {"lat": 41.3851, "lon": 2.1734, "country": "Spain", "radius_km": 12},
    "london": {"lat": 51.5074, "lon": -0.1278, "country": "England", "radius_km": 12},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "country": "UAE", "radius_km": 12},
    "taipei": {"lat": 25.0330, "lon": 121.5654, "country": "Taiwan", "radius_km": 12},
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

def create_osm_query(lat: float, lon: float, radius_km: int, category_query: str) -> str:
    """Create Overpass API query using bbox around coordinates"""
    lat_offset = (radius_km / 111.0)
    lon_offset = (radius_km / (111.0 * 0.8))
    
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
    """Fetch POI data from OpenStreetMap"""
    
    query = create_osm_query(lat, lon, radius_km, category_query)
    
    try:
        headers = {
            'User-Agent': 'Smart-Travel-Data-Platform/1.0 (Phase2-Collector)',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"🔄 Fetching {category} from {city}...")
            response = await client.post(
                overpass_url,
                data=query,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                logger.info(f"✅ {city} | {category}: Found {len(elements)} POIs")
                return elements
            else:
                logger.error(f"❌ {city} | {category}: HTTP {response.status_code}")
                return []
                
    except httpx.TimeoutException:
        logger.error(f"❌ {city} | {category}: Request timeout (60s)")
        return []
    except Exception as e:
        logger.error(f"❌ {city} | {category}: {str(e)}")
        return []

def save_osm_data(
    city: str,
    category: str,
    elements: List[Dict],
    timestamp: str
) -> int:
    """Save OSM data to storage/bronze/osm/{city}/{category}_{timestamp}.json"""
    
    if not elements:
        return 0
    
    # Create directory if needed
    city_dir = Path(f"storage/bronze/osm/{city}")
    city_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare data structure
    data = {
        "city": city,
        "category": category,
        "timestamp": timestamp,
        "count": len(elements),
        "elements": elements[:100]  # Limit to first 100 per file
    }
    
    # Save file
    filename = city_dir / f"{category}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 Saved {len(elements[:100])} records to {filename}")
    return len(elements)

async def collect_additional_cities_data():
    """Main function to collect data for all additional cities"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    total_collected = 0
    city_results = {}
    
    logger.info("="*80)
    logger.info("🚀 STARTING COLLECTION: 12 ADDITIONAL CITIES")
    logger.info("="*80)
    
    for city, coords in ADDITIONAL_CITIES.items():
        city_results[city] = {"total": 0, "categories": {}}
        logger.info(f"\n{'='*80}")
        logger.info(f"🏙️  COLLECTING: {city.upper()} ({coords['country']})")
        logger.info(f"📍 Coordinates: {coords['lat']}, {coords['lon']} | Radius: {coords['radius_km']}km")
        logger.info(f"{'='*80}")
        
        for category, query in CATEGORIES.items():
            # Random delay between requests (5-10 seconds)
            delay = random.uniform(5, 10)
            logger.info(f"⏱️  Waiting {delay:.1f}s before request...")
            await asyncio.sleep(delay)
            
            # Fetch data
            elements = await fetch_osm_data(
                city=city,
                lat=coords['lat'],
                lon=coords['lon'],
                radius_km=coords['radius_km'],
                category=category,
                category_query=query
            )
            
            # Save data
            count = save_osm_data(city, category, elements, timestamp)
            city_results[city]["categories"][category] = count
            city_results[city]["total"] += count
            total_collected += count
        
        # Delay between cities (10-15 seconds)
        if city != list(ADDITIONAL_CITIES.keys())[-1]:
            delay = random.uniform(10, 15)
            logger.info(f"⏱️  Waiting {delay:.1f}s before next city...")
            await asyncio.sleep(delay)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("🏆 COLLECTION COMPLETED")
    logger.info("="*80)
    logger.info(f"📊 Summary:")
    logger.info(f"    - Total Cities: {len(ADDITIONAL_CITIES)}")
    logger.info(f"    - Total POIs Collected: {total_collected}")
    logger.info(f"\n📋 Detailed Results by City:")
    
    for city in sorted(ADDITIONAL_CITIES.keys()):
        result = city_results[city]
        logger.info(f"  {city.ljust(20)} | {str(result['total']).rjust(5)} POIs")
        for cat, count in result['categories'].items():
            status = "✅" if count > 0 else "❌"
            logger.info(f"      {status} {cat.ljust(15)} ({count} POIs)")
    
    logger.info("="*80)
    
    # Save results to log file
    log_data = {
        "timestamp": timestamp,
        "total_pois": total_collected,
        "total_cities": len(ADDITIONAL_CITIES),
        "cities": city_results
    }
    
    log_file = Path("collection_log_phase2.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📝 Saved collection log to {log_file}")
    
    return total_collected

if __name__ == "__main__":
    total = asyncio.run(collect_additional_cities_data())
    logger.info(f"\n✨ Phase 2 Collection Complete: {total} POIs collected!")
    sys.exit(0)
