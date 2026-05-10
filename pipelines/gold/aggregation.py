"""
Gold Layer Aggregation
======================

Data aggregation cho Gold layer.
Theo RECOMMENDED_STRUCTURE.md - pipelines/gold/aggregation.py
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Aggregate data for analytics và reporting.
    
    Aggregations:
    1. Category statistics
    2. City statistics
    3. Rating distributions
    4. Quality metrics
    5. Source statistics
    """
    
    def __init__(self):
        logger.info("DataAggregator initialized")
    
    def aggregate_by_category(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate statistics by category.
        
        Returns:
            Dict mapping category to statistics
        """
        stats = defaultdict(lambda: {
            "count": 0,
            "avg_rating": 0.0,
            "total_reviews": 0,
            "avg_quality": 0.0
        })
        
        for record in records:
            category = record.get("primary_category", "uncategorized")
            
            stats[category]["count"] += 1
            
            # Accumulate ratings
            rating = record.get("rating", 0)
            if rating > 0:
                stats[category]["avg_rating"] += rating
            
            # Accumulate reviews
            reviews = record.get("user_ratings_total", 0)
            stats[category]["total_reviews"] += reviews
            
            # Accumulate quality scores
            quality = record.get("quality_score", 0)
            stats[category]["avg_quality"] += quality
        
        # Calculate averages
        for cat, stat in stats.items():
            count = stat["count"]
            if count > 0:
                stat["avg_rating"] = round(stat["avg_rating"] / count, 2)
                stat["avg_quality"] = round(stat["avg_quality"] / count, 2)
        
        return dict(stats)
    
    def aggregate_by_city(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate statistics by city."""
        stats = defaultdict(lambda: {
            "total_pois": 0,
            "categories": set(),
            "avg_rating": 0.0,
            "total_reviews": 0,
            "sources": set()
        })
        
        for record in records:
            city = record.get("city", "unknown")
            
            stats[city]["total_pois"] += 1
            stats[city]["categories"].add(record.get("primary_category", "uncategorized"))
            
            rating = record.get("rating", 0)
            if rating > 0:
                stats[city]["avg_rating"] += rating
            
            reviews = record.get("user_ratings_total", 0)
            stats[city]["total_reviews"] += reviews
            
            source = record.get("source", "unknown")
            stats[city]["sources"].add(source)
        
        # Calculate averages và convert sets
        for city, stat in stats.items():
            count = stat["total_pois"]
            if count > 0:
                stat["avg_rating"] = round(stat["avg_rating"] / count, 2)
            
            stat["category_count"] = len(stat["categories"])
            stat["categories"] = list(stat["categories"])
            stat["source_count"] = len(stat["sources"])
            stat["sources"] = list(stat["sources"])
        
        return dict(stats)
    
    def calculate_rating_distribution(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate rating distribution."""
        distribution = {
            "5_star": 0,
            "4_star": 0,
            "3_star": 0,
            "2_star": 0,
            "1_star": 0,
            "unrated": 0
        }
        
        for record in records:
            rating = record.get("rating", 0)
            
            if rating == 0:
                distribution["unrated"] += 1
            elif rating >= 4.5:
                distribution["5_star"] += 1
            elif rating >= 3.5:
                distribution["4_star"] += 1
            elif rating >= 2.5:
                distribution["3_star"] += 1
            elif rating >= 1.5:
                distribution["2_star"] += 1
            else:
                distribution["1_star"] += 1
        
        return distribution
    
    def calculate_quality_metrics(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        total = len(records)
        
        if total == 0:
            return {}
        
        # Quality score distribution
        high_quality = sum(1 for r in records if r.get("quality_score", 0) >= 0.9)
        medium_quality = sum(1 for r in records if 0.7 <= r.get("quality_score", 0) < 0.9)
        low_quality = sum(1 for r in records if r.get("quality_score", 0) < 0.7)
        
        # Data completeness
        with_phone = sum(1 for r in records if r.get("phone"))
        with_website = sum(1 for r in records if r.get("website"))
        with_hours = sum(1 for r in records if r.get("opening_hours"))
        with_photos = sum(1 for r in records if r.get("photos"))
        
        return {
            "total_records": total,
            "quality_distribution": {
                "high": high_quality,
                "medium": medium_quality,
                "low": low_quality
            },
            "completeness": {
                "phone": round(with_phone / total * 100, 2),
                "website": round(with_website / total * 100, 2),
                "opening_hours": round(with_hours / total * 100, 2),
                "photos": round(with_photos / total * 100, 2)
            },
            "avg_quality_score": round(
                sum(r.get("quality_score", 0) for r in records) / total, 2
            ),
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    def generate_summary_report(
        self,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive summary report."""
        return {
            "total_records": len(records),
            "by_category": self.aggregate_by_category(records),
            "by_city": self.aggregate_by_city(records),
            "rating_distribution": self.calculate_rating_distribution(records),
            "quality_metrics": self.calculate_quality_metrics(records),
            "generated_at": datetime.utcnow().isoformat()
        }
