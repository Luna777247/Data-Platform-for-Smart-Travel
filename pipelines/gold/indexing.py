"""
Gold Layer Indexing
====================

Index creation cho Gold layer data.
Theo RECOMMENDED_STRUCTURE.md - pipelines/gold/indexing.py
"""

import logging
from typing import Dict, Any, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class IndexManager:
    """
    Manage MongoDB indexes cho Gold layer.
    
    Indexes created:
    1. Geospatial index (2dsphere)
    2. Text index (searchable fields)
    3. Compound indexes (common queries)
    4. Single field indexes
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.collection_name = "gold_pois"
        logger.info("IndexManager initialized")
    
    async def create_all_indexes(self) -> Dict[str, bool]:
        """
        Create all required indexes.
        
        Returns:
            Dict of index name -> success status
        """
        if not self.db:
            logger.error("Database not available for indexing")
            return {}
        
        results = {}
        
        # Geospatial index
        results["location_2dsphere"] = await self._create_geospatial_index()
        
        # Text search index
        results["text_search"] = await self._create_text_index()
        
        # Compound indexes
        results["category_city"] = await self._create_compound_index(
            [("primary_category", 1), ("city", 1)],
            "category_city_idx"
        )
        
        results["rating_city"] = await self._create_compound_index(
            [("rating", -1), ("city", 1)],
            "rating_city_idx"
        )
        
        # Single field indexes
        results["place_id"] = await self._create_single_index("place_id", unique=True)
        results["city"] = await self._create_single_index("city")
        results["quality_score"] = await self._create_single_index("quality_score")
        results["popularity_score"] = await self._create_single_index("popularity_score")
        
        logger.info(f"Index creation results: {results}")
        return results
    
    async def _create_geospatial_index(self) -> bool:
        """Create 2dsphere index on location."""
        try:
            await self.db[self.collection_name].create_index(
                [("location", "2dsphere")],
                name="location_geospatial"
            )
            logger.info("Created geospatial index")
            return True
        except Exception as e:
            logger.error(f"Failed to create geospatial index: {e}")
            return False
    
    async def _create_text_index(self) -> bool:
        """Create text index for search."""
        try:
            # Create text index on searchable fields
            await self.db[self.collection_name].create_index(
                [
                    ("name", "text"),
                    ("searchable_text", "text"),
                    ("keywords", "text")
                ],
                name="text_search",
                default_language="none"
            )
            logger.info("Created text search index")
            return True
        except Exception as e:
            logger.error(f"Failed to create text index: {e}")
            return False
    
    async def _create_compound_index(
        self,
        fields: List[tuple],
        name: str
    ) -> bool:
        """Create compound index."""
        try:
            await self.db[self.collection_name].create_index(
                fields,
                name=name
            )
            logger.info(f"Created compound index: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create compound index {name}: {e}")
            return False
    
    async def _create_single_index(
        self,
        field: str,
        unique: bool = False
    ) -> bool:
        """Create single field index."""
        try:
            await self.db[self.collection_name].create_index(
                field,
                unique=unique,
                name=f"{field}_idx"
            )
            logger.info(f"Created index on {field} (unique={unique})")
            return True
        except Exception as e:
            logger.error(f"Failed to create index on {field}: {e}")
            return False
    
    async def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes trong collection."""
        if not self.db:
            return []
        
        try:
            indexes = await self.db[self.collection_name].list_indexes().to_list(None)
            return indexes
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []
    
    async def drop_index(self, name: str) -> bool:
        """Drop một index."""
        if not self.db:
            return False
        
        try:
            await self.db[self.collection_name].drop_index(name)
            logger.info(f"Dropped index: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop index {name}: {e}")
            return False
    
    async def drop_all_indexes(self) -> bool:
        """Drop all indexes (except _id)."""
        if not self.db:
            return False
        
        try:
            await self.db[self.collection_name].drop_indexes()
            logger.info("Dropped all indexes")
            return True
        except Exception as e:
            logger.error(f"Failed to drop indexes: {e}")
            return False
