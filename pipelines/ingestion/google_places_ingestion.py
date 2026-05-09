"""
Google Places Data Ingestion Engine - RapidAPI Implementation
=============================================================
Thu thập POI data từ Google Places API thông qua RapidAPI proxy

RapidAPI Endpoint: google-map-places.p.rapidapi.com
Sử dụng 18 API keys luân phiên để tránh rate limiting

Features:
- Find Place from Text: Tìm địa điểm từ text query
- Nearby Search: Tìm địa điểm gần vị trí
- Text Search: Tìm kiếm text nâng cao
- Place Details: Chi tiết địa điểm đầy đủ

Data Flow:
  RapidAPI → Google Places Data → BronzeRecord → JSON File

Usage:
    >>> from pipelines.ingestion.google_places_ingestion import GooglePlacesIngestionEngine
    >>> engine = GooglePlacesIngestionEngine()
    >>> 
    >>> # Ingest một thành phố
    >>> result = await engine.ingest_city("tokyo", ["restaurant", "hotel", "tourist_attraction"])
    >>> 
    >>> # Batch ingest nhiều thành phố
    >>> await engine.ingest_all(
    ...     cities=["tokyo", "osaka", "bangkok"],
    ...     categories=["restaurant", "hotel"],
    ...     max_results_per_category=100
    ... )
"""

# Import asyncio cho async operations
import asyncio

# Import logging cho structured logging
import logging

# Import json cho JSON serialization
import json

# Import os cho filesystem operations
import os

# Import datetime cho timestamps
from datetime import datetime, timezone

# Import typing cho type hints
from typing import List, Dict, Any, Optional

# Import pathlib cho cross-platform paths
from pathlib import Path

# Import aiohttp cho async HTTP requests
import aiohttp

# Import time cho rate limiting
import time

# Import random cho API key rotation
import random

# Import dataclass cho data structures
from dataclasses import dataclass, asdict

# Import GooglePlacesCollector từ collectors module
from src.collectors.google_places_collector import (
    GooglePlacesCollector,
    PlaceResult,
    PlaceDetails,
    RAPID_API_KEYS,
    RAPIDAPI_HOST,
    FIND_PLACE_URL,
    NEARBY_SEARCH_URL,
    TEXT_SEARCH_URL,
    PLACE_DETAILS_URL
)

# Import schemas từ pipelines.shared
from pipelines.shared.schemas import BronzeRecord, BronzeMetadata, SourceType, POICategory

# Import utility functions
from pipelines.shared.utils import make_ukey, setup_logging, normalize_coordinates


# =============================================================================
# LOGGER SETUP
# =============================================================================

logger = setup_logging(__name__)


# =============================================================================
# GOOGLE PLACES INGESTION ENGINE
# =============================================================================

