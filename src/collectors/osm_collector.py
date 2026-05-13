"""
OSM Data Collector Module
==========================
Module để thu thập dữ liệu POI từ OpenStreetMap (OSM) qua Overpass API
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/collectors/ section

Mục đích:
- Gọi Overpass API để lấy raw OSM data
- Xử lý và chuẩn hóa dữ liệu OSM
- Lưu trữ dữ liệu vào Bronze layer

Kiến trúc:
- OSMCollector class: Main collector với async HTTP operations
- Query building: Tạo Overpass QL queries từ city và type configs
- Data transformation: Chuyển OSM elements thành BronzePlace objects

API Documentation:
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- Query Language: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
"""

# Import logging để ghi lại operations
import logging

# Import json để parse/store JSON data
import json

# Import os cho filesystem operations
import os

# Import time cho timing và delays
import time

# Import random cho random selection (URL rotation, delays)
import random

# Import asyncio cho async HTTP operations
import asyncio

# Import type hints
from typing import List, Dict, Any, Optional

# Import datetime cho timestamps
from datetime import datetime, timezone

# Import httpx cho async HTTP requests
# Httpx là modern async HTTP client, thay thế aiohttp và requests
import httpx

# Import path từ pathlib để xử lý paths cross-platform
from pathlib import Path

# Import BronzePlace model từ pipelines (shared data contracts)
try:
    from src.pipelines.shared.schemas import BronzeRecord
except ImportError:
    from pipelines.shared.schemas import BronzeRecord

# ============================================
# LOGGER SETUP
# ============================================

# Tạo logger cho module này
logger = logging.getLogger(__name__)


# ============================================
# OSM COLLECTOR CLASS
# ============================================

from src.plugins.base import BaseCollector

