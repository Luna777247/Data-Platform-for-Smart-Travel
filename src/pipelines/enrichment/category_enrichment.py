"""
Category Enrichment
==================

Category enrichment cho POI data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/enrichment/category_enrichment.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CategoryEnricher:
    """
    Enrich POI data với category information.
    
    Enrichments:
    - Category classification
    - Subcategory assignment
    - Category keywords
    - Icon mapping
    """
    
    def __init__(self):
        self.category_mappings = self._load_category_mappings()
        self.icon_mappings = self._load_icon_mappings()
        logger.info("CategoryEnricher initialized")
    
    def _load_category_mappings(self) -> Dict[str, str]:
        """Load category mappings từ keywords."""
        return {
            # Restaurant keywords
            "restaurant": "restaurant",
            "dining": "restaurant",
            "food": "restaurant",
            "eatery": "restaurant",
            "cafe": "cafe",
            "coffee": "cafe",
            
            # Hotel keywords
            "hotel": "hotel",
            "lodging": "hotel",
            "accommodation": "hotel",
            "motel": "hotel",
            
            # Attraction keywords
            "attraction": "tourist_attraction",
            "sightseeing": "tourist_attraction",
            "landmark": "tourist_attraction",
            "monument": "tourist_attraction",
            
            # Shopping keywords
            "shopping": "shopping_mall",
            "shop": "shopping_mall",
            "store": "shopping_mall",
            "mall": "shopping_mall",
            
            # Nature keywords
            "park": "park",
            "garden": "park",
            "nature": "park",
        }
    
    def _load_icon_mappings(self) -> Dict[str, str]:
        """Load icon mappings cho categories."""
        return {
            "restaurant": "🍽️",
            "cafe": "☕",
            "hotel": "🏨",
            "tourist_attraction": "🎯",
            "shopping_mall": "🛍️",
            "park": "🌳",
            "museum": "🏛️",
            "cinema": "🎬",
        }
    
    def enrich(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một record với category data.
        
        Args:
            record: POI record
            
        Returns:
            Enriched record
        """
        enriched = record.copy()
        
        # Classify category from name/keywords
        name = record.get("name", "").lower()
        categories = record.get("categories", [])
        
        # Get primary category
        primary_category = self._classify_category(name, categories)
        enriched["primary_category"] = primary_category
        
        # Get icon
        enriched["category_icon"] = self._get_icon(primary_category)
        
        # Add category keywords
        enriched["category_keywords"] = self._extract_keywords(name, primary_category)
        
        # Add category enrichment timestamp
        enriched["category_enriched"] = True
        enriched["category_enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched
    
    def enrich_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich nhiều records."""
        return [self.enrich(r) for r in records]
    
    def _classify_category(
        self,
        name: str,
        categories: List[str]
    ) -> str:
        """Classify POI into primary category."""
        # Check existing categories first
        if categories:
            for cat in categories:
                cat_lower = cat.lower()
                if cat_lower in self.category_mappings:
                    return self.category_mappings[cat_lower]
        
        # Check name for keywords
        name_lower = name.lower()
        for keyword, category in self.category_mappings.items():
            if keyword in name_lower:
                return category
        
        return "uncategorized"
    
    def _get_icon(self, category: str) -> str:
        """Get icon for category."""
        return self.icon_mappings.get(category, "📍")
    
    def _extract_keywords(
        self,
        name: str,
        category: str
    ) -> List[str]:
        """Extract category-related keywords."""
        keywords = []
        name_lower = name.lower()
        
        # Add category-related keywords
        for keyword, mapped_cat in self.category_mappings.items():
            if mapped_cat == category and keyword in name_lower:
                keywords.append(keyword)
        
        return list(set(keywords))[:5]  # Limit to 5 unique keywords
