"""
Gold Layer Enrichment
======================

Data enrichment cho Gold layer.
Theo RECOMMENDED_STRUCTURE.md - pipelines/gold/enrichment.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GoldEnricher:
    """
    Enrich Gold layer data với additional computed fields.
    
    Enrichments:
    1. Keywords extraction
    2. Searchable text generation
    3. Popularity scoring
    4. Quality badges
    5. Feature flags
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_keywords = self.config.get("enable_keywords", True)
        self.enable_embeddings = self.config.get("enable_embeddings", False)
        logger.info("GoldEnricher initialized")
    
    def enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một Gold record.
        
        Args:
            record: Gold POI record
            
        Returns:
            Enriched record
        """
        enriched = record.copy()
        
        # Generate keywords
        if self.enable_keywords:
            enriched["keywords"] = self._extract_keywords(record)
        
        # Generate searchable text
        enriched["searchable_text"] = self._generate_searchable_text(record)
        
        # Calculate popularity score
        enriched["popularity_score"] = self._calculate_popularity(record)
        
        # Assign quality badges
        enriched["badges"] = self._assign_badges(record)
        
        # Set feature flags
        enriched["features"] = self._determine_features(record)
        
        # Add enrichment metadata
        enriched["enriched"] = True
        enriched["enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched
    
    def enrich_records(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich nhiều records."""
        return [self.enrich_record(r) for r in records]
    
    def _extract_keywords(self, record: Dict[str, Any]) -> List[str]:
        """Extract keywords từ record."""
        keywords = set()
        
        # From name
        name = record.get("name", "")
        if name:
            # Simple keyword extraction
            words = name.lower().split()
            keywords.update(w for w in words if len(w) > 3)
        
        # From categories
        categories = record.get("categories", [])
        if categories:
            if isinstance(categories, str):
                keywords.add(categories.lower())
            else:
                keywords.update(c.lower() for c in categories if isinstance(c, str))
        
        # From city/address
        city = record.get("city", "")
        if city:
            keywords.add(city.lower())
        
        # Add category-specific keywords
        primary = record.get("primary_category", "")
        if primary:
            keywords.add(primary.lower())
        
        return list(keywords)[:20]  # Limit to 20 keywords
    
    def _generate_searchable_text(self, record: Dict[str, Any]) -> str:
        """Generate searchable text cho full-text search."""
        parts = []
        
        # Name
        if record.get("name"):
            parts.append(record["name"])
        
        # Categories
        categories = record.get("categories", [])
        if categories:
            if isinstance(categories, list):
                parts.extend(categories)
            else:
                parts.append(str(categories))
        
        # Address
        address = record.get("address", {})
        if address:
            if isinstance(address, dict):
                street = address.get("street", "")
                district = address.get("district", "")
                if street:
                    parts.append(street)
                if district:
                    parts.append(district)
            else:
                parts.append(str(address))
        
        # City
        if record.get("city"):
            parts.append(record["city"])
        
        # Keywords (if already extracted)
        keywords = record.get("keywords", [])
        if keywords:
            parts.extend(keywords)
        
        return " ".join(str(p) for p in parts if p)
    
    def _calculate_popularity(self, record: Dict[str, Any]) -> float:
        """
        Calculate popularity score (0-100).
        
        Based on:
        - Rating score
        - Review count
        - Price level (higher = more popular)
        - Photo count
        """
        score = 0.0
        
        # Rating contribution (max 40)
        rating = record.get("rating", 0)
        if rating > 0:
            score += (rating / 5.0) * 40
        
        # Review count contribution (max 30)
        review_count = record.get("user_ratings_total", 0)
        if review_count > 0:
            # Log scale for review count
            import math
            score += min(math.log10(review_count + 1) * 10, 30)
        
        # Price level contribution (max 10)
        price_level = record.get("price_level", 0)
        if price_level > 0:
            score += price_level * 2.5
        
        # Photo count contribution (max 20)
        photos = record.get("photos", [])
        photo_count = len(photos) if isinstance(photos, list) else 0
        if photo_count > 0:
            score += min(photo_count * 2, 20)
        
        return round(score, 2)
    
    def _assign_badges(self, record: Dict[str, Any]) -> List[str]:
        """Assign quality badges dựa trên data quality."""
        badges = []
        
        # Top rated badge
        rating = record.get("rating", 0)
        if rating >= 4.5:
            badges.append("top_rated")
        elif rating >= 4.0:
            badges.append("highly_rated")
        
        # Popular badge
        review_count = record.get("user_ratings_total", 0)
        if review_count >= 1000:
            badges.append("very_popular")
        elif review_count >= 100:
            badges.append("popular")
        
        # Verified badge
        quality_score = record.get("quality_score", 0)
        if quality_score >= 0.9:
            badges.append("verified")
        
        # Complete info badge
        has_phone = bool(record.get("phone"))
        has_website = bool(record.get("website"))
        has_hours = bool(record.get("opening_hours"))
        has_photos = bool(record.get("photos"))
        
        if has_phone and has_website and has_hours:
            badges.append("complete_info")
        
        if has_photos:
            badges.append("has_photos")
        
        return badges
    
    def _determine_features(self, record: Dict[str, Any]) -> Dict[str, bool]:
        """Determine feature flags cho record."""
        features = {
            "has_phone": bool(record.get("phone")),
            "has_website": bool(record.get("website")),
            "has_opening_hours": bool(record.get("opening_hours")),
            "has_photos": bool(record.get("photos")),
            "has_rating": record.get("rating", 0) > 0,
            "is_premium": record.get("quality_score", 0) >= 0.9,
            "is_master": record.get("is_master", False),
        }
        
        return features
