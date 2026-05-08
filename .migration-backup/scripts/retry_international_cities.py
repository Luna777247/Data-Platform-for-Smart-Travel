"""
Enhanced Retry Script for Failed International Cities
Implements exponential backoff and slower rate limiting for resilient data collection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import logging
import random
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RetryInternationalCities")

class ErrorType(Enum):
    """Classification of errors for intelligent backoff"""
    RATE_LIMIT = "429"      # Too Many Requests - needs long backoff
    SERVER_ERROR = "504"     # Gateway Timeout - needs long backoff
    BAD_REQUEST = "400"      # Bad Request - may be unsolvable
    CONNECTION = "timeout"   # Connection timeout
    NETWORK = "network"      # Network error
    UNKNOWN = "unknown"

# Failed cities to retry
FAILED_CITIES = {
    "bali": {"lat": -8.3405, "lon": 115.0920, "country": "Indonesia", "radius_km": 15},
    "kualalumpur": {"lat": 3.1390, "lon": 101.6869, "country": "Malaysia", "radius_km": 12},
    "penang": {"lat": 5.4164, "lon": 100.3327, "country": "Malaysia", "radius_km": 10},
    "siemreap": {"lat": 13.3671, "lon": 103.8448, "country": "Cambodia", "radius_km": 10},
    "kathmandu": {"lat": 27.7172, "lon": 85.3240, "country": "Nepal", "radius_km": 10},
    "taipei": {"lat": 25.0330, "lon": 121.5654, "country": "Taiwan", "radius_km": 12},
    "agra": {"lat": 27.1767, "lon": 78.0081, "country": "India", "radius_km": 8},
}

# POI Categories - retry all 7 categories
CATEGORIES = {
    "attraction": 'node["tourism"="attraction"]',
    "restaurant": 'node["amenity"="restaurant"]',
    "hotel": 'node["tourism"="hotel"]',
    "cafe": 'node["amenity"="cafe"]',
    "museum": 'node["tourism"="museum"]',
    "viewpoint": 'node["tourism"="viewpoint"]',
    "park": 'node["leisure"="park"]',
}

class ExponentialBackoff:
    """Exponential backoff with error-type aware delays"""
    
    def __init__(self, base_delay: float = 5.0, max_delay: float = 60.0, multiplier: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.current_delay = base_delay
        self.retry_count = 0
    
    def get_error_type(self, status_code: Optional[int], error_msg: str) -> ErrorType:
        """Classify error type for intelligent backoff"""
        if status_code == 429:
            return ErrorType.RATE_LIMIT
        elif status_code == 504:
            return ErrorType.SERVER_ERROR
        elif status_code == 400:
            return ErrorType.BAD_REQUEST
        elif "timeout" in error_msg.lower():
            return ErrorType.CONNECTION
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            return ErrorType.NETWORK
        return ErrorType.UNKNOWN
    
    def calculate_backoff(self, error_type: ErrorType) -> float:
        """Calculate backoff time based on error type"""
        # Rate limit and server errors get longer backoff
        if error_type in [ErrorType.RATE_LIMIT, ErrorType.SERVER_ERROR]:
            delay = min(self.current_delay * self.multiplier, self.max_delay)
            self.current_delay = delay
        # Connection/network errors get moderate backoff
        elif error_type in [ErrorType.CONNECTION, ErrorType.NETWORK]:
            delay = min(self.current_delay * 1.5, self.max_delay)
        # Bad requests don't retry, return 0
        else:
            delay = 0
        
        self.retry_count += 1
        return delay
    
    def reset(self):
        """Reset backoff state after successful request"""
        self.current_delay = self.base_delay
        self.retry_count = 0


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


async def fetch_osm_data_with_backoff(
    city: str,
    lat: float,
    lon: float,
    radius_km: int,
    category: str,
    category_query: str,
    max_retries: int = 3,
    overpass_url: str = "https://lz4.overpass-api.de/api/interpreter"
) -> tuple[List[Dict[str, Any]], bool]:
    """
    Fetch POI data with exponential backoff and intelligent retry logic
    Returns: (data, success)
    """
    
    backoff = ExponentialBackoff(base_delay=5.0, max_delay=60.0, multiplier=2.0)
    query = create_osm_query(lat, lon, radius_km, category_query)
    
    for attempt in range(max_retries + 1):
        try:
            headers = {
                'User-Agent': 'Smart-Travel-Retry/1.0 (Enhanced Data Collector)',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            # Slower rate limiting: 5-15 seconds between requests
            rate_limit_delay = random.uniform(5.0, 15.0)
            
            logger.info(f"🔄 [{attempt+1}/{max_retries+1}] {city} | {category}: Waiting {rate_limit_delay:.1f}s before request...")
            await asyncio.sleep(rate_limit_delay)
            
            logger.info(f"🔄 [{attempt+1}/{max_retries+1}] Fetching {category} from {city} (Retry {attempt})...")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    overpass_url,
                    data={'data': query},
                    headers=headers,
                    follow_redirects=True
                )
                
                # Handle different status codes
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get('elements', [])
                    logger.info(f"✅ {city} | {category}: Found {len(elements)} POIs (Attempt {attempt+1})")
                    backoff.reset()
                    return elements[:100], True
                
                elif response.status_code in [429, 504]:
                    error_type = backoff.get_error_type(response.status_code, "")
                    backoff_delay = backoff.calculate_backoff(error_type)
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"⚠️  {city} | {category}: HTTP {response.status_code} - "
                            f"Backing off {backoff_delay:.1f}s (Attempt {attempt+1}/{max_retries+1})"
                        )
                        await asyncio.sleep(backoff_delay)
                    else:
                        logger.error(f"❌ {city} | {category}: HTTP {response.status_code} - Max retries exceeded")
                        return [], False
                
                elif response.status_code == 400:
                    logger.error(f"❌ {city} | {category}: HTTP 400 Bad Request - Query may be invalid")
                    return [], False
                
                else:
                    logger.error(f"❌ {city} | {category}: HTTP {response.status_code}")
                    if attempt < max_retries:
                        await asyncio.sleep(backoff.calculate_backoff(ErrorType.UNKNOWN))
                    else:
                        return [], False
        
        except httpx.TimeoutException as e:
            error_type = ErrorType.CONNECTION
            backoff_delay = backoff.calculate_backoff(error_type)
            
            if attempt < max_retries:
                logger.warning(
                    f"⚠️  {city} | {category}: Timeout - "
                    f"Backing off {backoff_delay:.1f}s (Attempt {attempt+1}/{max_retries+1})"
                )
                await asyncio.sleep(backoff_delay)
            else:
                logger.error(f"❌ {city} | {category}: Connection timeout - Max retries exceeded")
                return [], False
        
        except httpx.NetworkError as e:
            error_type = ErrorType.NETWORK
            backoff_delay = backoff.calculate_backoff(error_type)
            
            if attempt < max_retries:
                logger.warning(
                    f"⚠️  {city} | {category}: Network error - "
                    f"Backing off {backoff_delay:.1f}s (Attempt {attempt+1}/{max_retries+1})"
                )
                await asyncio.sleep(backoff_delay)
            else:
                logger.error(f"❌ {city} | {category}: Network error - Max retries exceeded")
                return [], False
        
        except Exception as e:
            logger.error(f"❌ {city} | {category}: Unexpected error: {e}")
            if attempt < max_retries:
                await asyncio.sleep(backoff.calculate_backoff(ErrorType.UNKNOWN))
            else:
                return [], False
    
    return [], False


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


async def retry_failed_cities():
    """Main function to retry failed cities with exponential backoff"""
    
    logger.info("=" * 80)
    logger.info("🔄 STARTING RETRY FOR FAILED INTERNATIONAL CITIES")
    logger.info("=" * 80)
    logger.info(f"⏱️  Retry strategy: Exponential backoff (5s base, 60s max)")
    logger.info(f"📊 Rate limiting: 5-15 seconds between requests (slower)")
    logger.info(f"🔁 Max retries per category: 3")
    logger.info("=" * 80)
    
    total_collected = 0
    successful_cities = 0
    city_results = {}
    
    for city_key, city_config in FAILED_CITIES.items():
        city_name = city_config.get("country", "Unknown")
        lat = city_config["lat"]
        lon = city_config["lon"]
        radius_km = city_config["radius_km"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏙️  RETRYING: {city_key.upper()} ({city_name})")
        logger.info(f"📍 Coordinates: {lat}, {lon} | Radius: {radius_km}km")
        logger.info(f"{'='*60}")
        
        city_total = 0
        city_success = False
        category_results = {}
        
        for category, query in CATEGORIES.items():
            try:
                # Fetch data from OSM with backoff
                elements, success = await fetch_osm_data_with_backoff(
                    city_key,
                    lat,
                    lon,
                    radius_km,
                    category,
                    query,
                    max_retries=3
                )
                
                category_results[category] = {
                    "success": success,
                    "count": len(elements)
                }
                
                if elements and success:
                    # Save to local storage
                    saved = await save_osm_data(city_key, category, elements)
                    if saved:
                        city_total += len(elements)
                        city_success = True
            
            except Exception as e:
                logger.error(f"❌ Unexpected error processing {category} for {city_key}: {e}")
                category_results[category] = {"success": False, "count": 0}
                continue
        
        city_results[city_key] = {
            "success": city_success,
            "total_collected": city_total,
            "categories": category_results
        }
        
        if city_success:
            successful_cities += 1
            total_collected += city_total
            logger.info(f"✅ {city_key}: RETRY SUCCESSFUL - Collected {city_total} POIs")
        else:
            logger.warning(f"⚠️  {city_key}: RETRY FAILED - No data collected")
        
        # Long pause between cities (15-25 seconds) to be very respectful to Overpass API
        inter_city_delay = random.uniform(15.0, 25.0)
        logger.info(f"⏱️  Waiting {inter_city_delay:.1f}s before next city...")
        await asyncio.sleep(inter_city_delay)
    
    # Print detailed results
    logger.info("\n" + "=" * 80)
    logger.info("🏆 RETRY OPERATION COMPLETED")
    logger.info("=" * 80)
    logger.info(f"📊 Summary:")
    logger.info(f"   - Total Failed Cities: {len(FAILED_CITIES)}")
    logger.info(f"   - Successfully Recovered: {successful_cities}")
    logger.info(f"   - Total POIs Collected: {total_collected}")
    logger.info("\n📋 Detailed Results by City:")
    
    for city_key, result in city_results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"  {city_key:15} {status:15} POIs: {result['total_collected']}")
        
        successful_categories = sum(1 for cat in result['categories'].values() if cat['success'])
        logger.info(f"    └─ Categories: {successful_categories}/{len(CATEGORIES)} successful")
        
        for cat, cat_result in result['categories'].items():
            cat_status = "✅" if cat_result['success'] else "❌"
            logger.info(f"       {cat_status} {cat:12} ({cat_result['count']} POIs)")
    
    logger.info("=" * 80)
    
    return total_collected > 0


if __name__ == "__main__":
    try:
        result = asyncio.run(retry_failed_cities())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Retry interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
