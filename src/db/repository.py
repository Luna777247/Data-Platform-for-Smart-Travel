# backend/app/db/repository.py
import json
import os
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone
from app.api.dependencies.database import mongo_client
from app.core.config import settings
from app.models.place import PlaceModel, PipelineStatus
import logging

logger = logging.getLogger(__name__)

class PlaceRepository:
    def __init__(self):
        self.db = mongo_client[settings.mongodb_database]
        # COMPACT STORAGE ARCHITECTURE (Corrected path to project root)
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        storage_dir = os.path.join(self.project_root, "storage")
        
        self.local_data_path = os.path.join(storage_dir, "data", "pois.json")
        self.local_status_path = os.path.join(storage_dir, "metadata", "pipeline_status.json")
        
        # Check connectivity
        self.is_offline = False  # Always online now
        self.places = self.db["places"]
        self.pipeline_status = self.db["pipeline_status"]
        self.users = self.db["users"]
        self.roles = self.db["roles"]
        self.api_keys = self.db["api_keys"]
        self.backups = self.db["backups"]
        self.settings = self.db["settings"]

    async def init_indexes(self):
        if self.is_offline: return
        try:
            await self.places.create_index([("city", 1)])
            await self.places.create_index([("categories", 1)])
            await self.places.create_index([("city", 1), ("categories", 1)])
            await self.places.create_index([("type", 1)])
            await self.places.create_index([("u_key", 1)], unique=True)
            await self.places.create_index([("location", "2dsphere")])
            await self.places.create_index([("rating", -1)])
            
            # TTL index for automatic cleanup (90 days)
            await self.places.create_index(
                [("created_at", 1)],
                expireAfterSeconds=7776000
            )
            
            # Admin indexes
            await self.users.create_index([("email", 1)], unique=True)
            await self.api_keys.create_index([("short_key", 1)], unique=True)
            
            logger.info("✅ All MongoDB indexes initialized successfully")
        except Exception as e:
            logger.error(f"❌ Index initialization failed: {e}", exc_info=True)

    # --- USER MANAGEMENT ---
    async def get_users(self):
        cursor = self.db["users"].find({})
        users = []
        async for doc in cursor:
            if "_id" in doc:
                doc["id"] = doc.get("id") or str(doc["_id"])
                doc["_id"] = str(doc["_id"])
            users.append(doc)
        return users

    async def delete_user(self, user_id: str):
        if self.is_offline: return
        await self.users.delete_one({"_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id})

    async def upsert_user(self, user_data: dict):
        if self.is_offline: return
        email = user_data.get("email")
        await self.users.update_one({"email": email}, {"$set": user_data}, upsert=True)

    # --- ROLE MANAGEMENT ---
    async def get_roles(self) -> List[dict]:
        if self.is_offline: return []
        cursor = self.roles.find({})
        return [self._format_doc(doc) async for doc in cursor]

    # --- API KEY MANAGEMENT ---
    async def get_api_keys(self) -> List[dict]:
        if self.is_offline: return []
        cursor = self.api_keys.find({})
        return [self._format_doc(doc) async for doc in cursor]

    async def delete_api_key(self, key_id: str):
        if self.is_offline: return
        await self.api_keys.delete_one({"_id": ObjectId(key_id) if ObjectId.is_valid(key_id) else key_id})

    async def upsert_api_key(self, key_data: dict):
        if self.is_offline: return
        short_key = key_data.get("short_key")
        await self.api_keys.update_one({"short_key": short_key}, {"$set": key_data}, upsert=True)

    # --- BACKUP MANAGEMENT ---
    async def get_backups(self) -> List[dict]:
        if self.is_offline: return []
        cursor = self.backups.find({}).sort("createdAt", -1)
        return [self._format_doc(doc) async for doc in cursor]

    async def create_backup_record(self, backup_data: dict):
        if self.is_offline: return
        await self.backups.insert_one(backup_data)

    # --- SETTINGS MANAGEMENT ---
    async def get_settings(self) -> dict:
        if self.is_offline: return {}
        settings = await self.settings.find_one({"_id": "system_config"})
        return self._format_doc(settings) if settings else {}

    async def update_settings(self, settings_data: dict):
        if self.is_offline: return
        await self.settings.update_one({"_id": "system_config"}, {"$set": settings_data}, upsert=True)

    async def get_all(self, city: Optional[str] = None, place_type: Optional[str] = None, 
                      rating_min: Optional[float] = None, limit: int = 50, offset: int = 0) -> List[dict]:
        if self.is_offline:
            return await self._get_from_json(city, place_type, limit, offset)

        query = {}
        if city: query["city"] = city.lower()
        if place_type: query["type"] = place_type.lower()
        if rating_min: query["rating"] = {"$gte": rating_min}

        cursor = self.places.find(query).skip(offset).limit(limit)
        return [self._format_doc(doc) async for doc in cursor]

    async def _get_from_json(self, city=None, p_type=None, limit=50, offset=0):
        if not os.path.exists(self.local_data_path): return []
        try:
            with open(self.local_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read local JSON data: {e}", exc_info=True)
            return []
        
        filtered = data
        if city: filtered = [p for p in filtered if p.get("city") == city.lower()]
        if p_type: filtered = [p for p in filtered if p.get("type") == p_type.lower()]
        
        return filtered[offset : offset + limit]

    async def get_by_ukey(self, u_key: str):
        if self.is_offline:
            data = await self._get_from_json(limit=10000)
            return next((p for p in data if p.get("u_key") == u_key), None)
        
        doc = await self.db["places"].find_one({"u_key": u_key})
        return self._format_doc(doc)

    async def upsert_place(self, place_data: dict):
        if self.is_offline:
            # Offline upsert is handled by the pipeline script directly to avoid file IO overhead in a loop
            return "SKIPPED_IN_REPOSITORY"

        u_key = place_data.get("u_key")
        if not u_key: return

        existing = await self.places.find_one({"u_key": u_key})
        if existing:
            if existing.get("hash") == place_data.get("hash"):
                return "SKIPPED"
            await self.places.update_one(
                {"u_key": u_key},
                {"$set": {**place_data, "last_updated": datetime.now(timezone.utc)}}
            )
            return "UPDATED"
        
        await self.places.insert_one({**place_data, "last_updated": datetime.now(timezone.utc)})
        return "CREATED"

    async def update_pipeline_status(self, status: PipelineStatus):
        if self.is_offline:
            current_status = await self._get_local_pipeline_status()
            match = False
            # Clean for JSON (convert datetime to string)
            status_data = status.model_dump(exclude_none=True)
            for k, v in status_data.items():
                if isinstance(v, datetime):
                    status_data[k] = v.isoformat()
            
            for s in current_status:
                if s["city"] == status.city and s["type"] == status.type:
                    s.update(status_data)
                    match = True
                    break
            if not match:
                current_status.append(status_data)
            
            with open(self.local_status_path, "w", encoding="utf-8") as f:
                json.dump(current_status, f, ensure_ascii=False, indent=2)
            return

        await self.pipeline_status.update_one(
            {"city": status.city, "type": status.type},
            {"$set": status.model_dump()},
            upsert=True
        )

    async def _get_local_pipeline_status(self):
        if not os.path.exists(self.local_status_path): return []
        try:
            with open(self.local_status_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read local pipeline status: {e}", exc_info=True)
            return []

    async def get_pipeline_status(self, city: str = None, place_type: str = None):
        if self.is_offline:
            data = await self._get_local_pipeline_status()
            if city: data = [s for s in data if s["city"] == city]
            if place_type: data = [s for s in data if s["type"] == place_type]
            return data

        query = {}
        if city: query["city"] = city
        if place_type: query["type"] = place_type
        cursor = self.pipeline_status.find(query)
        return [doc async for doc in cursor]

    async def get_pipeline_metrics(self):
        if self.is_offline:
            statuses = await self._get_local_pipeline_status()
            if not statuses: return []
            
            # Simple group by Global for offline
            metrics = {
                "total_collected": sum(s.get("collected", 0) for s in statuses),
                "total_target": sum(s.get("target", 0) for s in statuses),
                "active_jobs": sum(1 for s in statuses if s.get("status") == "running"),
                "completed_jobs": sum(1 for s in statuses if s.get("status") == "done"),
                "failed_jobs": sum(1 for s in statuses if s.get("status") == "failed")
            }
            return [{**metrics, "_id": "Offline Mode"}]

        pipeline = [
            {
                "$group": {
                    "_id": "$city",
                    "total_collected": {"$sum": "$collected"},
                    "total_target": {"$sum": "$target"},
                    "active_jobs": {"$sum": {"$cond": [{"$eq": ["$status", "running"]}, 1, 0]}},
                    "completed_jobs": {"$sum": {"$cond": [{"$eq": ["$status", "done"]}, 1, 0]}},
                    "failed_jobs": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
                }
            }
        ]
        return await self.pipeline_status.aggregate(pipeline).to_list(None)

    async def get_stats(self):
        data = await self._get_from_json(limit=1000000) if self.is_offline else []
        if self.is_offline:
            by_city, by_type, avg_rating = {}, {}, 0
            for p in data:
                c, t = p.get("city", "unknown"), p.get("type", "unknown")
                by_city[c] = by_city.get(c, 0) + 1
                by_type[t] = by_type.get(t, 0) + 1
                avg_rating += p.get("rating", 0)
            avg_rating = avg_rating / len(data) if data else 0
            return {"total_places": len(data), "avg_rating": round(avg_rating, 2), "by_city": by_city, "by_type": by_type}

        pipeline = [{"$group": {"_id": None, "total": {"$sum": 1}, "avg_rating": {"$avg": "$rating"}}}]
        stats = await self.places.aggregate(pipeline).to_list(1)
        city_stats = await self.places.aggregate([{"$group": {"_id": "$city", "count": {"$sum": 1}}}]).to_list(None)
        type_stats = await self.places.aggregate([{"$group": {"_id": "$type", "count": {"$sum": 1}}}]).to_list(None)
        stats_result = stats[0] if stats else {"total": 0, "avg_rating": 0}
        return {
            "total_places": stats_result["total"],
            "avg_rating": round(stats_result["avg_rating"] or 0, 2),
            "by_city": {s["_id"]: s["count"] for s in city_stats if s["_id"]},
            "by_type": {s["_id"]: s["count"] for s in type_stats if s["_id"]}
        }

    def _format_doc(self, doc):
        if doc and "_id" in doc: doc["_id"] = str(doc["_id"])
        return doc
