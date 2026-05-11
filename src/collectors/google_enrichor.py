# collectors/google_enrichor.py
"""
GoogleEnrichor
==============
Enrich bronze_pois (đã có osm_raw) với Google Places data.
Update từng POI vào bronze_pois với google_raw schema.
Dùng RapidAPI keys từ storage/configs/rapidapi_keys.json với quota guard.
Resume-safe: bỏ qua POIs đã có has_google_data=True.
"""
import json
import os
import logging
import hashlib
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from pymongo import MongoClient

logger = logging.getLogger(__name__)

# ==========================================
# RapidAPI config
# ==========================================
_RAPIDAPI_HOST = "google-map-places.p.rapidapi.com"
_NEARBY_SEARCH_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/nearbysearch/json"
_PLACE_DETAILS_URL = f"https://{_RAPIDAPI_HOST}/maps/api/place/details/json"

_KEYS_FILE = Path(__file__).parent.parent.parent / "storage" / "configs" / "rapidapi_keys.json"
try:
    with open(_KEYS_FILE, "r") as _f:
        _RAPIDAPI_KEYS: List[str] = json.load(_f)
except Exception:
    _RAPIDAPI_KEYS = []

_key_index = 0


def _get_next_key() -> str:
    global _key_index
    if not _RAPIDAPI_KEYS:
        raise RuntimeError(f"No RapidAPI keys found in {_KEYS_FILE}")
    key = _RAPIDAPI_KEYS[_key_index % len(_RAPIDAPI_KEYS)]
    _key_index += 1
    return key


def _rapidapi_headers() -> Dict[str, str]:
    return {
        "x-rapidapi-key": _get_next_key(),
        "x-rapidapi-host": _RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }


def _call_rapidapi(url: str, params: Dict) -> Dict:
    """Gọi RapidAPI với auto-rotate key khi gặp quota exceeded."""
    for _ in range(len(_RAPIDAPI_KEYS) or 1):
        try:
            resp = requests.get(url, headers=_rapidapi_headers(), params=params, timeout=30)
            data = resp.json()
            msg = data.get("message", "")
            if "quota" in msg.lower() or "exceeded" in msg.lower() or "limit" in msg.lower():
                continue
            return data
        except Exception as e:
            logger.warning(f"RapidAPI call error: {e}")
            continue
    return {"status": "QUOTA_EXCEEDED_ALL_KEYS"}


class GoogleEnrichor:
    """
    Enrich bronze_pois có osm_raw nhưng chưa có google_raw.
    Update trực tiếp vào MongoDB bronze_pois.
    Resume-safe: bỏ qua POIs đã có has_google_data=True.
    """

    def __init__(self, mongo_uri: Optional[str] = None):
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI",
            "mongodb+srv://nguyenanhilu9785_db_user:12345@cluster0.olqzq.mongodb.net/smart_travel_platform?appName=Cluster0"
        )
        self._client = MongoClient(self.mongo_uri)
        self._bronze = self._client.smart_travel_platform.bronze_pois
        logger.info(f"🔌 GoogleEnrichor initialized with {len(_RAPIDAPI_KEYS)} RapidAPI keys")

    def _search_nearby(self, lat: float, lon: float, radius: int = 100) -> Dict:
        return _call_rapidapi(_NEARBY_SEARCH_URL, {
            "location": f"{lat},{lon}",
            "radius": radius,
            "language": "vi"
        })

    def _get_place_details(self, place_id: str) -> Dict:
        return _call_rapidapi(_PLACE_DETAILS_URL, {
            "place_id": place_id,
            "fields": "all",
            "language": "vi"
        })

    def enrich_batch(self, city: Optional[str] = None, limit: int = 100) -> Dict[str, int]:
        """
        Enrich batch POIs trong bronze_pois có osm_raw nhưng chưa có google_raw.
        Update google_raw, has_google_data, data_sources trực tiếp trong MongoDB.

        Args:
            city: Lọc theo city code (optional)
            limit: Số POI tối đa mỗi lần chạy

        Returns:
            {"enriched": int, "not_found": int, "errors": int, "stopped": bool}
        """
        if not _RAPIDAPI_KEYS:
            logger.error(f"No RapidAPI keys found in {_KEYS_FILE}")
            return {"enriched": 0, "not_found": 0, "errors": 0, "stopped": True}

        query: Dict[str, Any] = {
            "has_osm_data": True,
            "has_google_data": False,
            "location": {"$exists": True}
        }
        if city:
            query["city"] = city

        pois = list(self._bronze.find(query).limit(limit))
        enriched = not_found = errors = 0

        for poi in pois:
            try:
                loc = poi.get("location", {})
                lat, lon = loc.get("lat"), loc.get("lon")
                if not lat or not lon:
                    not_found += 1
                    continue

                search_result = self._search_nearby(lat, lon, radius=100)
                status = search_result.get("status")

                # Quota exceeded → dừng ngay
                if status == "QUOTA_EXCEEDED_ALL_KEYS":
                    logger.error(f"All {len(_RAPIDAPI_KEYS)} RapidAPI keys exceeded daily quota. Stopping.")
                    return {"enriched": enriched, "not_found": not_found, "errors": errors, "stopped": True}

                if status in ("REQUEST_DENIED", "INVALID_REQUEST"):
                    logger.error(f"RapidAPI error: {status}. Stopping.")
                    return {"enriched": enriched, "not_found": not_found, "errors": errors, "stopped": True}

                results = search_result.get("results", [])
                if not results or status != "OK":
                    not_found += 1
                    continue

                closest = results[0]
                place_id = closest.get("place_id")
                details = self._get_place_details(place_id)

                self._bronze.update_one(
                    {"_id": poi["_id"]},
                    {
                        "$set": {
                            "google_raw": {
                                "place": closest,
                                "place_details": details,
                                "place_id": place_id,
                                "fetched_at": datetime.now(timezone.utc).isoformat()
                            },
                            "has_google_data": True,
                            "google_place_id": place_id,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        },
                        "$addToSet": {"data_sources": "google"}
                    }
                )
                enriched += 1
                logger.info(f"💾 Enriched: {poi.get('name')} ({poi.get('city')})")

            except Exception as e:
                logger.error(f"Error enriching POI {poi.get('_id')}: {e}")
                errors += 1
                continue

        return {"enriched": enriched, "not_found": not_found, "errors": errors, "stopped": False}

    def close(self):
        self._client.close()
