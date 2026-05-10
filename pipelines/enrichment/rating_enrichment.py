"""
Rating Enrichment
================

Rating enrichment cho pipeline data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/enrichment/rating_enrichment.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RatingEnricher:
    """
    Enrich POI data với rating calculations.
    
    Enrichments:
    - Rating distribution analysis
    - Popularity score
    - Rating trends
    - Sentiment indicators
    """
    
    def __init__(self):
        self.rating_weights = {
            "google": 1.0,
            "tripadvisor": 0.9,
            "osm": 0.8,
            "manual": 1.0
        }
        logger.info("RatingEnricher initialized")
    
    def enrich(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich một record với rating data.
        
        Args:
            record: POI record
            
        Returns:
            Enriched record
        """
        enriched = record.copy()
        
        rating = record.get("rating")
        review_count = record.get("user_ratings_total", 0)
        
        if rating is not None:
            # Calculate weighted rating
            source = record.get("source", "unknown")
            weight = self.rating_weights.get(source, 0.5)
            enriched["weighted_rating"] = rating * weight
            
            # Add rating category
            enriched["rating_category"] = self._categorize_rating(rating)
            
            # Calculate confidence
            enriched["rating_confidence"] = self._calculate_confidence(
                rating, review_count
            )
            
            # Add percentile info if available
            enriched["rating_percentile"] = self._estimate_percentile(rating)
        
        if review_count > 0:
            # Calculate popularity tier
            enriched["popularity_tier"] = self._calculate_popularity_tier(
                review_count
            )
            
            # Add engagement score
            enriched["engagement_score"] = self._calculate_engagement(
                rating, review_count
            )
        
        enriched["rating_enriched"] = True
        enriched["rating_enriched_at"] = datetime.utcnow().isoformat()
        
        return enriched
    
    def enrich_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich nhiều records."""
        return [self.enrich(r) for r in records]
    
    def aggregate_ratings(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate ratings từ nhiều sources.
        
        Args:
            records: List of records with ratings
            
        Returns:
            Aggregated rating statistics
        """
        ratings = []
        review_counts = []
        
        for r in records:
            rating = r.get("rating")
            if rating is not None:
                source = r.get("source", "unknown")
                weight = self.rating_weights.get(source, 0.5)
                
                ratings.append({
                    "value": rating,
                    "weight": weight,
                    "source": source
                })
            
            count = r.get("user_ratings_total", 0)
            if count > 0:
                review_counts.append(count)
        
        if not ratings:
            return {
                "average_rating": None,
                "weighted_average": None,
                "total_reviews": sum(review_counts),
                "sources": []
            }
        
        # Calculate weighted average
        total_weight = sum(r["weight"] for r in ratings)
        weighted_sum = sum(r["value"] * r["weight"] for r in ratings)
        
        simple_avg = sum(r["value"] for r in ratings) / len(ratings)
        weighted_avg = weighted_sum / total_weight if total_weight > 0 else simple_avg
        
        return {
            "average_rating": round(simple_avg, 2),
            "weighted_average": round(weighted_avg, 2),
            "total_reviews": sum(review_counts),
            "review_count_range": {
                "min": min(review_counts) if review_counts else 0,
                "max": max(review_counts) if review_counts else 0
            },
            "sources": list(set(r["source"] for r in ratings)),
            "rating_count": len(ratings)
        }
    
    def _categorize_rating(self, rating: float) -> str:
        """Categorize rating into descriptive label."""
        if rating >= 4.5:
            return "excellent"
        elif rating >= 4.0:
            return "very_good"
        elif rating >= 3.5:
            return "good"
        elif rating >= 3.0:
            return "average"
        elif rating >= 2.0:
            return "poor"
        else:
            return "very_poor"
    
    def _calculate_confidence(
        self,
        rating: float,
        review_count: int
    ) -> float:
        """
        Calculate confidence score for rating.
        
        Higher review count = higher confidence.
        """
        # Wilson score interval approximation
        if review_count == 0:
            return 0.0
        
        # Confidence increases with review count
        # Max confidence at 100+ reviews
        confidence = min(review_count / 100, 1.0)
        
        return round(confidence, 2)
    
    def _estimate_percentile(self, rating: float) -> str:
        """Estimate rating percentile."""
        # Rough estimate based on typical distribution
        if rating >= 4.5:
            return "top_10"
        elif rating >= 4.0:
            return "top_25"
        elif rating >= 3.5:
            return "top_50"
        elif rating >= 3.0:
            return "below_average"
        else:
            return "bottom_25"
    
    def _calculate_popularity_tier(self, review_count: int) -> str:
        """Calculate popularity tier based on review count."""
        if review_count >= 10000:
            return "very_high"
        elif review_count >= 1000:
            return "high"
        elif review_count >= 100:
            return "medium"
        elif review_count >= 10:
            return "low"
        else:
            return "very_low"
    
    def _calculate_engagement(
        self,
        rating: Optional[float],
        review_count: int
    ) -> float:
        """Calculate engagement score."""
        if rating is None:
            return 0.0
        
        # Engagement = rating * log(review_count + 1)
        import math
        engagement = rating * math.log10(review_count + 1)
        
        return round(min(engagement / 5, 1.0), 2)
