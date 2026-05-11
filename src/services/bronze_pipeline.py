"""
Bronze Pipeline Service
=======================
Thu thập và lưu raw data vào MongoDB (duy nhất)
"""
import asyncio
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.db.client import get_database
from src.core.logging import get_logger
from src.collectors.google_enricher import GooglePlacesEnricher

logger = get_logger(__name__)


class BronzePipeline:
    """
    Pipeline cho Bronze layer:
    - Collect từ Google Places API
    - Lưu raw JSON vào MongoDB (duy nhất)
    - Collection: bronze_records
    """
    
    def __init__(self):
        self.db = get_database()
        self.collector = GooglePlacesEnricher()
        self.collection_name = "bronze_records"
    
    async def collect_city_category(
        self,
        city: str,
        lat: float,
        lng: float,
        category: str,
        radius: int = 2000,
        max_results: int = 60
    ) -> Dict[str, Any]:
        """
        Thu thập POIs cho 1 city + category
        Lưu raw response vào MongoDB (duy nhất)
        
        Returns:
            {"saved": int, "poi_ids": List[str], "errors": List[str]}
        """
        logger.info(f"Collecting {category} in {city}...")
        
        try:
            # Collect from API
            places = await self.collector.search_nearby(
                lat=lat,
                lng=lng,
                radius=radius,
                place_type=category,
                max_results=max_results
            )
            
            saved_ids = []
            errors = []
            
            for place in places:
                try:
                    # Build bronze record
                    bronze_record = {
                        "u_key": self._generate_key(city, place.get('place_id', '')),
                        "original_osm_name": place.get('name', ''),
                        "city": city,
                        "category": category,
                        "google_raw": place,
                        "harvested_at": datetime.now().isoformat(),
                        "search_params": {
                            "lat": lat,
                            "lng": lng,
                            "radius": radius,
                            "type": category
                        },
                        "_source": "google",
                        "_layer": "bronze"
                    }
                    
                    # Save to MongoDB (duy nhất)
                    result = await self.db[self.collection_name].insert_one(bronze_record)
                    saved_ids.append(str(result.inserted_id))
                    
                except Exception as e:
                    errors.append(f"Error saving place: {e}")
                    continue
            
            result = {
                "saved": len(saved_ids),
                "poi_ids": saved_ids,
                "errors": errors,
                "city": city,
                "category": category
            }
            
            logger.info(f"Saved {result['saved']} bronze records to MongoDB for {city}/{category}")
            return result
            
        except Exception as e:
            logger.error(f"Collection failed for {city}/{category}: {e}")
            return {"saved": 0, "poi_ids": [], "errors": [str(e)]}
    
    async def run_mass_collection(
        self,
        cities: List[Dict[str, Any]],
        categories: List[str],
        grid_points: int = 9
    ) -> Dict[str, Any]:
        """
        Mass collection cho nhiều cities và categories
        
        Args:
            cities: List of {"name": str, "lat": float, "lng": float}
            categories: List of category strings
            grid_points: Số điểm thu thập mỗi city
        
        Returns:
            Collection summary
        """
        total_saved = 0
        results_by_city = {}
        
        for city_data in cities:
            city_name = city_data["name"]
            lat = city_data["lat"]
            lng = city_data["lng"]
            
            logger.info(f"=== Processing city: {city_name} ===")
            
            # Create grid points
            grid = self._create_grid(lat, lng, radius_km=10, points=grid_points)
            
            city_results = []
            
            for category in categories:
                for point in grid:
                    result = await self.collect_city_category(
                        city=city_name,
                        lat=point["lat"],
                        lng=point["lng"],
                        category=category,
                        radius=2000,
                        max_results=20
                    )
                    
                    city_results.append(result)
                    total_saved += result["saved"]
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
            
            results_by_city[city_name] = {
                "total_saved": sum(r["saved"] for r in city_results),
                "details": city_results
            }
        
        return {
            "total_bronze_saved": total_saved,
            "by_city": results_by_city,
            "cities_processed": len(cities),
            "categories": categories
        }
    
    def _generate_key(self, city: str, place_id: str) -> str:
        """Generate unique key như trong storage"""
        key_string = f"{city}_{place_id}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _create_grid(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float = 10,
        points: int = 9
    ) -> List[Dict[str, float]]:
        """Create grid of collection points"""
        # ~0.018 degrees = 2km
        step = 0.018 * (radius_km / 2)
        
        grid = []
        side = int(points ** 0.5)  # sqrt for square grid
        
        for i in range(-side//2, side//2 + 1):
            for j in range(-side//2, side//2 + 1):
                lat = center_lat + (i * step)
                lng = center_lng + (j * step)
                grid.append({"lat": lat, "lng": lng, "i": i, "j": j})
        
        return grid[:points]
    
    async def get_bronze_stats(self) -> Dict[str, Any]:
        """Lấy thống kê bronze layer từ MongoDB"""
        try:
            total = await self.db[self.collection_name].count_documents({})
            by_city = await self.db[self.collection_name].aggregate([
                {"$group": {"_id": "$city", "count": {"$sum": 1}}}
            ]).to_list(100)
            by_category = await self.db[self.collection_name].aggregate([
                {"$group": {"_id": "$category", "count": {"$sum": 1}}}
            ]).to_list(100)
            
            return {
                "total": total,
                "by_city": {item["_id"]: item["count"] for item in by_city},
                "by_category": {item["_id"]: item["count"] for item in by_category}
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total": 0, "by_city": {}, "by_category": {}}
    
    async def list_bronze_records(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Liệt kê bronze records từ MongoDB"""
        query = {"_layer": "bronze"}
        if city:
            query["city"] = city
        if category:
            query["category"] = category
        
        cursor = self.db[self.collection_name].find(query).limit(limit)
        return await cursor.to_list(length=limit)
