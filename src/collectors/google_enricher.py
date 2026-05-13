import httpx
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pymongo import MongoClient

# RapidAPI config
_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = "https://google-map-places.p.rapidapi.com/maps/api/place/details/json"

from src.core.config import settings

_RAPIDAPI_KEYS = settings.rapid_api_keys

_key_index = 0


def _get_rapidapi_headers() -> Dict[str, str]:
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError("No RapidAPI keys found in settings/env")
    key = _RAPIDAPI_KEYS[_key_index % len(_RAPIDAPI_KEYS)]
    _key_index += 1
    return {
        "x-rapidapi-key": key,
        "x-rapidapi-host": _RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }


class GoogleEnricher:
    def __init__(self, city: str, api_key: str = None, mongo_uri: str = None):
        self.city = city
        self.nearby_url = _NEARBY_SEARCH_URL
        self.details_url = _PLACE_DETAILS_URL

        # MongoDB connection
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client.smart_travel_platform

        self._load_city_config()

    def _load_city_config(self):
        from src.shared.path_manager import ROOT_DIR
        import json
        import os
        
        config_path = os.path.join(ROOT_DIR, "storage", "configs", "cities.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.city_config = json.load(f)
        except Exception:
            self.city_config = {}

    async def enrich_existing_pois(self) -> Dict[str, Any]:
        """Enrich existing bronze_pois with Google data (add google_raw)"""
        # Find POIs without Google data
        pois = list(self.db.bronze_pois.find({
            "city": self.city,
            "has_osm_data": True,
            "has_google_data": False,
            "location": {"$exists": True}
        }).limit(50))
        
        enriched_count = 0
        errors = []
        
        for poi in pois:
            try:
                location = poi.get("location", {})
                lat, lon = location.get("lat"), location.get("lon")
                
                if not lat or not lon:
                    continue
                
                # Search nearby
                search_data = await self._search_nearby(lat, lon, radius=100)
                
                if not search_data or search_data.get("status") != "OK":
                    continue
                
                results = search_data.get("results", [])
                if not results:
                    continue
                
                # Get closest match
                closest = results[0]
                place_id = closest.get("place_id")
                
                # Get place details
                details_data = await self._get_place_details(place_id)
                
                # Build google_raw
                google_raw = {
                    "nearby_search": search_data,
                    "place_details": details_data,
                    "place_id": place_id,
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Update bronze_pois with google_raw
                self.db.bronze_pois.update_one(
                    {"_id": poi["_id"]},
                    {
                        "$set": {
                            "google_raw": google_raw,
                            "has_google_data": True,
                            "google_place_id": place_id,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "rating": self._extract_rating(details_data),
                            "review_count": self._extract_review_count(details_data)
                        },
                        "$addToSet": {
                            "data_sources": "google"
                        }
                    }
                )
                
                enriched_count += 1
                
            except Exception as e:
                errors.append(str(e))
                continue
        
        return {
            "enriched": enriched_count,
            "errors": len(errors),
            "city": self.city
        }
    
    async def _search_nearby(self, lat: float, lon: float, radius: int = 100) -> Dict:
        """Search places near coordinates via RapidAPI"""
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "language": "vi"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.nearby_url,
                params=params,
                headers=_get_rapidapi_headers()
            )
            return response.json()

    async def _get_place_details(self, place_id: str) -> Dict:
        """Get place details via RapidAPI"""
        params = {
            "place_id": place_id,
            "fields": "all",
            "language": "vi"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.details_url,
                params=params,
                headers=_get_rapidapi_headers()
            )
            return response.json()
    
    def _extract_rating(self, details_data: Dict) -> Optional[float]:
        """Extract rating from place details"""
        try:
            if details_data.get("status") == "OK":
                result = details_data.get("result", {})
                return result.get("rating")
        except:
            pass
        return None
    
    def _extract_review_count(self, details_data: Dict) -> int:
        """Extract review count from place details"""
        try:
            if details_data.get("status") == "OK":
                result = details_data.get("result", {})
                return result.get("user_ratings_total", 0)
        except:
            pass
        return 0
