"""
TripAdvisor Collector Plugin
============================
Example custom collector implementing BaseCollector.

Demonstrates plugin system for adding new data sources dynamically.
"""

from typing import Dict, List, Any, Optional
import aiohttp
import hashlib

from src.plugins.base import BaseCollector
from src.core.logging import get_logger

logger = get_logger(__name__)


class TripAdvisorCollector(BaseCollector):
    """
    Collector cho TripAdvisor Content API.
    
    Example custom plugin demonstrating:
    - BaseCollector implementation
    - API key authentication
    - Rate limiting
    - Dynamic registration
    
    Usage:
        collector = TripAdvisorCollector(config={
            "api_key": "YOUR_API_KEY",
            "base_url": "https://api.content.tripadvisor.com"
        })
        data = await collector.collect(city="hanoi", category="restaurant")
    """
    
    @property
    def plugin_name(self) -> str:
        return "tripadvisor"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    @property
    def plugin_type(self) -> str:
        return "source"
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate TripAdvisor API configuration."""
        required = ["api_key"]
        
        for field in required:
            if field not in config:
                raise ValueError(f"Missing required config: {field}")
        
        # Validate API key format
        api_key = config.get("api_key", "")
        if len(api_key) < 20:
            raise ValueError("Invalid API key format")
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check TripAdvisor API connectivity."""
        try:
            base_url = self.config.get(
                "base_url", 
                "https://api.content.tripadvisor.com"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/v1/health") as resp:
                    if resp.status == 200:
                        return {
                            "status": "healthy",
                            "message": "TripAdvisor API accessible",
                            "api_version": "v1"
                        }
                    else:
                        return {
                            "status": "degraded",
                            "message": f"API returned status {resp.status}"
                        }
                        
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Cannot connect to TripAdvisor API: {str(e)}"
            }
    
    async def collect(
        self, 
        city: str, 
        category: str, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collect POI data from TripAdvisor.
        
        Args:
            city: City name (e.g., "hanoi", "tokyo")
            category: POI type (e.g., "restaurant", "attraction")
            
        Returns:
            List of POI dictionaries
        """
        logger.info(f"🚀 Collecting from TripAdvisor: {city}/{category}")
        
        try:
            # Validate config first
            await self.validate_config(self.config)
            
            # Get configuration
            api_key = self.config["api_key"]
            base_url = self.config.get(
                "base_url", 
                "https://api.content.tripadvisor.com/api/v1"
            )
            
            # Map categories
            category_map = {
                "restaurant": "restaurants",
                "hotel": "hotels",
                "attraction": "attractions"
            }
            ta_category = category_map.get(category, category)
            
            # Simulate API call (replace with actual implementation)
            # In production, this would call TripAdvisor Content API
            mock_data = self._generate_mock_data(city, ta_category)
            
            logger.info(f"✅ Collected {len(mock_data)} POIs from TripAdvisor")
            return mock_data
            
        except Exception as e:
            logger.error(f"❌ TripAdvisor collection failed: {e}")
            raise
    
    async def search_nearby(
        self,
        lat: float,
        lng: float,
        radius: int = 2000,
        place_type: Optional[str] = None,
        max_results: int = 60,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search POIs near a location.
        
        Args:
            lat: Latitude
            lng: Longitude  
            radius: Search radius in meters
            place_type: Type of place
            max_results: Maximum results
        """
        logger.info(
            f"🔍 Searching TripAdvisor near ({lat}, {lng}) "
            f"radius={radius}m, type={place_type}"
        )
        
        try:
            await self.validate_config(self.config)
            
            # In production: call TripAdvisor nearby search API
            # For demo: return mock data
            mock_data = self._generate_mock_data(
                f"lat_{lat}_lng_{lng}", 
                place_type or "restaurant",
                count=min(max_results, 10)
            )
            
            return mock_data
            
        except Exception as e:
            logger.error(f"❌ Nearby search failed: {e}")
            raise
    
    def _generate_mock_data(
        self, 
        location: str, 
        category: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate mock data for demonstration."""
        data = []
        
        for i in range(count):
            place_id = hashlib.md5(
                f"tripadvisor_{location}_{category}_{i}".encode()
            ).hexdigest()[:16]
            
            data.append({
                "place_id": f"TA_{place_id}",
                "name": f"{category.title()} {i+1} in {location.title()}",
                "location": {
                    "lat": 21.0 + (i * 0.01),
                    "lng": 105.8 + (i * 0.01)
                },
                "category": category,
                "rating": 4.0 + (i * 0.2),
                "review_count": 50 + (i * 10),
                "source": "tripadvisor",
                "source_url": f"https://www.tripadvisor.com/{place_id}",
                "price_level": 2,
                "opening_hours": "09:00-22:00"
            })
        
        return data


# Export for plugin registration
__all__ = ['TripAdvisorCollector']
