"""
Google Places Collector via RapidAPI
=====================================
Collector để lấy dữ liệu POI từ Google Places API thông qua RapidAPI proxy

RapidAPI Endpoint: google-map-places.p.rapidapi.com
Cung cấp 18 API keys luân phiên để tránh rate limiting

APIs Available:
- Find Place from Text: Tìm địa điểm từ text query
- Place Details: Chi tiết địa điểm
- Nearby Search: Tìm địa điểm gần vị trí
- Text Search: Tìm kiếm text nâng cao

Documentation: https://rapidapi.com/glavier/api/google-map-places
"""

# Import typing cho type hints
from typing import Dict, Any, List, Optional, Tuple

# Import asyncio cho async operations
import asyncio

# Import aiohttp cho async HTTP requests
import aiohttp

# Import json cho JSON handling
import json

# Import random cho API key rotation
import random

# Import logging cho structured logging
import logging

# Import time cho rate limiting delays
import time

# Import dataclass cho data structures
from dataclasses import dataclass

# Import os cho environment variables
import os

# Import math cho distance calculations
import math


# =============================================================================
# CONFIGURATION
# =============================================================================

# Danh sách 18 RapidAPI keys luân phiên để tránh rate limiting
RAPID_API_KEYS = [
    "02ad4fd6f3msh1f0390da51ae627p19a5cfjsn7f2b23cadfdb",  # Key 1
    "c196374069msh778243a9fe86ab0p18f5e5jsn70ead7ba888d",  # Key 2
    "ffbaceaaeamsh9084aa32f4d5dfdp13028bjsn2366c1d9a5c9",  # Key 3
    "b10c35b812mshddb576d2951f0f9p144c5ajsn1122b8b71222",  # Key 4
    "cf1b379a98msh116f2d78aa3d55ep1a4602jsndbd91f1a8bb4",  # Key 5
    "a8e7379197msh81d17cdf3eb3011p1d33edjsn80f3ab12c760",  # Key 6
    "9036bbd933mshe2c1df67124cf82p17e447jsn62bbd79e7831",  # Key 7
    "8273c590f0msh0fbb213f4e2259ap1eb5f2jsna331f7b571a5",  # Key 8
    "45a1bd5affmsheebc75157c3c1b6p1ecba2jsnb4d9bc4281a8",  # Key 9
    "d8f35af3b3msheafde79cfa9fb8ep1a3de2jsn2bf9a5caa8ff",  # Key 10
    "43cca0d81dmshda434d1ae285f35p1ac2f0jsn723e4b3b4527",  # Key 11
    "1ed19ade15msh0f90d44564b91a4p1339ebjsnb7ba3d888c30",  # Key 12
    "9150bcabc8msh7d6269a3add664ap1b08afjsne677054f3e81",  # Key 13
    "23b064b24fmsh5c0d6b9aa7f2c45p1869f3jsnfaa274a6282e",  # Key 14
    "53ec40f187msh1642c6724cceb2ep182fc3jsn6a584f1f4b07",  # Key 15
    "6e2b78e2f3msh87c727c6c10224ep1c5c71jsn12fd50cce4d9",  # Key 16
    "634b19ccc8msh14d2a916be1dedfp147a2ejsn98f0fcbe4207",  # Key 17
    "cd339b16e5msh9d08aa5988d3f0dp16e629jsnc2db1d0323ac",  # Key 18
]

# RapidAPI host
RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"

# Base URLs cho các Google Places APIs
FIND_PLACE_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/findplacefromtext/json"
PLACE_DETAILS_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/details/json"
NEARBY_SEARCH_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
TEXT_SEARCH_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/textsearch/json"
PLACE_PHOTO_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/photo"

