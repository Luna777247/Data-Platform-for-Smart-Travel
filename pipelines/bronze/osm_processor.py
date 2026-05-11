"""
Bronze Layer Processor - OSM Data Cleaning & Normalization
=========================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/bronze/ section
Part of: Bronze → Silver data transformation pipeline

Mục đích:
- Đọc raw Bronze records từ JSON files
- Clean và normalize OSM data (tags, coordinates, addresses)
- Transform thành SilverPlace objects (standardized schema)
- Lưu vào Silver layer cho downstream processing

Processing Steps:
1. Load Bronze JSON files
2. Extract và validate OSM elements
3. Normalize coordinates (lat/lon)
4. Extract names từ OSM tags (name, name:en, etc.)
5. Normalize categories (OSM tags → canonical categories)
6. Clean addresses
7. Calculate quality scores
8. Save Silver records

Data Flow:
  Bronze JSON → BronzeRecord → OSM Element → SilverPlace → Silver JSON

Usage:
    >>> processor = BronzeOSMProcessor()
    >>> await processor.process_city_category("tokyo", POICategory.RESTAURANT)
    ✅ Processed 1500 Bronze records → 1450 Silver records
    
    >>> await processor.process_all()
    ✅ Batch processing complete: 8 cities, 32 categories, 25000 records
"""

# Import logging để ghi lại processing operations
import logging

# Import json cho data serialization/deserialization
import json

# Import datetime classes cho timestamps
from datetime import datetime, timezone

# Import Path cho cross-platform filesystem operations
from pathlib import Path

# Import type hints cho type checking
from typing import List, Dict, Any, Optional

# Import MongoDB
from pymongo import MongoClient

# Import data schemas từ pipelines.shared
# BronzeRecord: Input format từ Bronze layer
# SilverPlace: Output format cho Silver layer
# POICategory: Enum cho category normalization
# SourceType: Enum cho data source tracking
# ProcessingStatus: Enum cho processing state
from pipelines.shared.schemas import (
    BronzeRecord, SilverPlace, POICategory, SourceType, ProcessingStatus
)

# Import utility functions từ pipelines.shared
# setup_logging: Cấu hình structured logging
# normalize_coordinates: Chuẩn hóa lat/lon
# extract_name_from_tags: Trích xuất tên từ OSM tags
# normalize_category: Chuẩn hóa category
# clean_address: Làm sạch địa chỉ
# calculate_quality_score: Tính điểm chất lượng data
# load_json_file: Đọc JSON files
# save_json_file: Lưu JSON files
from pipelines.shared.utils import (
    setup_logging, normalize_coordinates, extract_name_from_tags, 
    normalize_category, clean_address, calculate_quality_score,
    load_json_file, save_json_file
)

# ============================================
# LOGGER SETUP
# ============================================
# Khởi tạo logger cho module này
logger = setup_logging(__name__)


