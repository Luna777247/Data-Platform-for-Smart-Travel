"""
Silver & Gold Pipeline Service
==============================
Transform Bronze data (MongoDB) → Silver/Gold (MongoDB)
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

from src.db.client import get_database
from src.core.logging import get_logger

logger = get_logger(__name__)


class SilverGoldPipeline:
    """
    Pipeline cho Silver và Gold layers:
    - bronze_pois (osm_raw/google_raw) → Transform → Silver (MongoDB)
    - Silver (MongoDB) → Enrich → Gold (MongoDB)
    """
    
    def __init__(self):
        self.db = get_database()
        self.bronze_collection = "bronze_pois"  # New collection with raw data
    
    async def bronze_to_silver(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        batch_size: int = 100,
        source: Optional[str] = None  # "osm", "google", or None (both)
    ) -> Dict[str, Any]:
        """
        Transform bronze_pois records (osm_raw/google_raw) → Silver trong MongoDB
        
        Schema Silver:
        - Cleaned và normalized từ raw data
        - Standard location format
        - Unified categories từ cả OSM và Google
        - Basic deduplication
        """
        logger.info(f"Transforming Bronze → Silver for {city or 'all cities'}")
        
        # Query bronze_pois records có raw data
        query = {}
        if city:
            query["city"] = city
        if category:
            query["category"] = category
        
        # Filter by data source
        if source == "osm":
            query["has_osm_data"] = True
        elif source == "google":
            query["has_google_data"] = True
        else:
            # Cần có ít nhất 1 source
            query["$or"] = [{"has_osm_data": True}, {"has_google_data": True}]
        
        bronze_cursor = self.db[self.bronze_collection].find(query).limit(batch_size)
        bronze_records = await bronze_cursor.to_list(length=batch_size)
        
        transformed = 0
        errors = []
        
        for bronze_doc in bronze_records:
            try:
                # Transform to Silver schema
                silver_doc = self._transform_to_silver(bronze_doc)
                
                # Check for duplicates trong Silver
                existing = await self.db["silver_pois"].find_one({
                    "place_id": silver_doc["place_id"],
                    "city": silver_doc["city"]
                })
                
                if existing:
                    # Update existing
                    await self.db["silver_pois"].update_one(
                        {"_id": existing["_id"]},
                        {"$set": {**silver_doc, "updated_at": datetime.now().isoformat()}}
                    )
                else:
                    # Insert new
                    await self.db["silver_pois"].insert_one(silver_doc)
                
                transformed += 1
                
            except Exception as e:
                errors.append(f"Error transforming {bronze_doc.get('_id')}: {e}")
                continue
        
        logger.info(f"Transformed {transformed} records to Silver")
        
        return {
            "transformed": transformed,
            "errors": errors,
            "total_bronze": len(bronze_records)
        }
    
    def _transform_to_silver(
        self,
        bronze_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform bronze_pois record (với osm_raw và/hoặc google_raw) sang Silver schema
        """
        # Get raw data
        osm_raw = bronze_data.get("osm_raw", {})
        google_raw = bronze_data.get("google_raw", {})
        
        has_osm = bronze_data.get("has_osm_data", False) and osm_raw
        has_google = bronze_data.get("has_google_data", False) and google_raw
        
        # Extract OSM element data
        osm_element = osm_raw.get("element", {}) if osm_raw else {}
        osm_tags = osm_element.get("tags", {})
        
        # Extract Google data
        google_details = google_raw.get("place_details", {}).get("result", {}) if google_raw else {}
        
        # === LOCATION ===
        # Ưu tiên OSM location, fallback to Google
        location = bronze_data.get("location", {})
        if not location and has_osm:
            if osm_element.get("lat") and osm_element.get("lon"):
                location = {"lat": osm_element["lat"], "lon": osm_element["lon"]}
            elif osm_element.get("center"):
                location = {
                    "lat": osm_element["center"]["lat"],
                    "lon": osm_element["center"]["lon"]
                }
        
        # Fallback to Google location
        if not location and has_google:
            geo = google_details.get("geometry", {}).get("location", {})
            if geo:
                location = {"lat": geo.get("lat"), "lon": geo.get("lng")}
        
        # === NAME ===
        # Ưu tiên OSM name, fallback to Google
        name = bronze_data.get("name")
        if not name and has_osm:
            name = osm_tags.get("name") or osm_tags.get("name:en")
        if not name and has_google:
            name = google_details.get("name")
        name = name or "Unknown"
        
        # === ADDRESS ===
        address = bronze_data.get("address")
        if not address and has_osm:
            address = osm_tags.get("addr:street") or osm_tags.get("addr:full")
        if not address and has_google:
            address = google_details.get("formatted_address") or google_details.get("vicinity")
        
        # === CATEGORY ===
        category = bronze_data.get("category", "unknown")
        google_types = google_details.get("types", [])
        
        # === RATING ===
        # Ưu tiên Google rating
        rating = google_details.get("rating") if has_google else None
        user_rating_count = google_details.get("user_ratings_total", 0) if has_google else 0
        
        # === CONTACT ===
        phone = bronze_data.get("phone") or osm_tags.get("phone") if has_osm else None
        if has_google and not phone:
            phone = google_details.get("formatted_phone_number")
        
        website = bronze_data.get("website") or osm_tags.get("website") if has_osm else None
        if has_google and not website:
            website = google_details.get("website")
        
        # === OPENING HOURS ===
        opening_hours = osm_tags.get("opening_hours") if has_osm else None
        if has_google and not opening_hours:
            opening_hours = google_details.get("opening_hours", {}).get("weekday_text")
        
        # Build Silver document
        silver_doc = {
            # IDs
            "place_id": bronze_data.get("google_place_id") or bronze_data.get("poi_id"),
            "u_key": bronze_data.get("u_key"),
            
            # Basic info
            "name": name,
            "city": bronze_data.get("city"),
            "city_name": bronze_data.get("city_name"),
            "country": bronze_data.get("country", "Vietnam"),
            
            # Location (standardized)
            "location": location,
            
            # Address
            "address": address,
            
            # Contact
            "phone": phone,
            "website": website,
            "opening_hours": opening_hours,
            
            # Categories (unified)
            "category": category,
            "types": google_types,
            
            # Ratings
            "rating": rating,
            "user_rating_count": user_rating_count,
            
            # Price level (from Google)
            "price_level": self._normalize_price_level(
                google_details.get("price_level")
            ) if has_google else None,
            
            # Media (from Google)
            "photos": self._extract_photos(google_details.get("photos", [])) if has_google else [],
            "image_url": self._extract_main_photo(google_details.get("photos", [])) if has_google else None,
            
            # OSM specific
            "osm_id": bronze_data.get("osm_id"),
            "osm_type": bronze_data.get("osm_type"),
            "osm_tags": osm_tags if has_osm else None,
            
            # Data source tracking
            "has_osm_data": has_osm,
            "has_google_data": has_google,
            "data_sources": bronze_data.get("data_sources", []),
            
            # Raw data references (không lưu full raw để tránh document quá lớn)
            "_raw_refs": {
                "bronze_pois_id": str(bronze_data.get("_id")),
                "osm_element_id": osm_element.get("id") if has_osm else None,
                "google_place_id": bronze_data.get("google_place_id")
            },
            
            # Metadata
            "_collected_at": bronze_data.get("created_at"),
            "_transformed_at": datetime.now().isoformat(),
            "layer": "silver"
        }
        
        return silver_doc
    
    async def silver_to_gold(
        self,
        city: Optional[str] = None,
        min_rating: float = 3.5,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Transform Silver → Gold (Master Data)
        
        Schema Gold:
        - Enriched với additional data
        - Quality scoring
        - Deduplicated
        - Ready for production use
        """
        logger.info(f"Transforming Silver → Gold for {city or 'all cities'}")
        
        # Query Silver records
        query = {"layer": "silver"}
        if city:
            query["city"] = city
        if min_rating:
            query["rating"] = {"$gte": min_rating}
        
        silver_records = await self.db["silver_pois"].find(query).to_list(batch_size)
        
        enriched = 0
        errors = []
        
        for silver_doc in silver_records:
            try:
                # Transform to Gold
                gold_doc = self._transform_to_gold(silver_doc)
                
                # Upsert to Gold
                await self.db["gold_master_pois"].update_one(
                    {"place_id": gold_doc["place_id"]},
                    {"$set": gold_doc},
                    upsert=True
                )
                
                enriched += 1
                
            except Exception as e:
                errors.append(f"Error enriching {silver_doc.get('place_id')}: {e}")
                continue
        
        logger.info(f"Enriched {enriched} records to Gold")
        
        return {
            "enriched": enriched,
            "errors": errors,
            "total_silver": len(silver_records)
        }
    
    def _transform_to_gold(self, silver_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Silver → Gold với enrichment
        """
        gold_doc = {
            **silver_doc,  # Copy all Silver fields
            
            # Gold-specific fields
            "poi_id": f"gold_{silver_doc.get('place_id', '')}",
            "layer": "gold",
            
            # Quality scoring
            "quality_score": self._calculate_quality_score(silver_doc),
            "data_completeness": self._calculate_completeness(silver_doc),
            
            # Enriched fields
            "subcategory": self._extract_subcategory(silver_doc.get("types", [])),
            "review_count": silver_doc.get("user_rating_count", 0),
            
            # Flags
            "is_active": True,
            "verified": False,  # Cần manual verification
            
            # Timestamps
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        # Remove internal fields
        gold_doc.pop("_bronze_id", None)
        gold_doc.pop("_id", None)  # Will get new _id in Gold collection
        
        return gold_doc
    
    # ===== Helper Methods =====
    
    def _normalize_category(self, raw_category: str, types: List[str]) -> str:
        """Normalize category về standard format"""
        category_map = {
            "restaurant": "restaurant",
            "cafe": "cafe",
            "bar": "bar",
            "lodging": "hotel",
            "hotel": "hotel",
            "tourist_attraction": "attraction",
            "amusement_park": "attraction",
            "museum": "attraction",
            "shopping_mall": "shopping",
            "store": "shopping",
            "supermarket": "shopping",
            "gym": "entertainment",
            "spa": "entertainment",
            "movie_theater": "entertainment",
        }
        
        # Try raw category first
        if raw_category:
            normalized = category_map.get(raw_category.lower())
            if normalized:
                return normalized
        
        # Try types
        for t in types:
            t_lower = t.lower().replace("_", "")
            for key, value in category_map.items():
                if key in t_lower:
                    return value
        
        return "other"
    
    def _normalize_price_level(self, price_level: Any) -> Optional[int]:
        """Normalize price level về 1-4 scale"""
        if isinstance(price_level, str):
            mapping = {
                "PRICE_LEVEL_FREE": 0,
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4,
            }
            return mapping.get(price_level)
        elif isinstance(price_level, int):
            return price_level if 0 <= price_level <= 4 else None
        return None
    
    def _extract_photos(self, photos: List[Dict]) -> List[str]:
        """Extract photo URLs"""
        urls = []
        for photo in photos[:5]:  # Max 5 photos
            if isinstance(photo, dict):
                url = photo.get("photo_url") or photo.get("googleMapsUri")
                if url:
                    urls.append(url)
        return urls
    
    def _extract_main_photo(self, photos: List[Dict]) -> Optional[str]:
        """Extract main photo URL"""
        if photos and isinstance(photos[0], dict):
            return photos[0].get("photo_url") or photos[0].get("googleMapsUri")
        return None
    
    def _calculate_quality_score(self, doc: Dict[str, Any]) -> float:
        """Calculate quality score 0-1"""
        score = 0.0
        
        # Has rating
        if doc.get("rating"):
            score += 0.3 * (doc["rating"] / 5.0)
        
        # Has reviews
        if doc.get("user_rating_count", 0) > 10:
            score += 0.2
        
        # Has photos
        if doc.get("photos"):
            score += 0.2
        
        # Has complete info
        if doc.get("address") and doc.get("name"):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_completeness(self, doc: Dict[str, Any]) -> float:
        """Calculate data completeness 0-1"""
        required_fields = ["name", "location", "address", "category", "rating"]
        optional_fields = ["photos", "price_level", "types"]
        
        required_score = sum(1 for f in required_fields if doc.get(f)) / len(required_fields)
        optional_score = sum(1 for f in optional_fields if doc.get(f)) / len(optional_fields)
        
        return (required_score * 0.7) + (optional_score * 0.3)
    
    def _extract_subcategory(self, types: List[str]) -> str:
        """Extract subcategory từ types"""
        if not types:
            return "general"
        
        # Filter out generic types
        generic = ["establishment", "point_of_interest", "place_of_worship"]
        specific = [t for t in types if t not in generic]
        
        return specific[0] if specific else "general"
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics from MongoDB"""
        bronze_count = await self.db[self.bronze_collection].count_documents({})
        silver_count = await self.db["silver_pois"].count_documents({})
        gold_count = await self.db["gold_master_pois"].count_documents({})
        
        return {
            "bronze": {"total": bronze_count},
            "silver": {"total": silver_count},
            "gold": {"total": gold_count},
            "status": "healthy" if gold_count > 0 else "processing"
        }