# Rate limiting config
MAX_REQUESTS_PER_KEY_PER_MINUTE = 100  # RapidAPI limit
REQUEST_DELAY = 0.6  # Delay giữa các requests (giây)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PlaceResult:
    """
    Data class cho kết quả tìm kiếm địa điểm.
    
    Attributes:
        place_id: Google Place ID (unique identifier)
        name: Tên địa điểm
        address: Địa chỉ đầy đủ
        lat: Latitude
        lng: Longitude
        types: Loại địa điểm (restaurant, hotel, etc.)
        rating: Điểm đánh giá (1-5)
        user_ratings_total: Số lượt đánh giá
        phone_number: Số điện thoại
        website: Website URL
        opening_hours: Giờ mở cửa
        photos: Danh sách photo references
        price_level: Mức giá (0-4)
        vicinity: Địa chỉ ngắn gọn
        permanently_closed: Đã đóng cửa vĩnh viễn
        business_status: Trạng thái kinh doanh
    """
    place_id: str
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    types: Optional[List[str]] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[Dict] = None
    photos: Optional[List[Dict]] = None
    price_level: Optional[int] = None
    vicinity: Optional[str] = None
    permanently_closed: Optional[bool] = None
    business_status: Optional[str] = None


@dataclass
class PlaceDetails:
    """
    Data class cho chi tiết địa điểm đầy đủ.
    
    Attributes:
        place_id: Google Place ID
        name: Tên địa điểm
        formatted_address: Địa chỉ đầy đủ
        formatted_phone_number: Số điện thoại định dạng
        international_phone_number: Số điện thoại quốc tế
        website: Website URL
        rating: Điểm đánh giá
        user_ratings_total: Số lượt đánh giá
        price_level: Mức giá
        opening_hours: Chi tiết giờ mở cửa
        photos: Danh sách ảnh
        reviews: Đánh giá của users
        types: Loại địa điểm
        geometry: Tọa độ
        vicinity: Khu vực
        url: Google Maps URL
        utc_offset: Múi giờ
        wheelchair_accessible_entrance: Lối vào cho xe lăn
        business_status: Trạng thái kinh doanh
        editorial_summary: Tóm tắt biên tập
    """
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    formatted_phone_number: Optional[str] = None
    international_phone_number: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    opening_hours: Optional[Dict] = None
    photos: Optional[List[Dict]] = None
    reviews: Optional[List[Dict]] = None
    types: Optional[List[str]] = None
    geometry: Optional[Dict] = None
    vicinity: Optional[str] = None
    url: Optional[str] = None
    utc_offset: Optional[int] = None
    wheelchair_accessible_entrance: Optional[bool] = None
    business_status: Optional[str] = None
    editorial_summary: Optional[str] = None


# =============================================================================
# GOOGLE PLACES COLLECTOR CLASS
# =============================================================================

from src.plugins.base import BaseCollector