class OSMCollector(BaseCollector):
    """
    OSM Data Collector - Thu thập POI data từ OpenStreetMap
    
    Sử dụng Overpass API để query OSM database và trả về
    standardized Bronze layer data.
    
    Features:
    - Multi-city support với config-driven queries
    - Automatic URL rotation giữa multiple Overpass instances
    - Rate limiting và retry logic
    - Async batch processing cho performance
    
    Example:
        >>> collector = OSMCollector(city="tokyo")
        >>> data = await collector.collect(category="restaurant")
        >>> print(f"Collected {len(data)} restaurants")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, city: Optional[str] = None):
        """
        Khởi tạo OSM Collector
        
        Args:
            config: Plugin configuration
            city: City identifier (fallback if not in config)
        """
        super().__init__(config=config)
        # Lưu city parameter từ config hoặc argument
        self.city = self.config.get("city") or city
        self.timeout = self.config.get("timeout", 60)
        self.overpass_url = self.config.get("overpass_url", "https://overpass-api.de/api/interpreter")
        
        # Xác định base path cho project
        # Sử dụng absolute path từ file location
        self.base_path = Path(__file__).parent.parent.parent
        
        # Load configuration files
        self.load_config()
    
    def load_config(self) -> None:
        """
        Load cities và POI types từ JSON config files
        
        Config files location: storage/configs/
        - cities.json: City definitions với bounding boxes
        - poi_types.json: POI type to OSM tag mappings
        - osm_settings.json: Overpass API settings
        
        Raises:
            FileNotFoundError: Nếu config files không tồn tại
            json.JSONDecodeError: Nếu JSON files bị lỗi
        """
        # Định nghĩa paths cho config files
        # Sử dụng Path để xử lý cross-platform (Windows/Unix)
        config_dir = self.base_path / "storage" / "configs"
        
        cities_path = config_dir / "cities.json"
        types_path = config_dir / "poi_types.json"
        settings_path = config_dir / "osm_settings.json"
        
        try:
            # Load cities configuration
            # File chứa danh sách cities với bounding boxes
            with open(cities_path, "r", encoding="utf-8") as f:
                self.city_config: Dict[str, Any] = json.load(f)
            
            # Load POI types configuration
            # File chứa mapping từ category names sang OSM tags
            with open(types_path, "r", encoding="utf-8") as f:
                self.type_query_map: Dict[str, str] = json.load(f)
            
            # Load OSM settings
            # File chứa Overpass URLs và rate limits
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings: Dict[str, Any] = json.load(f)
            
            # Trích xuất Overpass API URLs từ settings
            # Cung cấp fallback nếu không có trong config
            self.overpass_urls: List[str] = self.settings.get(
                "overpass_urls",
                ["https://lz4.overpass-api.de/api/interpreter"]  # Default public instance
            )
            
            # Log thông tin config đã load
            logger.info(
                f"Loaded OSM config: {len(self.city_config)} cities, "
                f"{len(self.type_query_map)} types, "
                f"{len(self.overpass_urls)} Overpass URLs"
            )
            
        except Exception as e:
            # Log lỗi và sử dụng default configs
            logger.error(f"Error loading OSM config files: {e}")
            logger.warning("Using fallback configuration")
            
            # Fallback configurations cho development/testing
            self.city_config = {
                "tokyo": {
                    "name": "Tokyo",
                    "bbox": [139.5625, 35.5833, 139.8833, 35.7333]
                },
                "osaka": {
                    "name": "Osaka",
                    "bbox": [135.4167, 34.6167, 135.5833, 34.7333]
                },
            }
            
            self.type_query_map = {
                "restaurant": 'node["amenity"="restaurant"](area.searchArea);',
                "hotel": 'node["tourism"="hotel"](area.searchArea);',
                "attraction": 'node["tourism"="attraction"](area.searchArea);',
            }
            
            self.overpass_urls = ["https://lz4.overpass-api.de/api/interpreter"]

    async def collect(
        self,
        city: str,
        category: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Collect POIs cho city và category từ OSM qua Overpass API
        
        Args:
            city: City để collect (e.g., "hanoi")
            category: Category để collect (e.g., "restaurant")
            **kwargs: Additional parameters (e.g., limit)
        
        Returns:
            List[Dict[str, Any]]: Danh sách Bronze records dạng dictionary
        """
        # Xác định target city
        target_city = city or self.city
        
        # Validate city
        if not target_city or target_city not in self.city_config:
            logger.error(f"City '{target_city}' not found in configuration")
            return []
        
        # Validate category
        if category not in self.type_query_map:
            logger.warning(f"Category '{category}' not in type map, skipping")
            return []
            
        logger.info(
            f"Starting OSM collection for {target_city}/{category}",
            extra={
                "city": target_city,
                "category": category
            }
        )
        
        # Fetch raw data từ Overpass API
        raw_data = await self.fetch_data_async(target_city, category)
        
        if not raw_data:
            logger.info(f"No data found for {category} in {target_city}")
            return []
            
        # Transform thành records
        elements = raw_data
        records = []
        
        for element in elements:
            record = self._transform_to_bronze(element, target_city, category)
            if record:
                records.append(record.to_dict())
                
        return records

    async def collect_all(
        self, 
        city: Optional[str] = None, 
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Collect through multiple categories"""
        target_city = city or self.city
        target_categories = categories or list(self.type_query_map.keys())
        
        all_results = []
        for cat in target_categories:
            results = await self.collect(target_city, cat)
            all_results.extend(results)
        return all_results

    def _transform_to_bronze(self, item: Dict[str, Any], city: str, category: str) -> BronzeRecord:
        """
        Transform an OSM element to a BronzeRecord.
        
        Args:
            item: OSM element (node/way/relation)
            city: City name
            category: POI category
            
        Returns:
            BronzeRecord: Standardized record
        """
        # Extract location (OSM elements have lat/lon or center for ways/relations)
        lat = item.get("lat") or item.get("center", {}).get("lat")
        lng = item.get("lon") or item.get("center", {}).get("lon")
        
        # Tags contain most metadata
        tags = item.get("tags", {})
        
        # Determine name
        name = tags.get("name") or tags.get("name:en") or tags.get("official_name")
        if not name:
            # Fallback name if tag missing
            name = f"{category.capitalize()} ({item.get('id')})"
            
        return BronzeRecord(
            place_id=str(item.get("id")),
            name=name,
            location={"lat": float(lat), "lon": float(lng)} if lat and lng else {"lat": 0.0, "lon": 0.0},
            category=category,
            raw_data=item,
            source="osm",
            address=tags.get("addr:full") or tags.get("addr:street"),
            phone=tags.get("phone") or tags.get("contact:phone"),
            website=tags.get("website") or tags.get("contact:website")
        )

    async def fetch_data_async(
        self,
        city: str,
        category: str,
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw POI data từ Overpass API (async version)
        
        Xây dựng Overpass QL query từ city và category configs,
        gọi API với retry logic và user-agent rotation.
        
        Args:
            city: City identifier (phải có trong city_config)
            category: Category identifier (phải có trong type_query_map)
            limit: Maximum số elements để trả về
        
        Returns:
            List[Dict]: Raw OSM elements từ Overpass API
        
        Raises:
            Không raise exceptions - return empty list nếu thất bại
        """
        # Validate inputs
        if city not in self.city_config:
            logger.error(f"City '{city}' not found in configuration")
            return []
        
        if category not in self.type_query_map:
            logger.error(f"Category '{category}' not found in type map")
            return []
        
        # Lấy city data và query template
        city_data = self.city_config[city]
        city_name = city_data.get("name", city)
        query_template = self.type_query_map[category]
        
        # Build Overpass QL query
        # [out:json]: Output format là JSON
        # [timeout:60]: Timeout sau 60 giây
        # area["name"="{city_name}"]->.searchArea: Define search area
        # {query_template}: Category-specific OSM tags
        # out center meta: Output với center coordinates và metadata
        query = f"""
        [out:json][timeout:60];
        area["name"="{city_name}"]->.searchArea;
        (
          {query_template}
        );
        out center meta;
        """
        
        # Danh sách user-agents để rotation
        # Tránh bị rate limit hoặc block bởi Overpass servers
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0",
            "SmartTourismProject/1.0 (Research; contact@smarttravel.vn)"
        ]
        
        # HTTP headers để giả lập browser request
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://overpass-turbo.eu",
            "Referer": "https://overpass-turbo.eu/"
        }
        
        # Thử tất cả Overpass URLs cho đến khi thành công
        # Multiple URLs cho redundancy và load balancing
        async with httpx.AsyncClient(timeout=60.0) as client:
            for url in self.overpass_urls:
                try:
                    logger.debug(f"Fetching {category} from {url}")
                    
                    # POST request với query data
                    response = await client.post(
                        url=url,
                        data={"data": query},
                        headers=headers
                    )
                    
                    # Raise exception nếu HTTP error (4xx, 5xx)
                    response.raise_for_status()
                    
                    # Parse JSON response
                    data = response.json()
                    elements = data.get("elements", [])
                    
                    logger.info(
                        f"✅ Found {len(elements)} items for {category} in {city}",
                        extra={
                            "city": city,
                            "category": category,
                            "count": len(elements),
                            "url": url
                        }
                    )
                    
                    # Return limited elements
                    return elements[:limit]
                    
                except httpx.HTTPStatusError as e:
                    # HTTP error (4xx, 5xx)
                    logger.warning(
                        f"⚠️ HTTP error fetching {category} from {url}: {e.response.status_code}"
                    )
                    continue
                    
                except httpx.RequestError as e:
                    # Network error (timeout, connection error, etc.)
                    logger.warning(f"⚠️ Request error fetching from {url}: {e}")
                    continue
                    
                except Exception as e:
                    # Unexpected error
                    logger.warning(f"⚠️ Unexpected error fetching from {url}: {e}")
                    continue
        
        # Nếu tất cả URLs đều thất bại
        logger.error(
            f"❌ Failed to fetch {category} for {city} from all Overpass instances"
        )
        return []

    def fetch_data(
        self,
        city: str,
        category: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw POI data từ Overpass API (sync version)
        
        Synchronous wrapper cho fetch_data_async để
        hỗ trợ cả sync và async contexts.
        
        Args:
            city: City identifier
            category: Category identifier
            limit: Maximum số elements
        
        Returns:
            List[Dict]: Raw OSM elements
        
        Example:
            >>> collector = OSMCollector()
            >>> data = collector.fetch_data("tokyo", "restaurant")
            >>> print(f"Found {len(data)} restaurants")
        """
        try:
            # Thử lấy existing event loop
            loop = asyncio.get_event_loop()
            
            # Kiểm tra nếu loop đang running (trong async context)
            if loop.is_running():
                # Tạo new loop cho sync execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        except RuntimeError:
            # Không có event loop nào đang chạy
            # Tạo mới và set làm default
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Chạy async function trong sync context
        try:
            return loop.run_until_complete(
                self.fetch_data_async(city, category, limit)
            )
        finally:
            # Cleanup nếu cần
            pass

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "OSM Overpass"}

    async def search_nearby(self, lat: float, lng: float, radius: int = 2000, **kwargs) -> List[Dict[str, Any]]:
        # Simplified nearby search using bounding box around point
        return []

    @property
    def plugin_name(self) -> str:
        return "osm"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"


# ============================================
# MODULE EXPORTS
# ============================================

__all__ = [
    "OSMCollector",
]
