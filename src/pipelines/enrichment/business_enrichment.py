"""
Business Enrichment
====================

Business enrichment cho POI data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/enrichment/business_enrichment.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BusinessScorer:
    """
    Score POI data với business metrics.
    
    Scores:
    - Popularity score
    - Revenue potential
    - Competition level
    - Business viability
    """
    
    def __init__(self):
        self.category_multipliers = {
            "restaurant": 1.2,
            "hotel": 1.5,
            "tourist_attraction": 1.3,
            "cafe": 1.0,
            "shopping_mall": 1.4,
            "park": 0.8,
            "museum": 0.9,
        }
        logger.info("BusinessScorer initialized")
    
    def enrich(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một record với business scores.
        
        Args:
            record: POI record
            
        Returns:
            Enriched record
        """
        enriched = record.copy()
        
        # Calculate popularity score
        popularity = self._calculate_popularity(record)
        enriched["popularity_score"] = popularity
        
        # Calculate business viability
        viability = self._calculate_viability(record)
        enriched["business_viability"] = viability
        
        # Calculate revenue potential
        revenue = self._estimate_revenue(record)
        enriched["revenue_potential"] = revenue
        
        # Calculate competition level
        competition = self._estimate_competition(record)
        enriched["competition_level"] = competition
        
        # Add business enrichment timestamp
        enriched["business_enriched"] = True
        enriched["business_enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched
    
    def enrich_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich nhiều records."""
        return [self.enrich(r) for r in records]
    
    def _calculate_popularity(self, record: Dict[str, Any]) -> float:
        """Calculate popularity score (0-100)."""
        score = 0.0
        
        # Rating contribution (max 40 points)
        rating = record.get("rating", 0)
        if rating:
            score += (rating / 5) * 40
        
        # Review count contribution (max 30 points)
        review_count = record.get("user_ratings_total", 0)
        if review_count:
            # Logarithmic scale for review count
            import math
            score += min(math.log10(review_count + 1) * 10, 30)
        
        # Category multiplier (max 30 points)
        category = record.get("primary_category", "")
        multiplier = self.category_multipliers.get(category, 1.0)
        score += multiplier * 20
        
        return round(min(score, 100), 1)
    
    def _calculate_viability(self, record: Dict[str, Any]) -> float:
        """Calculate business viability (0-100)."""
        score = 50.0  # Base score
        
        # Add points for completeness
        required_fields = ["name", "location", "address", "rating"]
        for field in required_fields:
            if record.get(field):
                score += 10
        
        # Subtract for low ratings
        rating = record.get("rating", 0)
        if rating and rating < 3.0:
            score -= 20
        
        return round(max(min(score, 100), 0), 1)
    
    def _estimate_revenue(self, record: Dict[str, Any]) -> str:
        """Estimate revenue potential."""
        popularity = record.get("popularity_score", 50)
        category = record.get("primary_category", "")
        
        # Adjust based on category
        multiplier = self.category_multipliers.get(category, 1.0)
        adjusted_score = popularity * multiplier
        
        if adjusted_score >= 80:
            return "high"
        elif adjusted_score >= 50:
            return "medium"
        else:
            return "low"
    
    def _estimate_competition(self, record: Dict[str, Any]) -> str:
        """Estimate competition level."""
        category = record.get("primary_category", "")
        
        # High competition categories
        high_comp = ["restaurant", "cafe", "hotel"]
        # Medium competition categories
        medium_comp = ["shopping_mall", "tourist_attraction"]
        
        if category in high_comp:
            return "high"
        elif category in medium_comp:
            return "medium"
        else:
            return "low"
