"""
Gold Layer Processor
=====================

Gold layer processing cho Smart Tourism Platform.
Theo RECOMMENDED_STRUCTURE.md - pipelines/gold/gold_processor.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GoldProcessor:
    """
    Process Silver data thành Gold layer (Master POI).
    
    Gold layer characteristics:
    - Highest quality data
    - Enriched with additional info
    - Ready for API consumption
    - Business-ready format
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.quality_threshold = self.config.get("quality_threshold", 0.8)
        logger.info("GoldProcessor initialized")
    
    def process_to_gold(
        self,
        silver_records: List[Dict[str, Any]],
        city: str
    ) -> List[Dict[str, Any]]:
        """
        Process Silver records thành Gold Master POIs.
        
        Args:
            silver_records: List of Silver records
            city: Target city
            
        Returns:
            List of Gold Master POI records
        """
        logger.info(f"Processing {len(silver_records)} Silver records to Gold")
        
        gold_records = []
        
        for record in silver_records:
            # Check quality threshold
            if not self._meets_quality_threshold(record):
                continue
            
            # Transform to Gold format
            gold_record = self._transform_to_gold(record, city)
            
            if gold_record:
                gold_records.append(gold_record)
        
        logger.info(f"Created {len(gold_records)} Gold records")
        return gold_records
    
    def _meets_quality_threshold(self, record: Dict[str, Any]) -> bool:
        """Check if record meets Gold quality requirements."""
        quality_score = record.get("quality_score", 0)
        return quality_score >= self.quality_threshold
    
    def _transform_to_gold(
        self,
        record: Dict[str, Any],
        city: str
    ) -> Optional[Dict[str, Any]]:
        """Transform Silver record thành Gold format."""
        try:
            gold = {
                # Core identity
                "place_id": record.get("place_id"),
                "name": record.get("name"),
                
                # Location
                "location": record.get("location", {}),
                "address": record.get("address", {}),
                "city": city,
                
                # Categorization
                "primary_category": self._get_primary_category(record),
                "categories": record.get("categories", []),
                
                # Business info
                "phone": record.get("phone"),
                "website": record.get("website"),
                "opening_hours": record.get("opening_hours"),
                
                # Ratings
                "rating": record.get("rating"),
                "user_ratings_total": record.get("user_ratings_total"),
                "price_level": record.get("price_level"),
                
                # Media
                "photos": record.get("photos", []),
                "icon": record.get("icon"),
                
                # Metadata
                "source": record.get("source", "aggregated"),
                "sources": record.get("duplicate_source_ids", [record.get("place_id")]),
                "quality_score": record.get("quality_score", 0),
                
                # Processing metadata
                "created_at": record.get("ingested_at"),
                "updated_at": datetime.utcnow().isoformat(),
                "layer": "gold",
                "version": "1.0"
            }
            
            # Remove None values
            gold = {k: v for k, v in gold.items() if v is not None}
            
            return gold
            
        except Exception as e:
            logger.error(f"Error transforming record: {e}")
            return None
    
    def _get_primary_category(self, record: Dict[str, Any]) -> str:
        """Get primary category from record."""
        categories = record.get("categories", [])
        
        if not categories:
            return "uncategorized"
        
        if isinstance(categories, list) and len(categories) > 0:
            return categories[0]
        
        return str(categories)
    
    def create_master_poi(
        self,
        duplicates: List[Dict[str, Any]],
        city: str
    ) -> Dict[str, Any]:
        """
        Create Master POI từ multiple duplicate sources.
        
        Args:
            duplicates: List of duplicate POI records
            city: Target city
            
        Returns:
            Master POI record
        """
        if not duplicates:
            return {}
        
        # Start with highest quality record
        master = max(duplicates, key=lambda x: x.get("quality_score", 0)).copy()
        
        # Collect all source IDs
        all_sources = [d.get("place_id") for d in duplicates if d.get("place_id")]
        master["sources"] = all_sources
        master["source_count"] = len(all_sources)
        
        # Aggregate ratings
        ratings = [d.get("rating", 0) for d in duplicates if d.get("rating", 0) > 0]
        if ratings:
            master["rating"] = sum(ratings) / len(ratings)
        
        review_counts = [d.get("user_ratings_total", 0) for d in duplicates]
        master["user_ratings_total"] = sum(review_counts)
        
        # Collect all photos
        all_photos = []
        for d in duplicates:
            photos = d.get("photos", [])
            if photos:
                all_photos.extend(photos)
        
        if all_photos:
            master["photos"] = all_photos[:10]  # Limit to 10 photos
        
        # Set master metadata
        master["is_master"] = True
        master["city"] = city
        master["layer"] = "gold"
        master["updated_at"] = datetime.utcnow().isoformat()
        
        return master