class GooglePlacesIngestionEngine:
    """
    Engine để thu thập dữ liệu POI từ Google Places API qua RapidAPI.
    
    Features:
    - Luân phiên 18 RapidAPI keys để tránh rate limiting
    - Multi-city, multi-category batch ingestion
    - Automatic retry với exponential backoff
    - Bronze record creation và storage
    
    Data Sources:
    - Text Search: Tìm kiếm bằng text query
    - Nearby Search: Tìm địa điểm gần vị trí
    - Place Details: Chi tiết đầy đủ về địa điểm
    
    Storage:
    - Bronze layer: storage/bronze/google_places/{city}/{category}/
    """
    
    def __init__(
        self,
        bronze_dir: str = "storage/bronze",
        config_path: str = "storage/configs",
        max_concurrent_requests: int = 5
    ):
        """
        Khởi tạo GooglePlacesIngestionEngine.
        
        Args:
            bronze_dir: Thư mục lưu bronze records
            config_path: Thư mục chứa config files
            max_concurrent_requests: Số requests đồng thời tối đa
        """
        self.bronze_dir = Path(bronze_dir)
        self.config_path = Path(config_path)
        self.max_concurrent_requests = max_concurrent_requests
        
        # Khởi tạo collector
        self.collector = GooglePlacesCollector(logger=logger)
        
        # Tạo thư mục nếu chưa tồn tại
        self.bronze_dir.mkdir(parents=True, exist_ok=True)
        
        # Semaphore cho rate limiting
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # Stats tracking
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "records_created": 0
        }
        
        logger.info(
            "GooglePlacesIngestionEngine initialized: "
            f"bronze_dir={bronze_dir}, "
            f"max_concurrent={max_concurrent_requests}"
        )
    
    async def _ingest_single_category(
        self,
        city: str,
        category: str,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Ingest một category cho một thành phố.
        
        Args:
            city: Tên thành phố
            category: Loại POI (restaurant, hotel, etc.)
            max_results: Số kết quả tối đa
            
        Returns:
            List[Dict]: Bronze records
        """
        logger.info(f"Ingesting {category} in {city}")
        
        # Tạo text query
        query = f"{category} in {city}"
        
        async with self._semaphore:
            try:
                # Tìm kiếm địa điểm
                places = await self.collector.text_search(
                    query=query,
                    type_filter=category if category in [
                        "restaurant", "cafe", "bar", "lodging", "hotel",
                        "tourist_attraction", "museum", "park", "shopping_mall"
                    ] else None
                )
                
                self._stats["total_requests"] += 1
                
                if not places:
                    logger.warning(f"No results found for {category} in {city}")
                    return []
                
                # Giới hạn số kết quả
                places = places[:max_results]
                
                # Chuyển thành bronze records
                bronze_records = []
                
                for place in places:
                    bronze_record = await self._create_bronze_record(place, city, category)
                    if bronze_record:
                        bronze_records.append(bronze_record)
                
                self._stats["successful_requests"] += 1
                self._stats["records_created"] += len(bronze_records)
                
                logger.info(
                    f"Created {len(bronze_records)} bronze records "
                    f"for {category} in {city}"
                )
                
                return bronze_records
                
            except Exception as e:
                self._stats["failed_requests"] += 1
                logger.error(f"Error ingesting {category} in {city}: {str(e)}")
                return []
    
    async def _create_bronze_record(
        self,
        place: PlaceResult,
        city: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Tạo bronze record từ PlaceResult.
        
        Args:
            place: PlaceResult object
            city: Tên thành phố
            category: Loại POI
            
        Returns:
            Optional[Dict]: Bronze record hoặc None
        """
        try:
            # Lấy thêm chi tiết nếu cần
            details = None
            if place.place_id:
                try:
                    details = await self.collector.get_place_details(place.place_id)
                except Exception as e:
                    logger.warning(f"Could not get details for {place.place_id}: {e}")
            
            # Tạo bronze record
            timestamp = datetime.now(timezone.utc).isoformat()
            
            bronze_record = {
                "_id": make_ukey(f"google:{place.place_id}"),
                "source_id": f"google:{place.place_id}",
                "source": "google_places",
                "city": city.lower().replace(" ", "_"),
                "category": category,
                "raw_data": {
                    "place_id": place.place_id,
                    "name": place.name,
                    "address": place.address or place.vicinity,
                    "location": {
                        "lat": place.lat,
                        "lng": place.lng
                    },
                    "types": place.types,
                    "rating": place.rating,
                    "user_ratings_total": place.user_ratings_total,
                    "phone": place.phone_number,
                    "website": place.website,
                    "photos": [
                        {
                            "photo_reference": p.get("photo_reference"),
                            "width": p.get("width"),
                            "height": p.get("height")
                        }
                        for p in (place.photos or [])
                    ],
                    "price_level": place.price_level,
                    "vicinity": place.vicinity,
                    "business_status": place.business_status,
                    # Thêm chi tiết nếu có
                    "details": asdict(details) if details else None
                },
                "ingestion_timestamp": timestamp,
                "data_version": "1.0",
                "metadata": {
                    "collector": "google_places",
                    "api_source": "rapidapi",
                    "quality_score": self._calculate_quality_score(place, details)
                }
            }
            
            return bronze_record
            
        except Exception as e:
            logger.error(f"Error creating bronze record for {place.place_id}: {str(e)}")
            return None
    
    def _calculate_quality_score(
        self,
        place: PlaceResult,
        details: Optional[PlaceDetails]
    ) -> float:
        """
        Tính quality score cho record.
        
        Args:
            place: PlaceResult
            details: PlaceDetails (optional)
            
        Returns:
            float: Quality score (0.0 - 1.0)
        """
        score = 0.0
        
        # Có tọa độ
        if place.lat and place.lng:
            score += 0.3
        
        # Có địa chỉ
        if place.address or place.vicinity:
            score += 0.2
        
        # Có rating
        if place.rating:
            score += 0.2
        
        # Có số điện thoại
        if place.phone_number:
            score += 0.1
        
        # Có website
        if place.website:
            score += 0.1
        
        # Có chi tiết đầy đủ
        if details:
            score += 0.1
        
        return min(score, 1.0)
    
    def _save_bronze_records(
        self,
        records: List[Dict[str, Any]],
        city: str,
        category: str
    ) -> str:
        """
        Lưu bronze records vào file.
        
        Args:
            records: Danh sách bronze records
            city: Tên thành phố
            category: Loại POI
            
        Returns:
            str: Path đến file đã lưu
        """
        # Tạo thư mục
        save_dir = self.bronze_dir / "google_places" / city.lower().replace(" ", "_") / category
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{city.lower().replace(' ', '_')}_{category}_{timestamp}.json"
        filepath = save_dir / filename
        
        # Lưu file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(records)} records to {filepath}")
        
        return str(filepath)
    
    async def ingest_city(
        self,
        city: str,
        categories: List[str],
        max_results_per_category: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest dữ liệu cho một thành phố.
        
        Args:
            city: Tên thành phố
            categories: Danh sách loại POI cần ingest
            max_results_per_category: Số kết quả tối đa mỗi category
            
        Returns:
            Dict: Kết quả ingestion
        """
        logger.info(f"Starting ingestion for city: {city}")
        start_time = time.time()
        
        results = {
            "city": city,
            "categories": {},
            "total_records": 0,
            "files_created": []
        }
        
        for category in categories:
            logger.info(f"Processing category: {category}")
            
            # Ingest category
            records = await self._ingest_single_category(
                city=city,
                category=category,
                max_results=max_results_per_category
            )
            
            if records:
                # Lưu file
                filepath = self._save_bronze_records(records, city, category)
                
                results["categories"][category] = {
                    "records_count": len(records),
                    "file": filepath
                }
                results["total_records"] += len(records)
                results["files_created"].append(filepath)
            else:
                results["categories"][category] = {
                    "records_count": 0,
                    "file": None,
                    "error": "No records found"
                }
        
        elapsed_time = time.time() - start_time
        
        results["elapsed_seconds"] = round(elapsed_time, 2)
        results["status"] = "success" if results["total_records"] > 0 else "partial"
        
        logger.info(
            f"City ingestion complete: {city}, "
            f"{results['total_records']} records, "
            f"{elapsed_time:.2f}s"
        )
        
        return results
    
    async def ingest_all(
        self,
        cities: List[str],
        categories: List[str] = None,
        max_results_per_category: int = 100
    ) -> Dict[str, Any]:
        """
        Batch ingest cho nhiều thành phố.
        
        Args:
            cities: Danh sách thành phố
            categories: Danh sách loại POI (default: common types)
            max_results_per_category: Số kết quả tối đa
            
        Returns:
            Dict: Kết quả batch ingestion
        """
        # Default categories nếu không có
        if categories is None:
            categories = [
                "restaurant",
                "cafe",
                "bar",
                "lodging",
                "tourist_attraction",
                "museum",
                "park",
                "shopping_mall"
            ]
        
        logger.info(f"Starting batch ingestion: {len(cities)} cities, {len(categories)} categories")
        start_time = time.time()
        
        results = {
            "cities": {},
            "total_cities": len(cities),
            "total_categories": len(categories),
            "total_records": 0,
            "failed_cities": []
        }
        
        # Process từng city
        for city in cities:
            try:
                city_result = await self.ingest_city(
                    city=city,
                    categories=categories,
                    max_results_per_category=max_results_per_category
                )
                
                results["cities"][city] = city_result
                results["total_records"] += city_result["total_records"]
                
            except Exception as e:
                logger.error(f"Failed to ingest city {city}: {str(e)}")
                results["failed_cities"].append({
                    "city": city,
                    "error": str(e)
                })
        
        elapsed_time = time.time() - start_time
        
        results["elapsed_seconds"] = round(elapsed_time, 2)
        results["status"] = "success" if len(results["failed_cities"]) == 0 else "partial"
        
        # Thêm stats
        results["stats"] = self._stats.copy()
        
        logger.info(
            f"Batch ingestion complete: "
            f"{results['total_records']} records, "
            f"{len(results['failed_cities'])} failed cities, "
            f"{elapsed_time:.2f}s"
        )
        
        return results
    
    async def close(self):
        """
        Đóng collector và cleanup.
        """
        await self.collector.close()
        logger.info("GooglePlacesIngestionEngine closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    """
    CLI entry point cho testing.
    """
    import sys
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python google_places_ingestion.py <city> [category1,category2,...]")
        print("Example: python google_places_ingestion.py tokyo restaurant,hotel")
        sys.exit(1)
    
    city = sys.argv[1]
    categories = sys.argv[2].split(",") if len(sys.argv) > 2 else ["restaurant", "hotel"]
    
    print(f"Ingesting Google Places data for: {city}")
    print(f"Categories: {categories}")
    
    async with GooglePlacesIngestionEngine() as engine:
        result = await engine.ingest_city(city, categories, max_results_per_category=50)
        
        print(f"\n✅ Ingestion complete!")
        print(f"Total records: {result['total_records']}")
        print(f"Elapsed time: {result['elapsed_seconds']}s")
        
        for category, data in result['categories'].items():
            print(f"  - {category}: {data['records_count']} records")


if __name__ == "__main__":
    asyncio.run(main())
