#!/usr/bin/env python3
"""
Smart Travel Data Pipeline - Airflow DAG

DAG Structure:
  Bronze Layer → Silver Layer → Gold Layer → Notification

Dynamic DAGs generated per city based on SMART_TRAVEL_CITIES environment variable.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Callable
import asyncio
import logging
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
from airflow.exceptions import AirflowException

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Cities to process (can be overridden via Airflow Variables)
CITIES = [c.strip().lower() for c in os.getenv("SMART_TRAVEL_CITIES", "hanoi,hcm,danang").split(",") if c.strip()]

# Default DAG arguments
DEFAULT_ARGS: Dict[str, Any] = {
    "owner": "smart-travel",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "pool": "smart_travel_dag_pool",
}

# Shared DAG configuration
DEFAULT_DAG_CONFIG: Dict[str, Any] = {
    "catchup": False,
    "max_active_runs": 1,
    "description": "Smart Travel Data Platform Pipeline",
    "tags": ["smart-travel", "data-pipeline"],
}


# ============================================================================
# TASK DEFINITIONS
# ============================================================================
def bronze_osm_collector(city: str, **context) -> Dict[str, Any]:
    """
    Bronze Layer - OSM Data Collection

    Collects Points of Interest from OpenStreetMap for the specified city.
    """
    try:
        # Lazy imports to avoid dependency issues
        from src.collectors.osm_collector import OSMCollector

        logger.info(f"🔵 Bronze: Collecting OSM data for {city}...")

        collector = OSMCollector(city)
        # Create new event loop for async call in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            places = loop.run_until_complete(collector.collect())
        finally:
            loop.close()

        # Store count in XCom for downstream tasks
        count = len(places)
        context["ti"].xcom_push(key="bronze_osm_count", value=count)

        logger.info(f"✅ Bronze: {count} OSM places collected for {city}")
        return {"status": "success", "count": count}

    except Exception as e:
        logger.error(f"❌ Bronze OSM failed for {city}: {e}", exc_info=True)
        raise AirflowException(f"OSM collection failed: {e}")


def bronze_google_enrichment(city: str, **context) -> Dict[str, Any]:
    """
    Bronze Layer - Google Places Enrichment

    Enriches OSM data with Google Places API information.
    """
    try:
        from src.collectors.google_enricher import GoogleEnricher
        import os

        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise AirflowException("GOOGLE_PLACES_API_KEY not set")

        logger.info(f"🔵 Bronze: Enriching with Google Places data for {city}...")

        enricher = GoogleEnricher(city, api_key)
        # Create new event loop for async call in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            places = loop.run_until_complete(enricher.enrich())
        finally:
            loop.close()

        count = len(places)
        context["ti"].xcom_push(key="bronze_google_count", value=count)

        logger.info(f"✅ Bronze: {count} Google places enriched for {city}")
        return {"status": "success", "count": count}

    except Exception as e:
        logger.error(f"❌ Bronze Google failed for {city}: {e}", exc_info=True)
        # Don't fail the pipeline if Google enrichment fails
        logger.warning(f"⚠️ Continuing without Google enrichment")
        return {"status": "warning", "count": 0}


def silver_transform(city: str, **context) -> Dict[str, Any]:
    """
    Silver Layer - Data Transformation

    Cleans, validates, and standardizes data from bronze layer.
    """
    try:
        from src.transformers.silver_processor import SilverProcessor

        logger.info(f"🟩 Silver: Processing data for {city}...")

        processor = SilverProcessor()
        processor.process_city(city)

        count = context["ti"].xcom_pull(
            task_ids="bronze_osm", key="bronze_osm_count"
        )
        context["ti"].xcom_push(key="silver_count", value=count)

        logger.info(f"✅ Silver: {count} places processed for {city}")
        return {"status": "success", "count": count}

    except Exception as e:
        logger.error(f"❌ Silver processing failed for {city}: {e}", exc_info=True)
        raise AirflowException(f"Silver processing failed: {e}")


def gold_analytics(city: str, **context) -> Dict[str, Any]:
    """
    Gold Layer - Analytics & Aggregation

    Generates analytics, aggregations, and KPIs from silver data.
    """
    try:
        from src.analytics.gold_generator import GoldGenerator
        from src.shared.minio_client import get_minio_client

        logger.info(f"🟨 Gold: Generating analytics for {city}...")

        minio_client = get_minio_client()
        generator = GoldGenerator(minio_client)
        # Create new event loop for async call in sync context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(generator.generate_for_city(city))
        finally:
            loop.close()

        context["ti"].xcom_push(key="gold_result", value=result)

        logger.info(f"✅ Gold: Analytics generated for {city}")
        return {"status": "success", "result": result}

    except Exception as e:
        logger.error(f"❌ Gold generation failed for {city}: {e}", exc_info=True)
        raise AirflowException(f"Gold generation failed: {e}")


def notify_completion(city: str, **context) -> str:
    """
    Notification Task

    Sends completion notification.
    """
    bronze_count = context["ti"].xcom_pull(
        task_ids="bronze_osm", key="bronze_osm_count"
    )
    silver_count = context["ti"].xcom_pull(
        task_ids="silver_transform", key="silver_count"
    )

    message = f"""
    ✅ Pipeline completed for {city}
    - Bronze: {bronze_count} places
    - Silver: {silver_count} places
    """

    logger.info(message)
    return message


# ============================================================================
# DAG FACTORY
# ============================================================================
def create_city_dag(city: str) -> DAG:
    """
    Factory function to create a DAG for a specific city.

    Args:
        city: City name (e.g., 'hanoi', 'hochiminh')

    Returns:
        Configured DAG instance
    """

    dag_id = f"smart_travel_{city}"

    dag = DAG(
        dag_id=dag_id,
        default_args=DEFAULT_ARGS,
        schedule_interval="@daily",  # Run daily
        description=f"Smart Travel data pipeline for {city}",
        catchup=False,
        max_active_runs=1,
        tags=["smart-travel", city],
    )

    with dag:
        # Bronze Layer - Data Collection
        task_bronze_osm = PythonOperator(
            task_id="bronze_osm",
            python_callable=bronze_osm_collector,
            op_kwargs={"city": city},
            provide_context=True,
            pool_slots=1,
        )

        task_bronze_google = PythonOperator(
            task_id="bronze_google",
            python_callable=bronze_google_enrichment,
            op_kwargs={"city": city},
            provide_context=True,
            pool_slots=1,
        )

        # Silver Layer - Transformation
        task_silver = PythonOperator(
            task_id="silver_transform",
            python_callable=silver_transform,
            op_kwargs={"city": city},
            provide_context=True,
            pool_slots=1,
        )

        # Gold Layer - Analytics
        task_gold = PythonOperator(
            task_id="gold_analytics",
            python_callable=gold_analytics,
            op_kwargs={"city": city},
            provide_context=True,
            pool_slots=1,
        )

        # Notification
        task_notify = PythonOperator(
            task_id="notify_completion",
            python_callable=notify_completion,
            op_kwargs={"city": city},
            provide_context=True,
            trigger_rule="all_done",
        )

        # Task Dependencies
        [task_bronze_osm, task_bronze_google] >> task_silver >> task_gold >> task_notify

    return dag


# ============================================================================
# GENERATE DAGS
# ============================================================================
# Dynamically generate a DAG for each city
for city in CITIES:
    city = city.strip().lower()
    if city:
        dag_id = f"smart_travel_{city}"
        globals()[dag_id] = create_city_dag(city)
        logger.info(f"✅ Created DAG: {dag_id}")

logger.info(f"🚀 Smart Travel Pipeline DAG factory initialized for cities: {CITIES}")
