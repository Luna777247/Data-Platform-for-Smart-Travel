"""
OSM Data Ingestion Engine - Bronze Layer Implementation
=======================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/ingestion/ section
Kế thừa pattern từ BaseIngestionEngine

Mục đích:
- Thu thập raw POI data từ OpenStreetMap qua Overpass API
- Transform raw OSM elements thành standardized BronzeRecords
- Lưu trữ vào Bronze layer (raw JSON files)
- Hỗ trợ multi-city, multi-category batch ingestion

Architecture:
- OSMIngestionEngine: Main engine class
- fetch_osm_data(): Overpass API communication
- create_bronze_record(): Data transformation
- ingest_city_category(): Orchestrate single job
- ingest_all(): Batch processing orchestration

Data Flow:
  Overpass API → Raw OSM Elements → BronzeRecord → JSON File (Bronze Layer)

Usage:
    >>> engine = OSMIngestionEngine()
    >>> await engine.ingest_city_category("tokyo", POICategory.RESTAURANT)
    ✅ Saved 1500 records to storage/bronze/osm/tokyo/restaurant/
    
    >>> await engine.ingest_all(
    ...     cities=["tokyo", "osaka"],
    ...     categories=[POICategory.RESTAURANT, POICategory.HOTEL]
    ... )
    ✅ Batch ingestion complete: 4 jobs, 5000 total records
"""

# Import asyncio cho async operations (HTTP requests)
import asyncio

# Import logging để ghi lại ingestion process
import logging

# Import json cho serialization
import json

# Import os cho filesystem operations
import os

# Import datetime classes cho timestamps
# datetime: Tạo timestamp objects
# timezone: Xử lý UTC timestamps
from datetime import datetime, timezone

# Import type hints cho type checking và documentation
from typing import List, Dict, Any, Optional

# Import Path từ pathlib cho cross-platform path handling
from pathlib import Path

# Import httpx cho async HTTP requests
# Httpx: Modern async HTTP client, thay thế aiohttp và requests
import httpx

# Import data schemas từ pipelines.shared
# BronzeRecord: Standardized format cho raw data
# BronzeMetadata: Metadata wrapper cho Bronze records
# SourceType: Enum cho data sources (OSM, Google, etc.)
# POICategory: Enum cho POI categories
# ProcessingStatus: Enum cho processing states
from pipelines.shared.schemas import (
    BronzeRecord, BronzeMetadata, SourceType, POICategory, ProcessingStatus
)

# Import utility functions
# make_ukey: Tạo unique keys
# setup_logging: Cấu hình logging
from pipelines.shared.utils import make_ukey, setup_logging

# ============================================
# LOGGER SETUP
# ============================================
# Khởi tạo logger cho module này
# Logs sẽ có format JSON với correlation ID
logger = setup_logging(__name__)


