"""
Deduplication Module
====================

Deduplication logic cho Silver layer.
Theo RECOMMENDED_STRUCTURE.md - pipelines/silver/deduplication.py
"""

import logging
import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
from datetime import datetime

from src.utils.geo_utils import calculate_distance

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detect và merge duplicate POIs trong Silver layer.
    
    Algorithms:
    1. Exact match - Same name + coordinates
    2. Fuzzy match - Similar name trong radius
    3. Spatial match - Same location, different sources
    """
    
    def __init__(
        self,
        exact_match_threshold: float = 0.001,  # ~100m
        fuzzy_match_threshold: float = 0.05,   # ~5km
        name_similarity_threshold: float = 0.8
    ):
        self.exact_match_threshold = exact_match_threshold
        self.fuzzy_match_threshold = fuzzy_match_threshold
        self.name_similarity_threshold = name_similarity_threshold
        logger.info("DuplicateDetector initialized")
    
    def find_exact_duplicates(
        self,
        records: List[Dict[str, Any]]
    ) -> List[List[int]]:
        """
        Tìm exact duplicates dựa trên name + coordinates.
        
        Args:
            records: List of POI records
            
        Returns:
            List of duplicate groups (indices)
        """
        # Tạo hash key từ name + coordinates
        hash_groups: Dict[str, List[int]] = defaultdict(list)
        
        for idx, record in enumerate(records):
            name = record.get("name", "").lower().strip()
            lat = record.get("location", {}).get("lat", 0)
            lng = record.get("location", {}).get("lng", 0)
            
            # Round coordinates để group nearby points
            lat_rounded = round(lat, 4)  # ~10m precision
            lng_rounded = round(lng, 4)
            
            hash_key = f"{name}|{lat_rounded}|{lng_rounded}"
            hash_groups[hash_key].append(idx)
        
        # Filter groups with > 1 record
        duplicates = [
            indices for indices in hash_groups.values()
            if len(indices) > 1
        ]
        
        logger.info(f"Found {len(duplicates)} exact duplicate groups")
        return duplicates
    
    def find_fuzzy_duplicates(
        self,
        records: List[Dict[str, Any]]
    ) -> List[List[int]]:
        """
        Tìm fuzzy duplicates trong radius với similar names.
        
        Args:
            records: List of POI records
            
        Returns:
            List of duplicate groups (indices)
        """
        duplicates = []
        processed = set()
        
        for i, record1 in enumerate(records):
            if i in processed:
                continue
            
            group = [i]
            name1 = record1.get("name", "").lower()
            lat1 = record1.get("location", {}).get("lat", 0)
            lng1 = record1.get("location", {}).get("lng", 0)
            
            for j, record2 in enumerate(records[i+1:], start=i+1):
                if j in processed:
                    continue
                
                name2 = record2.get("name", "").lower()
                lat2 = record2.get("location", {}).get("lat", 0)
                lng2 = record2.get("location", {}).get("lng", 0)
                
                # Check distance
                distance = calculate_distance(lat1, lng1, lat2, lng2)
                
                if distance <= self.fuzzy_match_threshold:
                    # Check name similarity
                    similarity = self._calculate_name_similarity(name1, name2)
                    
                    if similarity >= self.name_similarity_threshold:
                        group.append(j)
                        processed.add(j)
            
            if len(group) > 1:
                duplicates.append(group)
                processed.update(group)
        
        logger.info(f"Found {len(duplicates)} fuzzy duplicate groups")
        return duplicates
    
    def merge_duplicates(
        self,
        records: List[Dict[str, Any]],
        duplicate_groups: List[List[int]]
    ) -> List[Dict[str, Any]]:
        """
        Merge duplicate records into single canonical record.
        
        Args:
            records: Original records
            duplicate_groups: Groups of duplicate indices
            
        Returns:
            Deduplicated records
        """
        # Track which records to keep/remove
        to_remove = set()
        merged_records = []
        
        for group in duplicate_groups:
            # Merge group into single record
            merged = self._merge_group([records[i] for i in group])
            
            # Add merged record
            merged_records.append(merged)
            
            # Mark original records for removal
            to_remove.update(group)
        
        # Add non-duplicate records
        for i, record in enumerate(records):
            if i not in to_remove:
                merged_records.append(record)
        
        logger.info(
            f"Merged {len(duplicate_groups)} groups, "
            f"removed {len(to_remove)} duplicates"
        )
        return merged_records
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity score between two names.
        
        Uses Jaccard similarity on character n-grams.
        """
        def get_ngrams(text: str, n: int = 2) -> Set[str]:
            text = text.lower()
            return {text[i:i+n] for i in range(len(text)-n+1)}
        
        ngrams1 = get_ngrams(name1)
        ngrams2 = get_ngrams(name2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def _merge_group(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a group of duplicate records."""
        if not records:
            return {}
        
        # Start with first record
        merged = records[0].copy()
        
        # Collect all source IDs
        source_ids = [r.get("place_id", "") for r in records]
        merged["duplicate_source_ids"] = source_ids
        
        # Merge ratings (weighted average)
        ratings = [r.get("rating", 0) for r in records if r.get("rating", 0) > 0]
        if ratings:
            merged["rating"] = sum(ratings) / len(ratings)
            merged["user_ratings_total"] = sum(
                r.get("user_ratings_total", 0) for r in records
            )
        
        # Merge review counts
        review_counts = [
            r.get("user_ratings_total", 0)
            for r in records
            if r.get("user_ratings_total", 0) > 0
        ]
        if review_counts:
            merged["user_ratings_total"] = max(review_counts)
        
        # Collect all categories
        all_categories = set()
        for r in records:
            cats = r.get("categories", [])
            if isinstance(cats, list):
                all_categories.update(cats)
            elif isinstance(cats, str):
                all_categories.add(cats)
        
        if all_categories:
            merged["categories"] = list(all_categories)
        
        # Use best available data
        for r in records[1:]:
            # Prefer records with more complete data
            if not merged.get("phone") and r.get("phone"):
                merged["phone"] = r["phone"]
            if not merged.get("website") and r.get("website"):
                merged["website"] = r["website"]
            if not merged.get("opening_hours") and r.get("opening_hours"):
                merged["opening_hours"] = r["opening_hours"]
            if not merged.get("photos") and r.get("photos"):
                merged["photos"] = r["photos"]
        
        # Mark as merged
        merged["deduplicated"] = True
        merged["deduplication_count"] = len(records)
        merged["deduplication_timestamp"] = datetime.utcnow().isoformat()
        
        return merged
    
    def deduplicate(
        self,
        records: List[Dict[str, Any]],
        method: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Main deduplication entry point.
        
        Args:
            records: Input records
            method: "exact", "fuzzy", or "both"
            
        Returns:
            Deduplicated records
        """
        if not records:
            return []
        
        logger.info(f"Starting deduplication of {len(records)} records")
        
        all_groups = []
        
        if method in ["exact", "both"]:
            exact_groups = self.find_exact_duplicates(records)
            all_groups.extend(exact_groups)
        
        if method in ["fuzzy", "both"]:
            fuzzy_groups = self.find_fuzzy_duplicates(records)
            all_groups.extend(fuzzy_groups)
        
        if all_groups:
            result = self.merge_duplicates(records, all_groups)
        else:
            result = records
        
        logger.info(f"Deduplication complete: {len(records)} -> {len(result)} records")
        return result
