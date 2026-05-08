from fastapi import APIRouter
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

router = APIRouter()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
DATA_FILE = STORAGE_DIR / "data" / "pois.json"
PIPELINE_STATUS_FILE = STORAGE_DIR / "metadata" / "pipeline_status.json"

@router.get("/status")
async def get_system_status():
    # Derive stats from pipeline_status.json
    total_runs = 0
    success_rate = 0
    runs_24h = 0
    
    if PIPELINE_STATUS_FILE.exists():
        with open(PIPELINE_STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
            total_runs = len(status_data)
            success_count = sum(1 for r in status_data if r.get("status") == "done")
            
            # Tính toán tiến độ làm giàu thực tế
            total_osm = sum(r.get("collected", 0) for r in status_data)
            total_enriched = sum(r.get("enriched", 0) for r in status_data)
            
            success_rate = round((total_enriched / total_osm * 100), 1) if total_osm > 0 else 0
            
            # Mock 24h runs for now or calculate if start_time exists
            runs_24h = sum(1 for r in status_data if r.get("status") == "done") 

    
    # Calculate uptime (mocked)
    uptime = "4 days, 12 hours"
    
    return {
        "status": "healthy",
        "health": "healthy",
        "uptime": uptime,
        "activeUsers": 3,
        "totalConnections": 5,
        "connections": {"active": 1, "total": 5},
        "schedules": {"total": 5, "active": 2},
        "runs": {"total": total_runs, "last24h": runs_24h},
        "activity": {"successRate": success_rate, "totalRuns": total_runs},
        "performance": {"successRate": success_rate, "avgResponseTime": 245}
    }

@router.get("/system/status")
async def get_system_status_alias():
    return await get_system_status()

@router.get("/monitoring")
async def get_monitoring_data():
    return await get_system_status()

@router.get("/analytics/success-rate-history")
async def get_success_rate_history(days: int = 7):
    # Mock history data for charts
    history = []
    base_success = 98.2
    for i in range(days, 0, -1):
        d = datetime.now(timezone.utc).timestamp() - (i * 86400)
        history.append({
            "date": datetime.fromtimestamp(d).strftime("%Y-%m-%d"),
            "successRate": base_success + (i % 2) - (i % 3) / 10
        })
    return {"data": history}

@router.get("/data")
async def get_data_explorer():
    total_records = 0
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            total_records = len(data)
            
    # Breakdown from pipeline_status
    breakdown = []
    if PIPELINE_STATUS_FILE.exists():
        with open(PIPELINE_STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
            # Group by city/type
            for item in status_data:
                if item.get("collected", 0) > 0:
                    breakdown.append({
                        "connectionId": f"{item['city']}-{item['type']}",
                        "connectionName": f"OSM Enrichment: {item['city'].capitalize()} ({item['type']})",
                        "totalRecords": item['collected'],
                        "enrichedRecords": item.get('enriched', 0),
                        "runCount": 1,
                        "status": item['status'],
                        "lastRun": item.get("end_time") or datetime.now(timezone.utc).isoformat(),
                        "avgExecutionTime": 12500, # 12.5s mock
                        "description": f"Extracted {item['type']} data for {item['city']}"
                    })

    return {
        "summary": {
            "totalRuns": len(breakdown),
            "totalRecords": total_records,
            "avgExecutionTime": 12500,
            "estimatedDataSize": f"{round(os.path.getsize(DATA_FILE) / 1024 / 1024, 2)} MB" if DATA_FILE.exists() else "0 MB"
        },
        "connectionBreakdown": breakdown
    }

@router.get("/connections")
async def get_connections():
    return [
       {
           "id": "mongo-atlas",
           "name": "MongoDB Atlas",
           "type": "database",
           "status": "connected",
           "lastUsed": datetime.now(timezone.utc).isoformat()
       },
       {
           "id": "osm-api",
           "name": "OpenStreetMap Overpass API",
           "type": "api",
           "status": "connected",
           "lastUsed": datetime.now(timezone.utc).isoformat()
       },
       {
           "id": "google-places",
           "name": "Google Places API",
           "type": "api",
           "status": "connected",
           "lastUsed": datetime.now(timezone.utc).isoformat()
       }
    ]

@router.get("/runs")
async def get_runs():
    runs = []
    if PIPELINE_STATUS_FILE.exists():
        with open(PIPELINE_STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
            for i, item in enumerate(status_data[:50]): # Top 50
                runs.append({
                    "id": f"run-{i}",
                    "connectionId": f"{item['city']}-{item['type']}",
                    "status": item['status'],
                    "startTime": item.get("start_time"),
                    "endTime": item.get("end_time"),
                    "recordsExtracted": item.get("collected", 0),
                    "logSummary": f"Successfully processed {item['collected']} records for {item['city']}"
                })
    return runs

# --- RAPIDAPI KEY MANAGEMENT ---

KEYS_FILE = STORAGE_DIR / "configs" / "rapidapi_keys.json"
KEY_REPORT_FILE = STORAGE_DIR / "logs" / "key_report.json"

@router.get("/keys/rapidapi")
async def get_rapidapi_keys():
    keys = []
    if KEYS_FILE.exists():
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)
    
    report = {}
    if KEY_REPORT_FILE.exists():
        with open(KEY_REPORT_FILE, "r", encoding="utf-8") as f:
            report = json.load(f)
    
    # Heuristic mapping: key_report usually uses RAPID_API_KEY1, RAPID_API_KEY2...
    # We'll try to match by index if possible, or just return the report separately
    # For a better UI, we'll return a list of objects
    result = []
    for i, k in enumerate(keys):
        # Find status in report
        key_label = f"RAPID_API_KEY{i+1}"
        status_code = report.get(key_label, 200)
        
        status = "Ready"
        if status_code == 403: status = "Blocked (403)"
        elif status_code == 429: status = "Rate Limited (429)"
        elif status_code == 401: status = "Invalid (401)"
        
        result.append({
            "id": i + 1,
            "key": k,
            "short_key": f"{k[:8]}...{k[-4:]}",
            "status": status,
            "status_code": status_code,
            "label": key_label
        })
    
    return result

@router.post("/keys/rapidapi")
async def add_rapidapi_key(payload: dict):
    new_key = payload.get("key")
    if not new_key:
        return {"status": "error", "message": "Key is required"}
    
    keys = []
    if KEYS_FILE.exists():
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)
    
    if new_key in keys:
        return {"status": "error", "message": "Key already exists"}
    
    keys.append(new_key)
    
    os.makedirs(KEYS_FILE.parent, exist_ok=True)
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2)
        
    return {"status": "success", "message": "Key added successfully"}

