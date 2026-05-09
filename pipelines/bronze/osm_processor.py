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
    """Processor cho Bronze OSM data"""
    
    def __init__(self, bronze_path: str = "storage/bronze"):
        self.bronze_path = Path(bronze_path)
        self.silver_path = Path("storage/silver/osm")
    
    def get_bronze_files(self, city: str, category: POICategory) -> List[Path]:
        """Get danh sách Bronze files cho city và category"""
        bronze_dir = self.bronze_path / "osm" / city / category.value
        if not bronze_dir.exists():
            logger.warning(f"Bronze directory not found: {bronze_dir}")
            return []
        
        # Get raw_*.json files
        files = list(bronze_dir.glob("raw_*.json"))
        return sorted(files, reverse=True)  # Latest first
    
    def load_bronze_record(self, file_path: Path) -> Optional[BronzeRecord]:
        """Load Bronze record từ file"""
        try:
            data = load_json_file(file_path)
            if not data:
                return None
            
            # Extract metadata và records
            metadata = data.get("metadata", {})
            records = data.get("records", [])
            
            if not records:
                logger.warning(f"No records found in {file_path}")
                return None
            
            # Return first record as BronzeRecord (for metadata extraction)
            if records:
                return BronzeRecord(**records[0])
            
        except Exception as e:
            logger.error(f"Error loading Bronze record from {file_path}: {e}")
            return None
    
    def process_osm_element(self, raw_element: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[SilverPlace]:
        """Process single OSM element sang Silver schema"""
        try:
            # Extract basic info
            element_id = str(raw_element.get("id", ""))
            element_type = raw_element.get("type", "node")
            tags = raw_element.get("tags", {})
            
            # Extract coordinates
            if element_type == "node":
                lat = raw_element.get("lat")
                lon = raw_element.get("lon")
            else:
                # For way/relation, get center from bounds
                bounds = raw_element.get("bounds", {})
                lat = bounds.get("lat") or raw_element.get("center", {}).get("lat")
                lon = bounds.get("lon") or raw_element.get("center", {}).get("lon")
            
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
            
            # Create unique key
            city = metadata.get("city", "")
            u_key = f"{city}_{element_id}_{category.value}"
            
            # Create Silver place
            silver_place = SilverPlace(
                u_key=u_key,
                source_id=element_id,
                name=name,
                name_en=tags.get("name:en"),
                category=category,
                subcategory=tags.get("tourism") or tags.get("shop") or tags.get("amenity"),
                city=city,
                country=self._get_country_from_city(city),
                address=address,
                location=coordinates,
                tags=tags,
                source=SourceType.OSM,
                language=self._detect_language(tags),
                ingestion_at=datetime.fromisoformat(metadata.get("ingestion_at", datetime.now(timezone.utc).isoformat())),
                processed_at=datetime.now(timezone.utc),
                raw_file=metadata.get("filename", ""),
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
    
    def process_bronze_file(self, bronze_file: Path) -> bool:
        """Process single Bronze file sang Silver format"""
        try:
            logger.info(f"🔄 Processing Bronze file: {bronze_file}")
            
            # Load Bronze data
            bronze_data = load_json_file(bronze_file)
            if not bronze_data:
                return False
            
            metadata = bronze_data.get("metadata", {})
            records = bronze_data.get("records", [])
            
            if not records:
                logger.warning(f"No records to process in {bronze_file}")
                return False
            
            # Process all records
            silver_places = []
            for record_data in records:
                raw_element = record_data.get("raw_response", {})
                if not raw_element:
                    continue
                
                silver_place = self.process_osm_element(raw_element, metadata)
                if silver_place:
                    silver_places.append(silver_place)
            
            if not silver_places:
                logger.warning(f"No valid Silver places created from {bronze_file}")
                return False
            
            # Save to Silver layer
            city = metadata.get("city", "")
            category = metadata.get("category", "")
            
            silver_dir = self.silver_path / city / category
            silver_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"processed_{timestamp}.json"
            output_file = silver_dir / filename
            
            # Prepare output data
            output_data = {
                "metadata": {
                    "city": city,
                    "category": category,
                    "source": SourceType.OSM.value,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "record_count": len(silver_places),
                    "quality_score": sum(calculate_quality_score(
                        p.name, p.address, p.location, p.tags, p.category
                    ) for p in silver_places) / len(silver_places),
                    "bronze_file": str(bronze_file.name)
                },
                "places": [place.dict() for place in silver_places]
            }
            
            success = save_json_file(output_data, output_file)
            if success:
                logger.info(f"✅ Processed {len(silver_places)} places to {output_file}")
                return True
            else:
                logger.error(f"❌ Failed to save Silver data to {output_file}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing Bronze file {bronze_file}: {e}")
            return False
    
    def process_city_category(self, city: str, category: POICategory) -> Dict[str, Any]:
        """Process tất cả Bronze files cho city và category"""
        bronze_files = self.get_bronze_files(city, category)
        
        if not bronze_files:
            return {
                "city": city,
                "category": category.value,
                "total_files": 0,
                "processed_files": 0,
                "total_places": 0,
                "errors": []
            }
        
        results = {
            "city": city,
            "category": category.value,
            "total_files": len(bronze_files),
            "processed_files": 0,
            "total_places": 0,
            "errors": []
        }
        
        for bronze_file in bronze_files:
            success = self.process_bronze_file(bronze_file)
            if success:
                results["processed_files"] += 1
                
                # Count places in processed file
                try:
                    silver_data = load_json_file(bronze_file)
                    if silver_data:
                        results["total_places"] += len(silver_data.get("records", []))
                except:
                    pass
            else:
                results["errors"].append(str(bronze_file.name))
        
        return results
    
    def process_all(self, cities: Optional[List[str]] = None, categories: Optional[List[POICategory]] = None) -> Dict[str, Any]:
        """Process tất cả Bronze data"""
        
        # Get available cities and categories
        available_cities = []
        if self.bronze_path.exists():
            for city_dir in (self.bronze_path / "osm").iterdir():
                if city_dir.is_dir():
                    available_cities.append(city_dir.name)
        
        target_cities = cities or available_cities
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
                "processed_files": 0,
                "failed_files": 0
            }
            
            for category in target_categories:
                result = self.process_city_category(city, category)
                
                if result["processed_files"] > 0:
                    summary["processed_jobs"] += 1
                else:
                    summary["failed_jobs"] += 1
                
                city_summary["categories"][category.value] = result
                city_summary["total_places"] += result["total_places"]
                city_summary["processed_files"] += result["processed_files"]
                city_summary["failed_files"] += len(result["errors"])
            
            summary["city_results"][city] = city_summary
            summary["total_places"] += city_summary["total_places"]
        
        logger.info("=" * 60)
        logger.info("📊 BRONZE PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total jobs: {summary['total_jobs']}")
        logger.info(f"Processed: {summary['processed_jobs']}")
        logger.info(f"Failed: {summary['failed_jobs']}")
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
