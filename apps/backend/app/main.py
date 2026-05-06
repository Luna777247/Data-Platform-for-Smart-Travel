# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.api import places, dashboard, system, airflow, admin
from app.db.client import MongoClient
from app.db.repository import PlaceRepository
from app.models.place import PipelineStatus
from datetime import datetime, timezone
import os
import time
import logging

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.utils.airflow_client import AirflowClient

app = FastAPI(title="Smart Travel Production API", version="2.1.0")
repo = PlaceRepository()
airflow_client = AirflowClient()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("smart_travel.api")

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await MongoClient.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    await MongoClient.disconnect()

# Request logging + metrics
@app.middleware("http")
async def log_and_measure_requests(request: Request, call_next):
    start = time.perf_counter()
    response: Response | None = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start
        path = request.url.path
        method = request.method
        HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status=str(status_code)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration)
        logger.info("%s %s -> %s (%.3fs)", method, path, status_code, duration)

# Include Routers
app.include_router(places.router, prefix="/api", tags=["Places"])
app.include_router(dashboard.router, prefix="/api/smart-travel/dashboard", tags=["Dashboard"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(airflow.router, prefix="/api/airflow", tags=["Airflow"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Smart Travel Data Platform API",
        "status": "online",
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/pipeline/run")
async def trigger_pipeline(city: str, type: str):
    # Check if already running
    current_status = await repo.get_pipeline_status(city=city, place_type=type)
    if current_status and current_status[0].get("status") == "running":
        return {"status": "error", "message": f"Pipeline for {city}-{type} is already running"}

    # Register start of job
    status = PipelineStatus(city=city, type=type, status="running", collected=0, target=150)
    await repo.update_pipeline_status(status)
    
    # PRODUCTION: Call Airflow API
    dag_id = f"ingest_{city.lower()}_{type.lower()}"
    result = await airflow_client.trigger_dag(
        dag_id=dag_id,
        conf={"city": city, "type": type}
    )
    
    if result["status"] == "success":
        return {"status": "triggered", "city": city, "type": type, "airflow_response": result["data"]}
    else:
        return {"status": "warning", "message": "Pipeline registered but Airflow trigger failed", "details": result.get("message")}

@app.get("/pipeline/status")
async def get_pipeline_status(city: str = None, type: str = None):
    return await repo.get_pipeline_status(city, type)

@app.get("/dashboard/pipeline-metrics")
async def get_pipeline_metrics():
    return await repo.get_pipeline_metrics()