class OSMIngestionEngine:
    """Engine để thu thập dữ liệu OSM"""
    
    def __init__(self, config_path: str = "storage/configs"):
        self.config_path = Path(config_path)
        self.cities_config = {}
        self.poi_types_config = {}
        self.osm_settings = {}
        self.load_configurations()
    
    def load_configurations(self):
        """Load cấu hình từ files"""
        try:
            # Load cities config
            cities_file = self.config_path / "cities.json"
            if cities_file.exists():
                with open(cities_file, 'r', encoding='utf-8') as f:
                    self.cities_config = json.load(f)
            
            # Load POI types config  
            types_file = self.config_path / "poi_types.json"
            if types_file.exists():
                with open(types_file, 'r', encoding='utf-8') as f:
                    self.poi_types_config = json.load(f)
            
            # Load OSM settings
            settings_file = self.config_path / "osm_settings.json"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.osm_settings = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.cities_config)} cities and {len(self.poi_types_config)} POI types")
            
        except Exception as e:
            logger.error(f"❌ Error loading configurations: {e}")
            raise
    
    def get_bronze_path(self, city: str, category: POICategory) -> Path:
        """Get đường dẫn lưu file Bronze"""
        bronze_dir = Path("storage/bronze/osm") / city / category.value
        bronze_dir.mkdir(parents=True, exist_ok=True)
        return bronze_dir
    
    def generate_filename(self, category: POICategory) -> str:
        """Generate filename theo unified naming convention"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"raw_{timestamp}.json"
    
    async def fetch_osm_data(
        self, 
        city: str, 
        category: POICategory, 
        limit: int = 50000
    ) -> List[Dict[str, Any]]:
        """Fetch dữ liệu từ OSM Overpass API"""
        
        if city not in self.cities_config:
            logger.error(f"❌ City '{city}' not found in configuration")
            return []
        
        if category.value not in self.poi_types_config:
            logger.error(f"❌ Category '{category.value}' not found in configuration")
            return []
        
        city_data = self.cities_config[city]
        city_name = city_data.get('name', city)
        query_template = self.poi_types_config[category.value]
        
        # Build Overpass QL query
        query = f"""
        [out:json][timeout:60];
        area["name"="{city_name}"]->.searchArea;
        (
          {query_template}
        );
        out center meta;
        """
        
        # User agents để tránh bị block
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "SmartTourismProject/1.0 (Research; contact@smarttravel.vn)",
            "DataPipeline/1.0 (Educational Purpose; +1 research)"
        ]
        
        overpass_urls = self.osm_settings.get(
            "overpass_urls", 
            ["https://lz4.overpass-api.de/api/interpreter"]
        )
        
        headers = {
            'User-Agent': user_agents[0],
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for url in overpass_urls:
                try:
                    response = await client.post(
                        url, 
                        data={'data': query}, 
                        headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    elements = data.get('elements', [])
                    
                    logger.info(f"✅ Found {len(elements)} {category.value} in {city}")
                    return elements[:limit]
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch from {url}: {e}")
                    continue
        
        logger.error(f"❌ Failed to fetch {category.value} from all URLs")
        return []
    
    def create_bronze_record(
        self, 
        raw_element: Dict[str, Any], 
        city: str, 
        category: POICategory,
        request_url: Optional[str] = None
    ) -> BronzeRecord:
        """Tạo Bronze record từ raw OSM element"""
        
        metadata = BronzeMetadata(
            city=city,
            category=category,
            source=SourceType.OSM,
            ingestion_at=datetime.now(timezone.utc),
            record_count=1,
            request_url=request_url
        )
        
        return BronzeRecord(
            metadata=metadata.dict(),
            source=SourceType.OSM,
            ingestion_at=datetime.now(timezone.utc),
            raw_response=raw_element
        )
    
    async def ingest_city_category(
        self, 
        city: str, 
        category: POICategory
    ) -> bool:
        """Ingest dữ liệu cho 1 city và 1 category"""
        
        try:
            start_time = datetime.now(timezone.utc)
            logger.info(f"🚀 Starting ingestion: {city} - {category.value}")
            
            # Fetch data từ OSM API
            raw_elements = await self.fetch_osm_data(city, category)
            
            if not raw_elements:
                logger.warning(f"⚠️ No data found for {city} - {category.value}")
                return False
            
            # Convert sang Bronze records
            bronze_records = []
            for element in raw_elements:
                record = self.create_bronze_record(element, city, category)
                bronze_records.append(record)
            
            # Lưu vào Bronze layer
            bronze_path = self.get_bronze_path(city, category)
            filename = self.generate_filename(category)
            output_file = bronze_path / filename
            
            # Prepare output data với metadata wrapper
            output_data = {
                "metadata": {
                    "city": city,
                    "category": category.value,
                    "source": SourceType.OSM.value,
                    "ingestion_at": datetime.now(timezone.utc).isoformat(),
                    "record_count": len(bronze_records),
                    "processing_time_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                },
                "records": [record.dict() for record in bronze_records]
            }
            
            # Write file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"✅ Completed {city} - {category.value}: {len(bronze_records)} records in {processing_time:.2f}s")
            logger.info(f"📁 Saved to: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ingesting {city} - {category.value}: {e}")
            return False
    
    async def ingest_all(
        self, 
        cities: Optional[List[str]] = None,
        categories: Optional[List[POICategory]] = None
    ) -> Dict[str, Any]:
        """Ingest toàn bộ dữ liệu"""
        
        # Use defaults if not specified
        target_cities = cities or list(self.cities_config.keys())
        target_categories = categories or [
            POICategory.TOURIST_ATTRACTION,
            POICategory.RESTAURANT,
            POICategory.HOTEL,
            POICategory.CAFE,
            POICategory.SHOPPING_MALL,
            POICategory.PARK,
            POICategory.CINEMA,
            POICategory.MUSEUM
        ]
        
        logger.info(f"🎯 Starting ingestion for {len(target_cities)} cities, {len(target_categories)} categories")
        
        results = {
            "total_jobs": len(target_cities) * len(target_categories),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process all combinations
        for city in target_cities:
            for category in target_categories:
                success = await self.ingest_city_category(city, category)
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{city}-{category.value}")
        
        logger.info(f"🎉 Ingestion completed: {results['successful']}/{results['total_jobs']} successful")
        if results["failed"] > 0:
            logger.warning(f"⚠️ Failed jobs: {results['failed']}")
            logger.warning(f"❌ Errors: {results['errors']}")
        
        return results


async def main():
    """Main function để run ingestion"""
    ingestion_engine = OSMIngestionEngine()
    
    # Run ingestion cho tất cả cities và categories
    results = await ingestion_engine.ingest_all()
    
    logger.info("=" * 50)
    logger.info("📊 INGESTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total jobs: {results['total_jobs']}")
    logger.info(f"Successful: {results['successful']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Success rate: {results['successful']/results['total_jobs']*100:.1f}%")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
