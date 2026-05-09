"""
Silver Layer Processing Module - Data Enrichment & Deduplication
===============================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/silver/ section
Part of: Silver → Gold data transformation pipeline

Mục đích:
- Load SilverPlace records từ Silver layer
- Detect và merge duplicate records (cùng location/name)
- Enrich data với business metrics, search keywords
- Transform thành GoldPlace objects (final schema)
- Lưu vào Gold layer cho serving API

Processing Steps:
1. Load Silver records từ JSON files
2. Detect duplicates dựa trên location proximity và name similarity
3. Merge duplicate records (aggregate ratings, reviews)
4. Calculate business metrics (popularity, quality scores)
5. Generate search keywords cho full-text search
6. Enrich với additional metadata
7. Transform thành GoldPlace objects
8. Save Gold records (JSON và Parquet)

Data Flow:
  Silver JSON → SilverPlace → Deduplication → Enrichment → GoldPlace → Gold JSON/Parquet

Usage:
    >>> processor = SilverProcessor()
    >>> await processor.process_city_category("tokyo", POICategory.RESTAURANT)
    ✅ Processed 1450 Silver records → 1250 Gold records (200 duplicates merged)
    
    >>> await processor.process_all()
    ✅ Batch processing complete: 8 cities, 22000 records, 1500 duplicates merged
"""

# Import logging để ghi lại processing operations
import logging

# Import json cho data serialization
import json

# Import datetime classes cho timestamps
from datetime import datetime, timezone

# Import Path cho filesystem operations
from pathlib import Path

# Import type hints cho type checking
from typing import List, Dict, Any, Optional, Set

# Import pandas cho data manipulation (deduplication, aggregation)
import pandas as pd

# Import defaultdict cho caching
from collections import defaultdict

# Import data schemas từ pipelines.shared
# SilverPlace: Input format từ Silver layer
# GoldPlace: Output format cho Gold layer
# POICategory: Enum cho categories
# ProcessingStatus: Enum cho processing state
# BusinessMetrics: Model cho business metrics
from pipelines.shared.schemas import (
    SilverPlace, GoldPlace, POICategory, ProcessingStatus, BusinessMetrics
)

# Import utility functions
# setup_logging: Cấu hình structured logging
# generate_search_keywords: Tạo search keywords
# save_json_file: Lưu JSON files
# load_json_file: Đọc JSON files
from pipelines.shared.utils import (
    setup_logging, generate_search_keywords, save_json_file, load_json_file
)

# ============================================
# LOGGER SETUP
# ============================================
# Khởi tạo logger cho module này
logger = setup_logging(__name__)


