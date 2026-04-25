# collectors/google_enrichor.py
import httpx
import asyncio
import os
import random
import logging
from typing import Dict, Any, List
# Workaround to import utils
try:
    from app.utils.data_quality import calculate_content_hash
except ImportError:
    import hashlib
    def calculate_content_hash(data):
        return hashlib.sha256(str(sorted(data.items())).encode()).hexdigest()

logger = logging.getLogger(__name__)

class GoogleEnrichor:
    def __init__(self):
        self.api_keys = [
            os.getenv(f"RAPID_API_KEY{i}") for i in range(1, 21)
            if os.getenv(f"RAPID_API_KEY{i}")
        ]
        # Fallback if no env vars found
        if not self.api_keys:
            self.api_keys = ["02ad4fd6f3msh1f0390da51ae627p19a5cfjsn7f2b23cadfdb"]
        
        self.host = "google-map-places.p.rapidapi.com"
        self.key_index = 0
        self.lock = asyncio.Lock()

    async def get_next_key(self):
        """Sequential key rotation (Round Robin)."""
        async with self.lock:
            key = self.api_keys[self.key_index]
            self.key_index = (self.key_index + 1) % len(self.api_keys)
            logger.info(f"Rotating to API Key index: {self.key_index}")
            return key

    async def enrich_batch(self, places: List[Dict[str, Any]], city: str) -> List[Dict[str, Any]]:
        """Enrich a batch of places concurrently with concurrency limit."""
        semaphore = asyncio.Semaphore(5) # Limit to 5 concurrent requests
        
        async with httpx.AsyncClient() as client:
            tasks = [self.enrich_single(client, place, city, semaphore) for place in places]
            return await asyncio.gather(*tasks)

    async def enrich_single(self, client, place, city, semaphore) -> Dict[str, Any]:
        async with semaphore:
            # Check if we should skip based on source
            if place.get("source") == "google":
                return place 
                
            api_key = await self.get_next_key()
            headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": self.host}
            
            try:
                # 1. Find Place
                resp = await client.get(
                    f"https://{self.host}/maps/api/place/findplacefromtext/json",
                    headers=headers,
                    params={"input": f"{place['name']}, {city}", "inputtype": "textquery", "fields": "place_id"},
                    timeout=15
                )
                candidates = resp.json().get("candidates", [])
                if not candidates: return place
                
                # 2. Get Details
                place_id = candidates[0]["place_id"]
                resp_details = await client.get(
                    f"https://{self.host}/maps/api/place/details/json",
                    headers=headers,
                    params={"place_id": place_id, "fields": "rating,user_ratings_total,price_level", "language": "vi"},
                    timeout=15
                )
                res = resp_details.json().get("result", {})
                
                # Update data
                place["rating"] = res.get("rating", 0)
                place["reviews"] = res.get("user_ratings_total", 0)
                place["price_level"] = res.get("price_level", 0)
                place["source"] = "google"
                
                # Calculate new hash for change detection
                place["hash"] = calculate_content_hash(place)
                
                return place
            except Exception as e:
                logger.error(f"[ERROR] Google API failed for {place['name']}: {e}")
                return place
