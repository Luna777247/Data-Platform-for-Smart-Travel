from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import random
import uuid
from app.db.repository import PlaceRepository
from app.utils.auth import create_access_token, check_admin_role, TokenData, get_current_user
from pydantic import BaseModel

router = APIRouter()
repo = PlaceRepository()

class LoginRequest(BaseModel):
    username: str
    password: str

# --- Authentication ---
async def _login(data: LoginRequest):
    users = await repo.get_users()
    user = next((u for u in users if u["email"] == data.username), None)
    
    if not user or data.password != "admin": # Demo password
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/auth/login")
async def login(data: LoginRequest):
    return await _login(data)


@router.post("/login")
async def login_legacy(data: LoginRequest):
    return await _login(data)


# --- Enterprise Observability ---
@router.get("/quality-stats")
async def get_data_quality_stats(admin_user: TokenData = Depends(check_admin_role)):
    cursor = repo.db["data_quality_stats"].find({}).sort("timestamp", -1).limit(20)
    return [repo._format_doc(doc) async for doc in cursor]

@router.get("/lineage/{u_key}")
async def get_data_lineage(u_key: str, admin_token: TokenData = Depends(get_current_user)):
    place = await repo.db["places"].find_one({"u_key": u_key})
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    return {
        "u_key": u_key,
        "name": place.get("name"),
        "lineage": {
            "source": place.get("_lineage_source", "unknown"),
            "bronze_files": place.get("_lineage_files", "automated"),
            "processed_at": place.get("last_updated"),
            "enrichment": "google_places_api" if place.get("rating") else "none"
        }
    }

# --- Users (Protected) ---
@router.get("/users")
async def get_users(admin_user: TokenData = Depends(check_admin_role)):
    users = await repo.get_users()
    if not users:
        return []
    return users

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_user: TokenData = Depends(check_admin_role)):
    await repo.delete_user(user_id)
    return {"status": "success", "message": "User deleted"}

# --- Roles ---
@router.get("/roles")
async def get_roles(admin_user: TokenData = Depends(check_admin_role)):
    roles = await repo.get_roles()
    if not roles:
        return [
            {
                "id": "r1",
                "name": "Administrator",
                "description": "Full access to all system features and management",
                "permissions": ["all", "manage_users", "manage_keys", "system_config"]
            }
        ]
    return roles

# --- API Keys ---
@router.get("/keys/rapidapi")
async def get_rapidapi_keys(admin_user: TokenData = Depends(check_admin_role)):
    keys = await repo.get_api_keys()
    return keys

@router.post("/keys/rapidapi")
async def add_rapidapi_key(data: dict, admin_user: TokenData = Depends(check_admin_role)):
    key_payload = {
        "short_key": f"{data['key'][:10]}...",
        "label": data.get("label", "New Key"),
        "status": "Ready",
        "status_code": 200,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await repo.upsert_api_key(key_payload)
    return {"status": "success", "message": "Key added"}

@router.delete("/keys/rapidapi/{id}")
async def delete_rapidapi_key(id: str, admin_user: TokenData = Depends(check_admin_role)):
    await repo.delete_api_key(id)
    return {"status": "success", "message": "Key deleted"}

# --- Backups ---
@router.get("/backups")
async def get_backups(admin_user: TokenData = Depends(check_admin_role)):
    backups = await repo.get_backups()
    return backups

@router.post("/backups")
async def create_backup(admin_user: TokenData = Depends(check_admin_role)):
    backup_id = str(uuid.uuid4())[:8]
    backup_payload = {
        "id": backup_id,
        "name": f"manual_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.sql",
        "size": 0,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "status": "processing"
    }
    await repo.create_backup_record(backup_payload)
    return backup_payload

# --- Settings ---
@router.get("/system/settings")
async def get_system_settings(admin_user: TokenData = Depends(check_admin_role)):
    settings = await repo.get_settings()
    return settings

@router.put("/system/settings")
async def update_system_settings(settings: dict, admin_user: TokenData = Depends(check_admin_role)):
    await repo.update_settings(settings)
    return {"status": "success", "message": "Settings updated"}

