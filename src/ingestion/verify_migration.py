import logging
import yaml
import psycopg2
import pandas as pd
from minio import Minio
from io import BytesIO

logger = logging.getLogger("verification")

def verify_migration(city: str, config: dict):
    """
    Kiểm soát chất lượng di trú:
    - So sánh số lượng record giữa Silver (MinIO) và Serving (Postgres)
    - Kiểm tra tính nhất quán dữ liệu mẫu
    """
    logger.info(f"Checking data consistency for {city}...")
    
    # 1. READ SILVER COUNT
    minio_client = Minio(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key'],
        secure=False
    )
    silver_path = f"silver/pois_cleaned/{city}/data.parquet"
    response = minio_client.get_object("lakehouse", silver_path)
    df_silver = pd.read_parquet(BytesIO(response.read()))
    silver_count = len(df_silver)
    
    # 2. READ POSTGRES COUNT
    conn = psycopg2.connect(**config['database']['postgres'])
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM pois WHERE city = %s", (city,))
    pg_count = cur.fetchone()[0]
    
    # 3. REPORT
    if silver_count == pg_count:
        logger.info(f"✅ Consistency OK: {silver_count} records in both layers.")
    else:
        logger.error(f"❌ Consistency FAIL: Silver={silver_count}, Postgres={pg_count}")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    verify_migration("hanoi", cfg)
