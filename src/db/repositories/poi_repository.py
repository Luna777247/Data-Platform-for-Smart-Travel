"""
POI Repository
==============

Repository cho Points of Interest data access.
Implement Repository Pattern cho bronze/silver/gold layers.

Supports:
- Bronze layer: Raw data from collectors
- Silver layer: Cleaned and enriched data
- Gold layer: Aggregated business-ready data
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class POIRepository:
    """
    Repository cho POI data across all layers.
    
    Provides unified interface cho bronze/silver/gold data access.
    
    Usage:
        repo = POIRepository(db)
        
        # Store bronze data
        count = await repo.store_bronze_data(city="hanoi", data=raw_data)
        
        # Read silver data
        pois = await repo.get_silver_data(city="hanoi")
        
        # Store gold data
        await repo.store_gold_data(city="hanoi", data=aggregated_data)
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self._collections = {}
        
        # Collection names
        self.BRONZE_COLLECTION = "bronze_places"
        self.SILVER_COLLECTION = "silver_places"
        self.GOLD_COLLECTION = "gold_places"
        
        logger.info("POIRepository initialized")
    
    def _get_collection(self, layer: str):
        """Get MongoDB collection cho layer."""
        if not self.db:
            raise Exception("Database not configured")
        
        collection_map = {
            "bronze": self.BRONZE_COLLECTION,
            "silver": self.SILVER_COLLECTION,
            "gold": self.GOLD_COLLECTION
        }
        
        collection_name = collection_map.get(layer)
        if not collection_name:
            raise ValueError(f"Unknown layer: {layer}")
        
        return self.db[collection_name]
    
    # ========================================================================
    # BRONZE LAYER OPERATIONS
    # ========================================================================
    
    async def store_bronze_data(
        self,
        city: str,
        data: List[Dict[str, Any]]
    ) -> int:
        """
        Store raw data to bronze layer.
        
        Args:
            city: Thành phố
            data: List raw POI data từ collector
            
        Returns:
            Số records đã store
        """
        if not data:
            return 0
        
        collection = self._get_collection("bronze")
        
        # Add metadata
        documents = []
        for item in data:
            doc = {
                **item,
                "_city": city,
                "_layer": "bronze",
                "_ingested_at": datetime.utcnow().isoformat(),
                "_source": item.get("_source", "google_places")
            }
            documents.append(doc)
        
        # Insert many
        try:
            result = await collection.insert_many(documents, ordered=False)
            count = len(result.inserted_ids)
            logger.info(f"Stored {count} bronze records for {city}")
            return count
        except Exception as e:
            logger.error(f"Failed to store bronze data: {e}")
            # Try inserting one by one
            count = 0
            for doc in documents:
                try:
                    await collection.insert_one(doc)
                    count += 1
                except Exception:
                    pass
            return count
    
    async def get_bronze_data(
        self,
        city: str,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """Lấy bronze data cho city."""
        collection = self._get_collection("bronze")
        
        cursor = collection.find({"_city": city}).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_bronze_data(self, city: str) -> int:
        """Đếm bronze records cho city."""
        collection = self._get_collection("bronze")
        return await collection.count_documents({"_city": city})
    
    # ========================================================================
    # SILVER LAYER OPERATIONS
    # ========================================================================
    
    async def store_silver_data(
        self,
        city: str,
        data: List[Dict[str, Any]]
    ) -> int:
        """
        Store cleaned data to silver layer.
        
        Sử dụng upsert để tránh duplicates.
        """
        if not data:
            return 0
        
        collection = self._get_collection("silver")
        
        count = 0
        for item in data:
            try:
                place_id = item.get("place_id")
                if not place_id:
                    continue
                
                doc = {
                    **item,
                    "_city": city,
                    "_layer": "silver",
                    "_processed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Upsert by place_id
                await collection.update_one(
                    {"place_id": place_id},
                    {"$set": doc},
                    upsert=True
                )
                count += 1
                
            except Exception as e:
                logger.warning(f"Failed to store silver record: {e}")
        
        logger.info(f"Stored {count} silver records for {city}")
        return count
    
    async def get_silver_data(
        self,
        city: str,
        limit: int = 10000,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lấy silver data cho city với optional filter."""
        collection = self._get_collection("silver")
        
        query = {"_city": city}
        if category:
            query["category"] = category
        
        cursor = collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_silver_poi_by_id(self, place_id: str) -> Optional[Dict]:
        """Lấy một POI by place_id."""
        collection = self._get_collection("silver")
        return await collection.find_one({"place_id": place_id})
    
    async def count_silver_data(self, city: str) -> int:
        """Đếm silver records cho city."""
        collection = self._get_collection("silver")
        return await collection.count_documents({"_city": city})
    
    # ========================================================================
    # GOLD LAYER OPERATIONS
    # ========================================================================
    
    async def store_gold_data(
        self,
        city: str,
        data: Dict[str, Any]
    ) -> int:
        """
        Store aggregated data to gold layer.
        
        Gold layer chứa aggregated data, không phải individual POIs.
        """
        collection = self._get_collection("gold")
        
        try:
            doc = {
                "_city": city,
                "_layer": "gold",
                "_aggregated_at": datetime.utcnow().isoformat(),
                **data
            }
            
            # Upsert by city
            result = await collection.update_one(
                {"_city": city},
                {"$set": doc},
                upsert=True
            )
            
            # Count records
            pois_count = len(data.get("pois", []))
            logger.info(f"Stored gold data for {city} ({pois_count} POIs)")
            return pois_count
            
        except Exception as e:
            logger.error(f"Failed to store gold data: {e}")
            return 0
    
    async def get_gold_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Lấy gold data cho city."""
        collection = self._get_collection("gold")
        return await collection.find_one({"_city": city})
    
    # ========================================================================
    # UTILITY OPERATIONS
    # ========================================================================
    
    async def delete_by_city(self, city: str, layer: Optional[str] = None) -> int:
        """Xóa data cho city."""
        if layer:
            collection = self._get_collection(layer)
            result = await collection.delete_many({"_city": city})
            return result.deleted_count
        else:
            # Delete from all layers
            total = 0
            for l in ["bronze", "silver", "gold"]:
                try:
                    collection = self._get_collection(l)
                    result = await collection.delete_many({"_city": city})
                    total += result.deleted_count
                except Exception as e:
                    logger.warning(f"Failed to delete from {l} layer: {e}")
            return total
    
    async def get_stats(self, city: str) -> Dict[str, int]:
        """Lấy stats cho city."""
        return {
            "bronze": await self.count_bronze_data(city),
            "silver": await self.count_silver_data(city),
            "gold": 1 if await self.get_gold_data(city) else 0
        }
    
    async def find_nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float = 1.0,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find POIs near a location.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius_km: Search radius in km
            category: Optional category filter
            limit: Max results
            
        Returns:
            List nearby POIs
        """
        collection = self._get_collection("silver")
        
        # Create geospatial query
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius_km * 1000  # Convert to meters
                }
            }
        }
        
        if category:
            query["category"] = category
        
        cursor = collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)
