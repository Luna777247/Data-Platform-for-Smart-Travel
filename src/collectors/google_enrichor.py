# collectors/google_enrichor.py
import httpx
import asyncio
import os
import random
import logging
from datetime import datetime
from typing import Dict, Any, List
# Workaround to import utils
from src.shared.key_manager import SmartKeyManager
from src.shared.data_utils import calculate_content_hash

logger = logging.getLogger(__name__)

class GoogleEnrichor:
    def __init__(self):
        working_keys = os.getenv("WORKING_KEYS")
        if working_keys:
            keys = working_keys.split(",")
        else:
            keys = [
                os.getenv(f"RAPID_API_KEY{i}") for i in range(1, 21)
                if os.getenv(f"RAPID_API_KEY{i}")
            ]
        
        if not keys:
            keys = ["02ad4fd6f3msh1f0390da51ae627p19a5cfjsn7f2b23cadfdb"]
        
        # SMART KEY MANAGER: Each free key has ~500 daily requests limit
        self.key_manager = SmartKeyManager(keys, daily_limit=500)
        logger.info(f"🔌 GoogleEnrichor initialized with {len(keys)} keys from env.")
        for i, k in enumerate(keys):
             logger.info(f"   - Key {i+1}: {k[:8]}...")
        self.host = "google-map-places.p.rapidapi.com"
        self.lock = asyncio.Lock()

    async def get_next_key(self):
        """Find the best available key based on usage and status."""
        async with self.lock:
            key = self.key_manager.get_best_key()
            if not key:
                raise Exception("CRITICAL: All API keys are exhausted or blocked.")
            return key

    async def enrich_batch(self, places: List[Dict[str, Any]], city: str) -> List[Dict[str, Any]]:
        """Enrich a batch of places concurrently with concurrency limit."""
        semaphore = asyncio.Semaphore(5) # Limit to 5 concurrent requests
        
        async with httpx.AsyncClient() as client:
            tasks = [self.enrich_single(client, place, city, semaphore) for place in places]
            return await asyncio.gather(*tasks)

    async def enrich_single(self, client, place, city, semaphore) -> Dict[str, Any]:
        """
        Làm giàu dữ liệu: Gọi API và LƯU RAW JSON vào Bronze Layer.
        """
        async with semaphore:
            u_key = place.get("u_key")
            if not u_key: return place
            
            # 1. KIỂM TRA CHECKPOINT: Nếu đã có file raw rồi thì bỏ qua (Tiết kiệm Request)
            local_raw_path = os.path.join("storage", "bronze", "google", city, f"{u_key}.json")
            if os.path.exists(local_raw_path):
                return place

            api_key = await self.get_next_key()
            headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": self.host}
            
            try:
                # 2. BƯỚC 1: Tìm Place ID
                search_resp = await client.get(
                    f"https://{self.host}/maps/api/place/findplacefromtext/json",
                    headers=headers,
                    params={"input": f"{place['name']}, {city}", "inputtype": "textquery", "fields": "place_id"},
                    timeout=15
                )
                
                if search_resp.status_code != 200:
                    self.key_manager.report_error(api_key, search_resp.status_code)
                    return place
                
                candidates = search_resp.json().get("candidates", [])
                if not candidates: 
                    return place
                
                # 3. BƯỚC 2: Lấy chi tiết (DETAILS) - ĐÂY LÀ DỮ LIỆU QUÝ GIÁ
                place_id = candidates[0]["place_id"]
                details_resp = await client.get(
                    f"https://{self.host}/maps/api/place/details/json",
                    headers=headers,
                    params={
                        "place_id": place_id, 
                        "fields": "name,rating,user_ratings_total,price_level,formatted_phone_number,opening_hours,geometry,reviews", 
                        "language": "vi"
                    },
                    timeout=15
                )
                
                if details_resp.status_code == 200:
                    raw_result = details_resp.json().get("result", {})
                    
                    # 4. LƯU NGUYÊN BẢN (RAW JSON) VÀO BRONZE
                    os.makedirs(os.path.dirname(local_raw_path), exist_ok=True)
                    with open(local_raw_path, "w", encoding="utf-8") as f:
                        import json
                        # Lưu kèm u_key để dễ quản lý
                        full_payload = {
                            "u_key": u_key,
                            "original_osm_name": place['name'],
                            "google_raw": raw_result,
                            "harvested_at": datetime.now().isoformat()
                        }
                        json.dump(full_payload, f, ensure_ascii=False, indent=2)
                    
                    self.key_manager.record_usage(api_key)
                    logger.info(f"💾 [GOOGLE BRONZE] Saved raw data for: {place['name']} ({u_key})")
                else:
                    self.key_manager.report_error(api_key, details_resp.status_code)
                    
                return place
            except Exception as e:
                logger.error(f"❌ Google API Error for {place['name']}: {e}")
                self.key_manager.report_error(api_key, 500)
                return place