class GooglePlacesCollector(BaseCollector):
    """
    Collector để lấy dữ liệu POI từ Google Places API qua RapidAPI.
    
    Features:
    - Luân phiên 18 API keys để tránh rate limiting
    - Async requests cho performance cao
    - Retry logic với exponential backoff
    - Error handling và logging chi tiết
    
    Usage:
        collector = GooglePlacesCollector()
        places = await collector.find_places("restaurants in Tokyo")
        details = await collector.get_place_details("ChIJ...")
    """
    
    def __init__(self, config: Dict[str, Any] = None, logger: Optional[logging.Logger] = None):
        """
        Khởi tạo GooglePlacesCollector.
        
        Args:
            config: Plugin configuration
            logger: Logger instance (optional)
        """
        super().__init__(config=config)
        # Khởi tạo logger
        self.logger = logger or logging.getLogger(__name__)
        
        # Session cho aiohttp (sẽ được khởi tạo khi cần)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Current API key index cho rotation
        self._current_key_index = 0
        
        # Config values
        self.api_keys = self.config.get("api_keys", RAPID_API_KEYS)
        
        # Rate limiting tracking
        self._last_request_time = 0
        self._request_count_per_key = {i: 0 for i in range(len(self.api_keys))}
        
        self.logger.info("GooglePlacesCollector initialized with %d API keys", len(self.api_keys))
    
    def _get_next_api_key(self) -> str:
        """
        Lấy API key tiếp theo theo round-robin rotation.
        
        Returns:
            str: RapidAPI key
        """
        key = RAPID_API_KEYS[self._current_key_index]
        self._current_key_index = (self._current_key_index + 1) % len(RAPID_API_KEYS)
        return key
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Tạo headers cho RapidAPI request.
        
        Returns:
            Dict[str, str]: Headers với API key
        """
        return {
            "x-rapidapi-key": self._get_next_api_key(),
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get hoặc tạo aiohttp session.
        
        Returns:
            aiohttp.ClientSession: HTTP session
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "SmartTourismPlatform/1.0"
                }
            )
        return self.session
    
    async def _make_request(
        self,
        url: str,
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Thực hiện HTTP GET request với retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            max_retries: Số lần retry tối đa
            
        Returns:
            Optional[Dict]: JSON response hoặc None nếu failed
        """
        # Rate limiting delay
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - time_since_last)
        
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                
                self.logger.debug(f"Request to {url} (attempt {attempt + 1}/{max_retries})")
                
                async with session.get(url, headers=headers, params=params) as response:
                    self._last_request_time = time.time()
                    
                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"Request successful: {url}")
                        return data
                    
                    elif response.status == 429:  # Rate limited
                        self.logger.warning(f"Rate limited on attempt {attempt + 1}, switching key...")
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    
                    elif response.status >= 500:  # Server error
                        self.logger.error(f"Server error {response.status}, retrying...")
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    
                    else:
                        error_text = await response.text()
                        self.logger.error(f"HTTP {response.status}: {error_text}")
                        return None
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on attempt {attempt + 1}")
                await asyncio.sleep(1 * (attempt + 1))
                
            except Exception as e:
                self.logger.error(f"Request error: {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))
        
        self.logger.error(f"Failed after {max_retries} attempts")
        return None
    
    async def find_place(
        self,
        input_text: str,
        input_type: str = "textquery",
        fields: str = "all",
        language: str = "en"
    ) -> Optional[PlaceResult]:
        """
        Tìm địa điểm từ text input.
        
        API: Find Place from Text
        
        Args:
            input_text: Text để tìm kiếm (ví dụ: "Museum of Contemporary Art Australia")
            input_type: Loại input (textquery hoặc phonenumber)
            fields: Fields cần lấy (comma-separated hoặc "all")
            language: Ngôn ngữ kết quả
            
        Returns:
            Optional[PlaceResult]: Thông tin địa điểm hoặc None
        """
        params = {
            "input": input_text,
            "inputtype": input_type,
            "fields": fields,
            "language": language
        }
        
        data = await self._make_request(FIND_PLACE_URL, params)
        
        if not data or data.get("status") != "OK":
            self.logger.warning(f"Find place failed: {data.get('status') if data else 'No response'}")
            return None
        
        candidates = data.get("candidates", [])
        if not candidates:
            self.logger.warning("No candidates found")
            return None
        
        # Lấy candidate đầu tiên (best match)
        candidate = candidates[0]
        
        return PlaceResult(
            place_id=candidate.get("place_id", ""),
            name=candidate.get("name", ""),
            address=candidate.get("formatted_address"),
            lat=candidate.get("geometry", {}).get("location", {}).get("lat"),
            lng=candidate.get("geometry", {}).get("location", {}).get("lng"),
            types=candidate.get("types", []),
            rating=candidate.get("rating"),
            user_ratings_total=candidate.get("user_ratings_total"),
            phone_number=candidate.get("formatted_phone_number"),
            website=candidate.get("website"),
            opening_hours=candidate.get("opening_hours"),
            photos=candidate.get("photos", []),
            price_level=candidate.get("price_level"),
            vicinity=candidate.get("vicinity"),
            business_status=candidate.get("business_status")
        )
    
    async def get_place_details(
        self,
        place_id: str,
        fields: str = "all",
        language: str = "en"
    ) -> Optional[PlaceDetails]:
        """
        Lấy chi tiết địa điểm từ Place ID.
        
        API: Place Details
        
        Args:
            place_id: Google Place ID
            fields: Fields cần lấy
            language: Ngôn ngữ kết quả
            
        Returns:
            Optional[PlaceDetails]: Chi tiết địa điểm
        """
        params = {
            "place_id": place_id,
            "fields": fields,
            "language": language
        }
        
        data = await self._make_request(PLACE_DETAILS_URL, params)
        
        if not data or data.get("status") != "OK":
            self.logger.warning(f"Place details failed: {data.get('status') if data else 'No response'}")
            return None
        
        result = data.get("result", {})
        
        return PlaceDetails(
            place_id=result.get("place_id", ""),
            name=result.get("name", ""),
            formatted_address=result.get("formatted_address"),
            formatted_phone_number=result.get("formatted_phone_number"),
            international_phone_number=result.get("international_phone_number"),
            website=result.get("website"),
            rating=result.get("rating"),
            user_ratings_total=result.get("user_ratings_total"),
            price_level=result.get("price_level"),
            opening_hours=result.get("opening_hours"),
            photos=result.get("photos", []),
            reviews=result.get("reviews", []),
            types=result.get("types", []),
            geometry=result.get("geometry"),
            vicinity=result.get("vicinity"),
            url=result.get("url"),
            utc_offset=result.get("utc_offset"),
            wheelchair_accessible_entrance=result.get("wheelchair_accessible_entrance"),
            business_status=result.get("business_status"),
            editorial_summary=result.get("editorial_summary", {}).get("overview") if result.get("editorial_summary") else None
        )
    
    async def nearby_search(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        type_filter: Optional[str] = None,
        keyword: Optional[str] = None,
        language: str = "en"
    ) -> List[PlaceResult]:
        """
        Tìm địa điểm gần vị trí.
        
        API: Nearby Search
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Bán kính tìm kiếm (mét, max 50000)
            type_filter: Loại địa điểm (restaurant, hotel, etc.)
            keyword: Từ khóa tìm kiếm
            language: Ngôn ngữ
            
        Returns:
            List[PlaceResult]: Danh sách địa điểm
        """
        location = f"{lat},{lng}"
        params = {
            "location": location,
            "radius": min(radius, 50000),  # Max 50km
            "language": language
        }
        
        if type_filter:
            params["type"] = type_filter
        if keyword:
            params["keyword"] = keyword
        
        data = await self._make_request(NEARBY_SEARCH_URL, params)
        
        if not data or data.get("status") not in ["OK", "ZERO_RESULTS"]:
            self.logger.warning(f"Nearby search failed: {data.get('status') if data else 'No response'}")
            return []
        
        results = data.get("results", [])
        places = []
        
        for result in results:
            place = PlaceResult(
                place_id=result.get("place_id", ""),
                name=result.get("name", ""),
                address=result.get("vicinity"),
                lat=result.get("geometry", {}).get("location", {}).get("lat"),
                lng=result.get("geometry", {}).get("location", {}).get("lng"),
                types=result.get("types", []),
                rating=result.get("rating"),
                user_ratings_total=result.get("user_ratings_total"),
                photos=result.get("photos", []),
                price_level=result.get("price_level"),
                vicinity=result.get("vicinity"),
                permanently_closed=result.get("permanently_closed"),
                business_status=result.get("business_status")
            )
            places.append(place)
        
        self.logger.info(f"Found {len(places)} nearby places")
        return places
    
    async def text_search(
        self,
        query: str,
        location: Optional[Tuple[float, float]] = None,
        radius: Optional[int] = None,
        type_filter: Optional[str] = None,
        language: str = "en"
    ) -> List[PlaceResult]:
        """
        Tìm kiếm địa điểm bằng text query.
        
        API: Text Search
        
        Args:
            query: Text query (ví dụ: "restaurants in Sydney")
            location: Tuple(lat, lng) - ưu tiên kết quả gần vị trí
            radius: Bán kính tìm kiếm
            type_filter: Loại địa điểm
            language: Ngôn ngữ
            
        Returns:
            List[PlaceResult]: Danh sách địa điểm
        """
        params = {
            "query": query,
            "language": language
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
        if radius:
            params["radius"] = radius
        if type_filter:
            params["type"] = type_filter
        
        data = await self._make_request(TEXT_SEARCH_URL, params)
        
        if not data or data.get("status") not in ["OK", "ZERO_RESULTS"]:
            self.logger.warning(f"Text search failed: {data.get('status') if data else 'No response'}")
            return []
        
        results = data.get("results", [])
        places = []
        
        for result in results:
            place = PlaceResult(
                place_id=result.get("place_id", ""),
                name=result.get("name", ""),
                address=result.get("formatted_address"),
                lat=result.get("geometry", {}).get("location", {}).get("lat"),
                lng=result.get("geometry", {}).get("location", {}).get("lng"),
                types=result.get("types", []),
                rating=result.get("rating"),
                user_ratings_total=result.get("user_ratings_total"),
                photos=result.get("photos", []),
                price_level=result.get("price_level"),
                vicinity=result.get("vicinity"),
                permanently_closed=result.get("permanently_closed"),
                business_status=result.get("business_status")
            )
            places.append(place)
        
        self.logger.info(f"Text search found {len(places)} places")
        return places
    
    async def collect_city_pois(
        self,
        city_name: str,
        poi_types: List[str],
        max_results_per_type: int = 50
    ) -> Dict[str, List[PlaceResult]]:
        """
        Collect POIs cho một thành phố.
        
        Args:
            city_name: Tên thành phố
            poi_types: Danh sách loại POI cần collect
            max_results_per_type: Số kết quả tối đa mỗi loại
            
        Returns:
            Dict[str, List[PlaceResult]]: POIs theo loại
        """
        self.logger.info(f"Collecting POIs for {city_name}")
        
        results = {}
        
        for poi_type in poi_types:
            query = f"{poi_type} in {city_name}"
            places = await self.text_search(
                query=query,
                type_filter=poi_type
            )
            
            # Limit results
            results[poi_type] = places[:max_results_per_type]
            
            self.logger.info(f"Found {len(results[poi_type])} {poi_type} in {city_name}")
            
            # Delay để tránh rate limiting
            await asyncio.sleep(REQUEST_DELAY)
        
        return results
    
    async def close(self):
        """
        Đóng HTTP session.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Session closed")
    
    async def __aenter__(self):
        """
        Async context manager entry.
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.close()

    async def collect(
        self, 
        city: str, 
        category: str, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Thu thập POI từ Google Places.
        
        Args:
            city: Tên thành phố
            category: Loại POI
        """
        self.logger.info(f"Collecting from Google Places: {city}/{category}")
        results_map = await self.collect_city_pois(city, [category])
        poi_list = results_map.get(category, [])
        
        return [convert_to_bronze_record(p, city) for p in poi_list]

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "Google Places via RapidAPI"}

    async def search_nearby(self, lat: float, lng: float, radius: int = 2000, **kwargs) -> List[Dict[str, Any]]:
        places = await self.nearby_search(lat, lng, radius, **kwargs)
        return [convert_to_bronze_record(p, "nearby").get("raw_data") for p in places]

    @property
    def plugin_name(self) -> str:
        return "google_places"

    @property
    def plugin_version(self) -> str:
        return "1.0.0"



# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def collect_multiple_cities(
    cities: List[str],
    poi_types: List[str],
    max_results: int = 50
) -> Dict[str, Dict[str, List[PlaceResult]]]:
    """
    Collect POIs cho nhiều thành phố.
    
    Args:
        cities: Danh sách tên thành phố
        poi_types: Danh sách loại POI
        max_results: Số kết quả tối đa mỗi loại
        
    Returns:
        Dict: Kết quả theo city và loại POI
    """
    all_results = {}
    
    async with GooglePlacesCollector() as collector:
        for city in cities:
            all_results[city] = await collector.collect_city_pois(
                city_name=city,
                poi_types=poi_types,
                max_results_per_type=max_results
            )
    
    return all_results


def convert_to_bronze_record(place: PlaceResult, city: str, source: str = "google_places") -> Dict[str, Any]:
    """
    Chuyển PlaceResult thành bronze record format.
    
    Args:
        place: PlaceResult object
        city: Tên thành phố
        source: Nguồn dữ liệu
        
    Returns:
        Dict: Bronze record
    """
    return {
        "source_id": f"{source}:{place.place_id}",
        "source": source,
        "city": city.lower().replace(" ", "_"),
        "category": place.types[0] if place.types else "unknown",
        "raw_data": {
            "place_id": place.place_id,
            "name": place.name,
            "address": place.address,
            "location": {
                "lat": place.lat,
                "lng": place.lng
            },
            "types": place.types,
            "rating": place.rating,
            "user_ratings_total": place.user_ratings_total,
            "phone": place.phone_number,
            "website": place.website,
            "photos": place.photos,
            "price_level": place.price_level,
            "vicinity": place.vicinity,
            "business_status": place.business_status
        },
        "ingestion_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "data_version": "1.0"
    }

