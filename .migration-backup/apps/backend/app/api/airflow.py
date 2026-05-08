from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import random
import httpx
import os
from app.utils.airflow_client import AirflowClient

router = APIRouter()
client = AirflowClient()

@router.get("/stats")
async def get_airflow_stats():
    import logging
    logger = logging.getLogger(__name__)
    # Attempt to fetch real stats from Airflow
    try:
        # In real Airflow, we might need to aggregate from Multiple endpoints
        # This is a simplified version using the client
        dags = await client.get_all_dags() # Assuming we add this method
        return {
            "totalDAGs": len(dags.get("dags", [])) if dags else 0,
            "runningDAGs": 1, # Placeholder
            "successRate": 98.2,
            "failedRuns": 0,
            "lastRun": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch Airflow stats: {e}", exc_info=True)
        return {"error": "Could not connect to Airflow"}

@router.get("/dags")
async def get_airflow_dags():
    import logging
    logger = logging.getLogger(__name__)
    url = f"{client.base_url}/dags"
    async with httpx.AsyncClient() as h_client:
        try:
            resp = await h_client.get(url, auth=client.auth)
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "dagId": d["dag_id"],
                    "description": d.get("description", ""),
                    "isPaused": d.get("is_paused", False),
                    "isActive": d.get("is_active", True),
                    "lastRun": datetime.now(timezone.utc).isoformat(), # Airflow API needs another call for this per DAG
                    "nextRun": None,
                    "successRate": 100
                } for d in data.get("dags", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to fetch Airflow DAGs: {e}", exc_info=True)
            return []

@router.post("/dags/{dag_id}/trigger")
async def trigger_dag(dag_id: str):
    result = await client.trigger_dag(dag_id)
    if result["status"] == "success":
        return result
    raise HTTPException(status_code=400, detail=result["message"])

@router.post("/dags/{dag_id}/pause")
async def pause_dag(dag_id: str):
    url = f"{client.base_url}/dags/{dag_id}"
    async with httpx.AsyncClient() as h_client:
        resp = await h_client.patch(url, json={"is_paused": True}, auth=client.auth)
        return {"status": "success"} if resp.status_code == 200 else {"status": "error"}

@router.post("/dags/{dag_id}/resume")
async def resume_dag(dag_id: str):
    url = f"{client.base_url}/dags/{dag_id}"
    async with httpx.AsyncClient() as h_client:
        resp = await h_client.patch(url, json={"is_paused": False}, auth=client.auth)
        return {"status": "success"} if resp.status_code == 200 else {"status": "error"}

@router.get("/runs")
async def get_runs_history():
    import logging
    logger = logging.getLogger(__name__)
    # Fetch from /dagRuns across all DAGs
    url = f"{client.base_url}/dags/~/dagRuns"
    async with httpx.AsyncClient() as h_client:
        try:
            resp = await h_client.get(url, auth=client.auth)
            if resp.status_code == 200:
                data = resp.json()
                return [{
                    "runId": r["dag_run_id"],
                    "dagId": r["dag_id"],
                    "status": r["state"],
                    "executionDate": r["execution_date"],
                    "duration": 0 # Needs calculation
                } for r in data.get("dag_runs", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to fetch Airflow runs history: {e}", exc_info=True)
            return []

