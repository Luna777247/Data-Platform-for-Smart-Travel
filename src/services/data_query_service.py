"""
Data Query Service
==================

Business logic cho data query operations.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/services/data_query_service.py

Responsibilities:
- POI data retrieval
- Data aggregation
- Search operations
- Filter và pagination
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.db.repositories.poi_repository import POIRepository

logger = logging.getLogger(__name__)


class DataQueryService:
    """
    Service cho data query operations.
    
    Provides:
    - POI data retrieval
    - Search and filtering
    - Data aggregation
    - Statistics calculation
    """
    
    def __init__(self, repository: Optional[POIRepository] = None):
        self.repository = repository or POIRepository()
        logger.info("DataQueryService initialized")
    
    async def get_pois(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get POIs với pagination."""
        try:
            # Get from silver layer
            pois = await self.repository.get_silver_data(
                city=city or "hanoi",
                limit=page_size * page
            )
            
            # Filter by category if specified
            if category:
                pois = [p for p in pois if p.get("category") == category]
            
            # Pagination
            total = len(pois)
            start = (page - 1) * page_size
            end = start + page_size
            paginated = pois[start:end]
            
            return {
                "items": paginated,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        
        except Exception as e:
            logger.error(f"Failed to get POIs: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "pages": 0}
    
    async def get_poi_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get single POI by ID."""
        return await self.repository.get_silver_poi_by_id(place_id)
    
    async def search_pois(
        self,
        query: str,
        city: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search POIs by name."""
        try:
            pois = await self.repository.get_silver_data(city=city, limit=1000)
            
            # Simple text search
            query_lower = query.lower()
            results = [
                p for p in pois
                if query_lower in p.get("name", "").lower()
                or query_lower in p.get("category", "").lower()
            ]
            
            return results[:limit]
        
        except Exception as e:
            logger.error(f"Failed to search POIs: {e}")
            return []
    
    async def get_nearby_pois(
        self,
        lat: float,
        lng: float,
        radius_km: float = 1.0,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find POIs near location."""
        try:
            return await self.repository.find_nearby(
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                category=category,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get nearby POIs: {e}")
            return []
    
    async def get_data_stats(self, city: Optional[str] = None) -> Dict[str, Any]:
        """Get data statistics."""
        try:
            pois = await self.repository.get_silver_data(city=city, limit=10000)
            
            # Calculate stats
            total = len(pois)
            
            by_category = {}
            by_city = {}
            by_source = {}
            
            for poi in pois:
                cat = poi.get("category", "unknown")
                by_category[cat] = by_category.get(cat, 0) + 1
                
                c = poi.get("_city", "unknown")
                by_city[c] = by_city.get(c, 0) + 1
                
                src = poi.get("source", "unknown")
                by_source[src] = by_source.get(src, 0) + 1
            
            return {
                "total_pois": total,
                "by_category": by_category,
                "by_city": by_city,
                "by_source": by_source,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_pois": 0,
                "by_category": {},
                "by_city": {},
                "by_source": {},
                "error": str(e)
            }
    
    async def get_layers(self) -> List[Dict[str, Any]]:
        """Get layer information."""
        return [
            {
                "name": "bronze",
                "description": "Raw data from collectors",
                "format": "json",
                "location": "MongoDB"
            },
            {
                "name": "silver",
                "description": "Cleaned and enriched data",
                "format": "json",
                "location": "MongoDB"
            },
            {
                "name": "gold",
                "description": "Aggregated business-ready data",
                "format": "json",
                "location": "MongoDB"
            }
        ]