class BronzeOSMProcessor:
    """Processor cho Bronze OSM data từ MongoDB bronze_pois"""
    
    def __init__(self, mongo_uri: str = None):
        # MongoDB connection
        import os
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI", 
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client.smart_travel_platform
        
        # Output path for Silver (file backup)
        self.silver_path = Path("storage/silver/osm")
    
    def get_bronze_records(self, city: str, category: POICategory) -> List[Dict[str, Any]]:
        """Get bronze records từ MongoDB bronze_pois collection"""
        try:
            # Query bronze_pois collection với osm_raw data
            query = {
                "city": city,
                "category": category.value,
                "has_osm_data": True,
                "osm_raw": {"$exists": True}
            }
            
            records = list(self.db.bronze_pois.find(query))
            logger.info(f"Found {len(records)} bronze records for {city}/{category.value}")
            return records
            
        except Exception as e:
            logger.error(f"Error querying bronze_pois: {e}")
            return []
    
    def load_bronze_record(self, record: Dict[str, Any]) -> Optional[BronzeRecord]:
        """Load Bronze record từ MongoDB document"""
        try:
            if not record or not record.get("osm_raw"):
                return None
            
            # Extract from osm_raw.element
            osm_raw = record.get("osm_raw", {})
            element = osm_raw.get("element", {})
            
            if not element:
                return None
            
            # Build BronzeRecord from MongoDB document
            return BronzeRecord(
                u_key=record.get("u_key"),
                poi_id=record.get("poi_id"),
                name=record.get("name"),
                city=record.get("city"),
                category=record.get("category"),
                location=record.get("location"),
                osm_id=record.get("osm_id"),
                osm_type=record.get("osm_type"),
                osm_tags=element.get("tags", {}),
                raw_response=element,
                metadata={
                    "city": record.get("city"),
                    "category": record.get("category"),
                    "ingestion_at": record.get("created_at"),
                    "has_google_data": record.get("has_google_data", False)
                }
            )
            
        except Exception as e:
            logger.error(f"Error loading Bronze record: {e}")
            return None
    
    def process_osm_element(self, bronze_record: Dict[str, Any]) -> Optional[SilverPlace]:
        """Process bronze record từ MongoDB sang Silver schema"""
        try:
            # Extract from bronze_pois document
            osm_raw = bronze_record.get("osm_raw", {})
            element = osm_raw.get("element", {})
            
            if not element:
                logger.warning("No osm_raw.element found in record")
                return None
            
            # Extract basic info
            element_id = str(element.get("id", ""))
            element_type = element.get("type", "node")
            tags = element.get("tags", {})
            
            # Extract coordinates
            if element_type == "node":
                lat = element.get("lat")
                lon = element.get("lon")
            else:
                # For way/relation, get center from bounds
                bounds = element.get("bounds", {})
                lat = bounds.get("lat") or element.get("center", {}).get("lat")
                lon = bounds.get("lon") or element.get("center", {}).get("lon")
            
            coordinates = normalize_coordinates(lat, lon)
            if not coordinates:
                logger.warning(f"Invalid coordinates for element {element_id}")
                return None
            
            # Extract name
            name = extract_name_from_tags(tags)
            if not name or name == "Unnamed":
                logger.warning(f"No valid name for element {element_id}")
                return None
            
            # Normalize category
            category = normalize_category(tags)
            if not category:
                logger.warning(f"Cannot categorize element {element_id}")
                return None
            
            # Extract address
            address = clean_address(tags)
            
            # Get city từ bronze_record
            city = bronze_record.get("city", "")
            u_key = bronze_record.get("u_key") or f"{city}_{element_id}_{category.value}"
            
            # Create Silver place
            silver_place = SilverPlace(
                u_key=u_key,
                source_id=element_id,
                name=name,
                name_en=tags.get("name:en"),
                category=category,
                subcategory=tags.get("tourism") or tags.get("shop") or tags.get("amenity"),
                city=city,
                country=bronze_record.get("country") or self._get_country_from_city(city),
                address=address,
                location=coordinates,
                tags=tags,
                source=SourceType.OSM,
                language=self._detect_language(tags),
                ingestion_at=datetime.fromisoformat(bronze_record.get("created_at", datetime.now(timezone.utc).isoformat())),
                processed_at=datetime.now(timezone.utc),
                raw_file="bronze_pois",
                status=ProcessingStatus.PROCESSED
            )
            
            return silver_place
            
        except Exception as e:
            logger.error(f"Error processing OSM element: {e}")
            return None
    
    def _get_country_from_city(self, city: str) -> str:
        """Map city sang country"""
        vietnam_cities = [
            "hanoi", "hcm", "danang", "dalat", "hue", 
            "cantho", "haiphong", "nhatrang", "vungtau"
        ]
        
        if city.lower() in vietnam_cities:
            return "Vietnam"
        else:
            # International cities mapping
            international_mapping = {
                "tokyo": "Japan",
                "beijing": "China", 
                "seoul": "South Korea",
                "bangkok": "Thailand",
                "singapore": "Singapore",
                "taipei": "Taiwan",
                "shanghai": "China",
                "hongkong": "Hong Kong",
                "osaka": "Japan",
                "kyoto": "Japan",
                "chiangmai": "Thailand"
            }
            return international_mapping.get(city.lower(), "Unknown")
    
    def _detect_language(self, tags: Dict[str, Any]) -> str:
        """Detect primary language từ tags"""
        # Check for explicit language tags
        for key in tags:
            if key.startswith("name:"):
                lang_code = key.split(":")[1]
                if lang_code in ["vi", "en", "ja", "ko", "zh", "th"]:
                    return lang_code
        
        # Fallback based on content
        if any(key.startswith("name:vi") for key in tags):
            return "vi"
        elif any(key.startswith("name:en") for key in tags):
            return "en"
        elif any(key.startswith("name:ja") for key in tags):
            return "ja"
        elif any(key.startswith("name:ko") for key in tags):
            return "ko"
        elif any(key.startswith("name:zh") for key in tags):
            return "zh"
        elif any(key.startswith("name:th") for key in tags):
            return "th"
        
        return "en"  # Default
    
    def process_bronze_batch(self, city: str, category: POICategory) -> bool:
        """Process batch Bronze records từ MongoDB sang Silver"""
        try:
            logger.info(f"🔄 Processing Bronze batch: {city}/{category.value}")
            
            # Get Bronze records từ MongoDB
            bronze_records = self.get_bronze_records(city, category)
            
            if not bronze_records:
                logger.warning(f"No bronze records found for {city}/{category.value}")
                return False
            
            # Process all records
            silver_places = []
            for bronze_record in bronze_records:
                silver_place = self.process_osm_element(bronze_record)
                if silver_place:
                    silver_places.append(silver_place)
            
            if not silver_places:
                logger.warning(f"No valid Silver places created for {city}/{category.value}")
                return False
            
            # Save to Silver layer (file backup)
            silver_dir = self.silver_path / city / category.value
            silver_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"processed_{timestamp}.json"
            output_file = silver_dir / filename
            
            # Prepare output data
            output_data = {
                "metadata": {
                    "city": city,
                    "category": category.value,
                    "source": SourceType.OSM.value,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "record_count": len(silver_places),
                    "quality_score": sum(calculate_quality_score(
                        p.name, p.address, p.location, p.tags, p.category
                    ) for p in silver_places) / len(silver_places) if silver_places else 0,
                    "bronze_source": "bronze_pois"
                },
                "places": [place.dict() for place in silver_places]
            }
            
            success = save_json_file(output_data, output_file)
            if success:
                logger.info(f"✅ Processed {len(silver_places)} places to {output_file}")
                
                # Also save to MongoDB silver_pois collection
                self._save_to_silver_mongodb(silver_places, city, category.value)
                
                return True
            else:
                logger.error(f"❌ Failed to save Silver data to {output_file}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing Bronze batch {city}/{category.value}: {e}")
            return False
    
    def _save_to_silver_mongodb(self, silver_places: List[SilverPlace], city: str, category: str):
        """Save Silver places to MongoDB silver_pois collection"""
        try:
            silver_docs = []
            for place in silver_places:
                doc = {
                    **place.dict(),
                    "_layer": "silver",
                    "_processed_at": datetime.now(timezone.utc).isoformat()
                }
                silver_docs.append(doc)
            
            if silver_docs:
                # Use insert_many with ordered=False để skip duplicates
                self.db.silver_pois.insert_many(silver_docs, ordered=False)
                logger.info(f"💾 Saved {len(silver_docs)} to MongoDB silver_pois")
        except Exception as e:
            logger.warning(f"MongoDB silver insert: {e}")
    
    def process_city_category(self, city: str, category: POICategory) -> Dict[str, Any]:
        """Process tất cả Bronze records cho city và category"""
        # Get bronze records from MongoDB
        bronze_records = self.get_bronze_records(city, category)
        
        if not bronze_records:
            return {
                "city": city,
                "category": category.value,
                "total_records": 0,
                "processed_records": 0,
                "total_places": 0,
                "errors": []
            }
        
        results = {
            "city": city,
            "category": category.value,
            "total_records": len(bronze_records),
            "processed_records": 0,
            "total_places": 0,
            "errors": []
        }
        
        # Process batch
        success = self.process_bronze_batch(city, category)
        if success:
            results["processed_records"] = len(bronze_records)
            # Count actual silver places created
            try:
                silver_count = self.db.silver_pois.count_documents({
                    "city": city,
                    "category": category.value
                })
                results["total_places"] = silver_count
            except:
                pass
        else:
            results["errors"].append(f"{city}/{category.value}")
        
        return results
    
    def process_all(self, cities: Optional[List[str]] = None, categories: Optional[List[POICategory]] = None) -> Dict[str, Any]:
        """Process tất cả Bronze data từ MongoDB bronze_pois"""
        
        # Get available cities từ MongoDB bronze_pois collection
        if cities:
            target_cities = cities
        else:
            # Distinct cities from bronze_pois
            target_cities = self.db.bronze_pois.distinct("city", {"has_osm_data": True})
            if not target_cities:
                # Fallback to common cities
                target_cities = ["hanoi", "hcm", "danang", "cantho", "haiphong", "hue", "nhatrang", "dalat", "vungtau"]
        
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
        
        logger.info(f"🚀 Starting Bronze processing for {len(target_cities)} cities, {len(target_categories)} categories")
        logger.info(f"   Source: MongoDB bronze_pois (osm_raw data)")
        
        summary = {
            "total_jobs": len(target_cities) * len(target_categories),
            "processed_jobs": 0,
            "failed_jobs": 0,
            "total_places": 0,
            "city_results": {}
        }
        
        for city in target_cities:
            city_summary = {
                "categories": {},
                "total_places": 0,
                "processed_records": 0,
                "failed_batches": 0
            }
            
            for category in target_categories:
                result = self.process_city_category(city, category)
                
                if result["processed_records"] > 0:
                    summary["processed_jobs"] += 1
                else:
                    summary["failed_jobs"] += 1
                
                city_summary["categories"][category.value] = result
                city_summary["total_places"] += result["total_places"]
                city_summary["processed_records"] += result["processed_records"]
                city_summary["failed_batches"] += len(result["errors"])
            
            summary["city_results"][city] = city_summary
            summary["total_places"] += city_summary["total_places"]
        
        logger.info("=" * 60)
        logger.info("📊 BRONZE PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Source: MongoDB bronze_pois")
        logger.info(f"Total jobs: {summary['total_jobs']}")
        logger.info(f"Processed: {summary['processed_jobs']}")
        logger.info(f"Failed: {summary['failed_jobs']}")
        if summary['total_jobs'] > 0:
            logger.info(f"Success rate: {summary['processed_jobs']/summary['total_jobs']*100:.1f}%")
        logger.info(f"Total places: {summary['total_places']}")
        
        return summary


def main():
    """Main function để run Bronze processing"""
    processor = BronzeOSMProcessor()
    results = processor.process_all()
    return results


if __name__ == "__main__":
    main()
