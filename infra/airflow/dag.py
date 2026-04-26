# airflow/dag.py
from datetime import datetime, timedelta
import asyncio
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

# Mocked imports for the example
from src.collectors.osm_collector import OSMCollector
from src.collectors.google_enrichor import GoogleEnrichor
# Assuming repository is available in python path
from app.db.repository import PlaceRepository
from app.models.place import PipelineStatus

async def run_pipeline_async(city: str, place_type: str, target: int = 150):
    repo = PlaceRepository()
    osm = OSMCollector()
    enrichor = GoogleEnrichor()
    
    try:
        # 1. Update status to running
        await repo.update_pipeline_status(PipelineStatus(city=city, type=place_type, status="running", target=target))
        
        # 2. Collect from OSM
        places = osm.fetch_data(city, place_type, limit=target)
        
        # 3. Enrich in batch (async)
        enriched_places = await enrichor.enrich_batch(places, city)
        
        # 4. Upsert to DB with change detection
        collected_count = 0
        for p in enriched_places:
            result = await repo.upsert_place(p)
            if result in ["CREATED", "UPDATED"]:
                collected_count += 1
        
        # 5. Final status update
        await repo.update_pipeline_status(PipelineStatus(
            city=city, type=place_type, status="done", 
            collected=collected_count, target=target, 
            end_time=datetime.utcnow()
        ))
        
    except Exception as e:
        logging.error(f"[ERROR] Pipeline failed for {city}-{place_type}: {e}")
        await repo.update_pipeline_status(PipelineStatus(
            city=city, type=place_type, status="failed", 
            error_message=str(e), end_time=datetime.utcnow()
        ))

def run_pipeline_wrapper(city: str, place_type: str):
    asyncio.run(run_pipeline_async(city, place_type))

default_args = {
    'owner': 'lakehouse_admin',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'smart_tourism_production_v2',
    default_args=default_args,
    start_date=datetime(2026, 4, 1),
    schedule_interval='0 0 * * 1', # Monday 00:00
    catchup=False,
    tags=['production', 'lakehouse'],
) as dag:

    cities = ["hanoi", "hcm", "danang"]
    types = ["attraction", "restaurant", "hotel"]

    for city in cities:
        for t in types:
            PythonOperator(
                task_id=f"harvest_{city}_{t}",
                python_callable=run_pipeline_wrapper,
                op_kwargs={'city': city, 'place_type': t},
            )
