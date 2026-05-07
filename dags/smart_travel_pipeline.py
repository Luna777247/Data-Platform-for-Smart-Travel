"""
Smart Travel Pipeline DAG — Dynamic city-based pipelines.
Creates a separate DAG per city: Bronze → Silver → Gold.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import asyncio
import sys
import os

# Ensure Airflow can import src modules
sys.path.insert(0, "/opt/airflow")
sys.path.insert(0, "/opt/airflow/src")

default_args = {
    "owner": "smart-travel",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def create_city_dag(city: str) -> DAG:
    dag = DAG(
        f"smart_travel_{city}",
        default_args=default_args,
        description=f"Data pipeline for {city}",
        schedule_interval="@daily",
        catchup=False,
        max_active_runs=1,
        tags=["smart-travel", city],
    )

    # ── BRONZE ──────────────────────────────────────────
    def bronze_osm_task(**context):
        from src.collectors.osm_collector import OSMCollector
        from src.transformers.bronze_processor import BronzeProcessor
        from src.shared.db_client import get_mongo_client

        collector = OSMCollector(city)
        places = asyncio.run(collector.collect())

        mongo_client = get_mongo_client()
        processor = BronzeProcessor(mongo_client)
        inserted_count = asyncio.run(processor.process(places))

        context["ti"].xcom_push(key="bronze_osm_count", value=inserted_count)
        print(f"Inserted {inserted_count} OSM places for {city}")

    def bronze_google_task(**context):
        from src.collectors.google_enricher import GoogleEnricher
        from src.transformers.bronze_processor import BronzeProcessor
        from src.shared.db_client import get_mongo_client
        from airflow.models import Variable

        api_key = Variable.get("google_places_api_key", default_var="mock_api_key")

        enricher = GoogleEnricher(city, api_key)
        places = asyncio.run(enricher.enrich())

        mongo_client = get_mongo_client()
        processor = BronzeProcessor(mongo_client)
        inserted_count = asyncio.run(processor.process(places))

        context["ti"].xcom_push(key="bronze_google_count", value=inserted_count)
        print(f"Inserted {inserted_count} Google places for {city}")

    # ── SILVER ──────────────────────────────────────────
    def silver_task(**context):
        from src.transformers.silver_processor import SilverTransformer
        from src.shared.db_client import get_mongo_client

        mongo_client = get_mongo_client()
        processor = SilverTransformer(mongo_client)
        processed_count = asyncio.run(processor.process(city))

        context["ti"].xcom_push(key="silver_count", value=processed_count)
        print(f"Processed {processed_count} silver places for {city}")

    # ── GOLD ────────────────────────────────────────────
    def gold_task(**context):
        from src.transformers.gold_processor import GoldProcessor
        from src.shared.db_client import get_mongo_client

        mongo_client = get_mongo_client()
        processor = GoldProcessor(mongo_client)
        processed_count = asyncio.run(processor.process(city))

        context["ti"].xcom_push(key="gold_count", value=processed_count)
        print(f"Processed {processed_count} gold places for {city}")

    # Define tasks
    bronze_osm = PythonOperator(
        task_id="bronze_osm",
        python_callable=bronze_osm_task,
        dag=dag,
    )

    bronze_google = PythonOperator(
        task_id="bronze_google",
        python_callable=bronze_google_task,
        dag=dag,
    )

    silver = PythonOperator(
        task_id="silver",
        python_callable=silver_task,
        dag=dag,
    )

    gold = PythonOperator(
        task_id="gold",
        python_callable=gold_task,
        dag=dag,
    )

    # Dependencies: Bronze (parallel) → Silver → Gold
    [bronze_osm, bronze_google] >> silver >> gold

    return dag


# Create DAGs for each city
cities = ["hanoi", "hcm", "danang"]
for _city in cities:
    globals()[f"smart_travel_{_city}"] = create_city_dag(_city)