@router.delete("/keys/rapidapi/{index}")
async def delete_rapidapi_key(index: int):
    # index is 1-based to match the UI ID
    idx = index - 1
    
    keys = []
    if KEYS_FILE.exists():
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            keys = json.load(f)
    
    if 0 <= idx < len(keys):
        keys.pop(idx)
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=2)
        return {"status": "success", "message": "Key deleted successfully"}
    
    return {"status": "error", "message": "Key not found"}

# --- OSM CONFIGURATION ---

CITIES_FILE = STORAGE_DIR / "configs" / "cities.json"
OSM_SETTINGS_FILE = STORAGE_DIR / "configs" / "osm_settings.json"

@router.get("/osm/config")
async def get_osm_config():
    cities = {}
    if CITIES_FILE.exists():
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            cities = json.load(f)
    
    settings = {}
    if OSM_SETTINGS_FILE.exists():
        with open(OSM_SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            
    return {
        "cities": cities,
        "overpass_urls": settings.get("overpass_urls", [])
    }

@router.put("/osm/config")
async def update_osm_config(payload: dict):
    cities = payload.get("cities")
    urls = payload.get("overpass_urls")
    
    if cities is not None:
        with open(CITIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cities, f, ensure_ascii=False, indent=2)
            
    if urls is not None:
        with open(OSM_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"overpass_urls": urls}, f, indent=2)
            
    return {"status": "success", "message": "OSM configuration updated successfully"}

# --- ENRICHMENT CONFIGURATION ---

ENRICHMENT_SETTINGS_FILE = STORAGE_DIR / "configs" / "enrichment_settings.json"

@router.get("/enrichment/config")
async def get_enrichment_config():
    settings = {}
    if ENRICHMENT_SETTINGS_FILE.exists():
        with open(ENRICHMENT_SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    return settings

@router.put("/enrichment/config")
async def update_enrichment_config(payload: dict):
    with open(ENRICHMENT_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return {"status": "success", "message": "Enrichment configuration updated successfully"}
