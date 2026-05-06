import httpx
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AirflowClient:
    def __init__(self):
        self.base_url = os.getenv("AIRFLOW_URL", "http://localhost:8080/api/v1")
        self.username = os.getenv("AIRFLOW_USER", "admin")
        self.password = os.getenv("AIRFLOW_PASSWORD", "admin")
        self.auth = (self.username, self.password)

    async def trigger_dag(self, dag_id: str, conf: Dict[str, Any] = None) -> Dict[str, Any]:
        """Triggers a DAG run in Airflow."""
        url = f"{self.base_url}/dags/{dag_id}/dagRuns"
        payload = {
            "conf": conf or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, 
                    json=payload, 
                    auth=self.auth,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {"status": "success", "data": response.json()}
                else:
                    logger.error(f"Airflow Trigger Failed ({response.status_code}): {response.text}")
                    return {"status": "error", "message": response.text}
            except Exception as e:
                logger.error(f"Airflow Connection Error: {e}")
                return {"status": "error", "message": str(e)}

    async def get_all_dags(self) -> Dict[str, Any]:
        """Fetches all DAGs from Airflow."""
        url = f"{self.base_url}/dags"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, auth=self.auth)
                return response.json() if response.status_code == 200 else {}
            except:
                return {}

    async def get_dag_status(self, dag_id: str) -> Dict[str, Any]:
        """Fetches status of a specific DAG."""
        url = f"{self.base_url}/dags/{dag_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, auth=self.auth)
                return response.json() if response.status_code == 200 else {}
            except:
                return {}

