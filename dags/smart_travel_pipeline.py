from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os
import sys

# Đảm bảo Airflow có thể import các module từ src
sys.path.append('/opt/airflow/plugins')

def fetch_data_task(source, **kwargs):
    # Lấy city từ config của run, fallback về hanoi
    conf = kwargs.get('dag_run').conf or {}
    city = conf.get('city', 'hanoi')
    
    print(f"🚀 Fetching {source} data for {city}...")
    from src.ingestion.bronze_writer import BronzeWriter
    writer = BronzeWriter()
    
    sample_data = [{"name": f"Place {source} {city}", "lat": 21.0, "lon": 105.0}]
    file_path = writer.write_raw(source, city, sample_data)
    return file_path

def process_silver_task(**kwargs):
    conf = kwargs.get('dag_run').conf or {}
    city = conf.get('city', 'hanoi')
    
    print(f"🧹 Processing Silver for {city}...")
    from src.ingestion.silver_processor import SilverProcessor
    processor = SilverProcessor()
    
    processor.process_osm_to_silver(city)
    processor.merge_and_finalize(city)
    return f"Silver processed for {city}"

def load_gold_task(**kwargs):
    conf = kwargs.get('dag_run').conf or {}
    city = conf.get('city', 'hanoi')
    
    print(f"🏆 Loading Gold for {city}...")
    import asyncio
    from src.serving.gold_server import GoldServer
    from app.db.client import MongoClient
    
    async def run_load():
        await MongoClient.connect()
        server = GoldServer()
        await server.load_city_to_gold(city)
        await MongoClient.disconnect()
        
    asyncio.run(run_load())
    return f"Gold loaded for {city}"

# Định nghĩa DAG
default_args = {
    'owner': 'smart_travel',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'smart_travel_ingestion_v2',
    default_args=default_args,
    description='Configurable Smart Travel Data Pipeline',
    schedule_interval=None, # Tắt schedule để chạy Manual/API call
    start_date=days_ago(1),
    catchup=False,
    tags=['production', 'travel'],
) as dag:

    t1 = PythonOperator(
        task_id='fetch_osm',
        python_callable=fetch_data_task,
        op_kwargs={'source': 'osm'},
    )

    t2 = PythonOperator(
        task_id='fetch_google',
        python_callable=fetch_data_task,
        op_kwargs={'source': 'google'},
    )

    t3 = PythonOperator(
        task_id='silver_processing',
        python_callable=process_silver_task,
    )

    t4 = PythonOperator(
        task_id='gold_loading',
        python_callable=load_gold_task,
    )

    [t1, t2] >> t3 >> t4
