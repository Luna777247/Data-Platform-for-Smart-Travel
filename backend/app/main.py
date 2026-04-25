# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.api import places
from app.db.client import MongoClient
from app.db.repository import PlaceRepository
from app.models.place import PipelineStatus
from datetime import datetime
import os

app = FastAPI(title="Smart Travel Production API", version="2.1.0")
repo = PlaceRepository()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    try:
        await MongoClient.connect()
        # Initialize indexes for production scalability
        await repo.init_indexes()
    except Exception as e:
        print(f"[ERROR] Database startup failed: {e}. API will run in OFFLINE mode.")

@app.on_event("shutdown")
async def shutdown_db_client():
    await MongoClient.disconnect()

app.include_router(places.router, prefix="/places", tags=["Places"])

@app.get("/")
async def root():
    return {"message": "Smart Travel API v2.1.0 is healthy", "env": os.getenv("ENV", "production")}

# --- PIPELINE CONTROL ---

@app.post("/pipeline/run")
async def trigger_pipeline(city: str, type: str):
    # Check if already running
    current_status = await repo.get_pipeline_status(city=city, place_type=type)
    if current_status and current_status[0].get("status") == "running":
        return {"status": "error", "message": f"Pipeline for {city}-{type} is already running"}

    # Register start of job
    status = PipelineStatus(city=city, type=type, status="running", collected=0, target=150)
    await repo.update_pipeline_status(status)
    
    # In production, call Airflow API here
    # For now, simulate success trigger
    return {"status": "triggered", "city": city, "type": type}

@app.get("/pipeline/status")
async def get_pipeline_status(city: str = None, type: str = None):
    return await repo.get_pipeline_status(city, type)

# --- DASHBOARD MONITOR ---

@app.get("/dashboard/pipeline-metrics")
async def get_pipeline_metrics():
    """Returns summarized metrics for the Pipeline Monitor dash."""
    return await repo.get_pipeline_metrics()