class SilverProcessor:
    """Processor cho Silver layer data"""
    
    def __init__(self, silver_path: str = "storage/silver", gold_path: str = "storage/gold"):
        self.silver_path = Path(silver_path)
        self.gold_path = Path(gold_path)
        self.deduplication_cache: Dict[str, SilverPlace] = {}
    
    def get_silver_files(self, city: str, category: POICategory) -> List[Path]:
        """Get danh sách Silver files cho city và category"""
        silver_dir = self.silver_path / "osm" / city / category.value
        if not silver_dir.exists():
            logger.warning(f"Silver directory not found: {silver_dir}")
            return []
        
        # Get processed_*.json files
        files = list(silver_dir.glob("processed_*.json"))
        return sorted(files, reverse=True)  # Latest first
    
    def load_silver_places(self, file_path: Path) -> List[SilverPlace]:
        """Load Silver places từ file"""
        try:
            data = load_json_file(file_path)
            if not data:
                return []
            
            places_data = data.get("places", [])
            silver_places = []
            
            for place_data in places_data:
                try:
                    silver_place = SilverPlace(**place_data)
                    silver_places.append(silver_place)
                except Exception as e:
                    logger.warning(f"Error parsing Silver place: {e}")
                    continue
            
            return silver_places
            
        except Exception as e:
            logger.error(f"Error loading Silver places from {file_path}: {e}")
            return []
    
    def detect_duplicates(self, places: List[SilverPlace]) -> Dict[str, List[SilverPlace]]:
        """Detect duplicate POIs dựa trên location và name"""
        duplicates = defaultdict(list)
        seen_names: Dict[str, Set[str]] = defaultdict(set)
        
        for place in places:
            # Create deduplication key
            name_key = place.name.lower().strip()
            location_key = f"{place.location['lat']:.6f}_{place.location['lon']:.6f}"
            
            # Check for duplicates by name within 0.001 degrees (~100m)
            for existing_key, existing_places in duplicates.items():
                for existing_place in existing_places:
                    dist = self._calculate_distance(
                        place.location, existing_place.location
                    )
                    if dist < 0.001:  # ~100m radius
                        if name_key in seen_names[existing_key]:
                            duplicates[existing_key].append(place)
                            seen_names[existing_key].add(name_key)
                            break
            
            # If no duplicate found, add as new group
            if not any(place in dup_group for dup_group in duplicates.values()):
                key = f"{name_key}_{location_key}"
                duplicates[key].append(place)
                seen_names[key].add(name_key)
        
        # Filter only groups with duplicates
        return {k: v for k, v in duplicates.items() if len(v) > 1}
    
    def _calculate_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """Calculate distance between two coordinates (degrees)"""
        lat1, lon1 = loc1['lat'], loc1['lon']
        lat2, lon2 = loc2['lat'], loc2['lon']
        return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5
    
    def merge_duplicates(self, duplicate_groups: Dict[str, List[SilverPlace]]) -> List[SilverPlace]:
        """Merge duplicate POIs"""
        merged_places = []
        
        for group_key, places in duplicate_groups.items():
            if len(places) == 1:
                merged_places.extend(places)
                continue
            
            # Choose best place based on data quality
            best_place = self._choose_best_duplicate(places)
            merged_places.append(best_place)
            
            logger.info(f"🔄 Merged {len(places)} duplicates for '{best_place.name}'")
        
        return merged_places
    
    def _choose_best_duplicate(self, places: List[SilverPlace]) -> SilverPlace:
        """Choose best POI từ group duplicates"""
        def score_place(place: SilverPlace) -> int:
            score = 0
            
            # Prefer places with English names
            if place.name_en:
                score += 2
            
            # Prefer places with more tags
            score += len(place.tags)
            
            # Prefer places with addresses
            if place.address and len(place.address.strip()) > 5:
                score += 1
            
            # Prefer places with subcategories
            if place.subcategory:
                score += 1
            
            return score
        
        return max(places, key=score_place)
    
    def enrich_silver_place(self, place: SilverPlace) -> Dict[str, Any]:
        """Enrich Silver place với business metrics"""
        # Calculate business metrics
        business_metrics = BusinessMetrics(
            popularity_score=self._calculate_popularity_score(place),
            quality_score=self._calculate_quality_score(place),
            trust_score=self._calculate_trust_score(place),
            completeness_score=self._calculate_completeness_score(place),
            category_confidence=self._calculate_category_confidence(place)
        )
        
        # Generate search keywords
        search_keywords = generate_search_keywords(
            place.name, place.tags, place.category
        )
        
        # Generate embedding text
        embedding_text = self._generate_embedding_text(place)
        
        # Generate region hierarchy
        region_hierarchy = self._generate_region_hierarchy(place)
        
        return {
            "business_metrics": business_metrics.dict(),
            "search_keywords": search_keywords,
            "embedding_text": embedding_text,
            "region_hierarchy": region_hierarchy
        }
    
    def _calculate_popularity_score(self, place: SilverPlace) -> float:
        """Calculate popularity score (0-1)"""
        score = 0.0
        
        # Base score from tags
        if any(key in place.tags for key in ["tourism", "amenity", "shop"]):
            score += 0.3
        
        # Bonus for well-known places
        if any(keyword in place.name.lower() for keyword in [
            "quán", "nhà hàng", "khách sạn", "công viên", "bảo tàng"
        ]):
            score += 0.2
        
        # Bonus for multiple tags
        score += min(len(place.tags) * 0.05, 0.3)
        
        # Bonus for address
        if place.address and len(place.address.strip()) > 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_quality_score(self, place: SilverPlace) -> float:
        """Calculate data quality score (0-1)"""
        score = 0.0
        
        # Name quality
        if place.name and len(place.name.strip()) >= 3:
            score += 0.3
        
        # Coordinate quality
        if place.location and 'lat' in place.location and 'lon' in place.location:
            lat, lon = place.location['lat'], place.location['lon']
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                score += 0.3
        
        # Tags completeness
        important_tags = ["name", "amenity", "shop", "tourism", "cuisine"]
        tag_count = sum(1 for tag in important_tags if tag in place.tags)
        score += (tag_count / len(important_tags)) * 0.2
        
        # Address completeness
        if place.address and len(place.address.strip()) >= 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_trust_score(self, place: SilverPlace) -> float:
        """Calculate trust score (0-1)"""
        score = 0.5  # Base score
        
        # Bonus for English name
        if place.name_en:
            score += 0.2
        
        # Bonus for multiple language names
        name_langs = [key for key in place.tags.keys() if key.startswith("name:")]
        score += min(len(name_langs) * 0.1, 0.3)
        
        # Bonus for official categories
        if place.subcategory:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_completeness_score(self, place: SilverPlace) -> float:
        """Calculate data completeness score (0-1)"""
        score = 0.0
        
        # Required fields
        if place.name:
            score += 0.2
        if place.location:
            score += 0.2
        if place.category:
            score += 0.2
        
        # Optional fields
        if place.address:
            score += 0.1
        if place.subcategory:
            score += 0.1
        if place.name_en:
            score += 0.1
        if place.tags:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_category_confidence(self, place: SilverPlace) -> float:
        """Calculate category confidence (0-1)"""
        score = 0.5  # Base score
        
        # High confidence if subcategory exists
        if place.subcategory:
            score += 0.3
        
        # Check for explicit category tags
        category_tags = ["tourism", "amenity", "shop", "leisure"]
        if any(tag in place.tags for tag in category_tags):
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_embedding_text(self, place: SilverPlace) -> str:
        """Generate text cho embedding models"""
        text_parts = []
        
        # Name in multiple languages
        if place.name:
            text_parts.append(place.name)
        if place.name_en:
            text_parts.append(place.name_en)
        
        # Category and subcategory
        text_parts.append(place.category.value)
        if place.subcategory:
            text_parts.append(place.subcategory)
        
        # Address
        if place.address:
            text_parts.append(place.address)
        
        # Important tags
        important_tags = ["cuisine", "shop", "amenity", "tourism"]
        for tag in important_tags:
            if tag in place.tags and place.tags[tag]:
                text_parts.append(str(place.tags[tag]))
        
        return " ".join(text_parts)
    
    def _generate_region_hierarchy(self, place: SilverPlace) -> Dict[str, str]:
        """Generate region hierarchy"""
        hierarchy = {
            "city": place.city,
            "country": place.country,
            "continent": self._get_continent(place.country)
        }
        
        # Add region if available
        if "addr:state" in place.tags:
            hierarchy["state"] = place.tags["addr:state"]
        elif "addr:province" in place.tags:
            hierarchy["province"] = place.tags["addr:province"]
        
        return hierarchy
    
    def _get_continent(self, country: str) -> str:
        """Map country sang continent"""
        continent_mapping = {
            "Vietnam": "Asia",
            "Japan": "Asia",
            "China": "Asia",
            "South Korea": "Asia",
            "Thailand": "Asia",
            "Singapore": "Asia",
            "Taiwan": "Asia",
            "Hong Kong": "Asia"
        }
        return continent_mapping.get(country, "Unknown")
    
    def create_gold_place(self, silver_place: SilverPlace, enrichment: Dict[str, Any]) -> GoldPlace:
        """Create Gold place từ Silver place và enrichment data"""
        return GoldPlace(
            # Inherit from SilverPlace
            u_key=silver_place.u_key,
            source_id=silver_place.source_id,
            name=silver_place.name,
            name_en=silver_place.name_en,
            category=silver_place.category,
            subcategory=silver_place.subcategory,
            city=silver_place.city,
            country=silver_place.country,
            address=silver_place.address,
            location=silver_place.location,
            tags=silver_place.tags,
            source=silver_place.source,
            language=silver_place.language,
            ingestion_at=silver_place.ingestion_at,
            processed_at=silver_place.processed_at,
            raw_file=silver_place.raw_file,
            status=ProcessingStatus.ENRICHED,
            
            # Gold-specific fields
            id=f"gold_{silver_place.u_key}",
            rating=None,  # Will be populated from other sources
            review_count=None,  # Will be populated from other sources
            business_metrics=enrichment["business_metrics"],
            search_keywords=enrichment["search_keywords"],
            embedding_text=enrichment["embedding_text"],
            region_hierarchy=enrichment["region_hierarchy"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def process_city_category(self, city: str, category: POICategory) -> Dict[str, Any]:
        """Process Silver data cho city và category sang Gold layer"""
        silver_files = self.get_silver_files(city, category)
        
        if not silver_files:
            return {
                "city": city,
                "category": category.value,
                "total_files": 0,
                "processed_files": 0,
                "total_places": 0,
                "duplicates_removed": 0,
                "gold_places": 0,
                "errors": []
            }
        
        results = {
            "city": city,
            "category": category.value,
            "total_files": len(silver_files),
            "processed_files": 0,
            "total_places": 0,
            "duplicates_removed": 0,
            "gold_places": 0,
            "errors": []
        }
        
        all_silver_places = []
        
        # Load all Silver places
        for silver_file in silver_files:
            places = self.load_silver_places(silver_file)
            all_silver_places.extend(places)
            results["processed_files"] += 1
        
        results["total_places"] = len(all_silver_places)
        
        if not all_silver_places:
            logger.warning(f"No Silver places found for {city} - {category.value}")
            return results
        
        # Detect and merge duplicates
        duplicate_groups = self.detect_duplicates(all_silver_places)
        merged_places = self.merge_duplicates(duplicate_groups)
        
        # Count duplicates removed
        duplicates_removed = len(all_silver_places) - len(merged_places)
        results["duplicates_removed"] = duplicates_removed
        
        logger.info(f"🔍 Found {len(duplicate_groups)} duplicate groups")
        logger.info(f"🔄 Removed {duplicates_removed} duplicates")
        
        # Enrich and convert to Gold places
        gold_places = []
        for silver_place in merged_places:
            try:
                enrichment = self.enrich_silver_place(silver_place)
                gold_place = self.create_gold_place(silver_place, enrichment)
                gold_places.append(gold_place)
            except Exception as e:
                logger.error(f"Error processing Silver place {silver_place.u_key}: {e}")
                results["errors"].append(f"{silver_place.u_key}: {str(e)}")
        
        results["gold_places"] = len(gold_places)
        
        # Save to Gold layer
        if gold_places:
            success = self._save_gold_places(city, category, gold_places)
            if not success:
                results["errors"].append("Failed to save Gold places")
        
        logger.info(f"✅ Processed {city} - {category.value}: {len(gold_places)} Gold places")
        
        return results
    
    def _save_gold_places(self, city: str, category: POICategory, gold_places: List[GoldPlace]) -> bool:
        """Save Gold places sang parquet và JSON formats"""
        try:
            # Create Gold directory
            gold_dir = self.gold_path / "osm"
            gold_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            
            # Save as JSON (for debugging)
            json_file = gold_dir / f"{category.value}_master_{timestamp}.json"
            gold_data = {
                "metadata": {
                    "city": city,
                    "category": category.value,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "record_count": len(gold_places),
                    "source": "silver_layer"
                },
                "places": [place.dict() for place in gold_places]
            }
            
            json_success = save_json_file(gold_data, json_file)
            
            # Save as Parquet (for analytics)
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
                
                # Convert to DataFrame
                df_data = []
                for place in gold_places:
                    row = place.dict()
                    # Flatten nested objects for Parquet
                    row.update(row.pop('business_metrics', {}))
                    row.update(row.pop('region_hierarchy', {}))
                    row['search_keywords'] = ','.join(row.get('search_keywords', []))
                    df_data.append(row)
                
                df = pd.DataFrame(df_data)
                
                # Save as Parquet
                parquet_file = gold_dir / f"{category.value}_master.parquet"
                table = pa.Table.from_pandas(df)
                pq.write_table(table, parquet_file)
                
                logger.info(f"💾 Saved Gold data: {parquet_file}")
                
            except ImportError:
                logger.warning("⚠️ PyArrow not available, skipping Parquet export")
            
            return json_success
            
        except Exception as e:
            logger.error(f"❌ Error saving Gold places: {e}")
            return False
    
    def process_all(self, cities: Optional[List[str]] = None, categories: Optional[List[POICategory]] = None) -> Dict[str, Any]:
        """Process tất cả Silver data sang Gold layer"""
        
        # Get available cities and categories
        available_cities = []
        if self.silver_path.exists():
            for city_dir in (self.silver_path / "osm").iterdir():
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
        
        logger.info(f"🚀 Starting Silver processing for {len(target_cities)} cities, {len(target_categories)} categories")
        
        summary = {
            "total_jobs": len(target_cities) * len(target_categories),
            "processed_jobs": 0,
            "failed_jobs": 0,
            "total_silver_places": 0,
            "total_gold_places": 0,
            "total_duplicates_removed": 0,
            "city_results": {}
        }
        
        for city in target_cities:
            city_summary = {
                "categories": {},
                "total_places": 0,
                "gold_places": 0,
                "duplicates_removed": 0,
                "processed_files": 0,
                "failed_files": 0
            }
            
            for category in target_categories:
                result = self.process_city_category(city, category)
                
                if result["gold_places"] > 0:
                    summary["processed_jobs"] += 1
                else:
                    summary["failed_jobs"] += 1
                
                city_summary["categories"][category.value] = result
                city_summary["total_places"] += result["total_places"]
                city_summary["gold_places"] += result["gold_places"]
                city_summary["duplicates_removed"] += result["duplicates_removed"]
                city_summary["processed_files"] += result["processed_files"]
                city_summary["failed_files"] += len(result["errors"])
            
            summary["city_results"][city] = city_summary
            summary["total_silver_places"] += city_summary["total_places"]
            summary["total_gold_places"] += city_summary["gold_places"]
            summary["total_duplicates_removed"] += city_summary["duplicates_removed"]
        
        logger.info("=" * 70)
        logger.info("📊 SILVER PROCESSING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total jobs: {summary['total_jobs']}")
        logger.info(f"Processed: {summary['processed_jobs']}")
        logger.info(f"Failed: {summary['failed_jobs']}")
        logger.info(f"Success rate: {summary['processed_jobs']/summary['total_jobs']*100:.1f}%")
        logger.info(f"Total Silver places: {summary['total_silver_places']}")
        logger.info(f"Total Gold places: {summary['total_gold_places']}")
        logger.info(f"Total duplicates removed: {summary['total_duplicates_removed']}")
        
        return summary


def main():
    """Main function để run Silver processing"""
    processor = SilverProcessor()
    results = processor.process_all()
    return results


if __name__ == "__main__":
    main()
