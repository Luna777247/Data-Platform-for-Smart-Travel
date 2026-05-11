import logging
import yaml
import psycopg2
from pymongo import MongoClient

logger = logging.getLogger("verification")


def verify_migration(city: str, config: dict):
    """
    Kiểm soát chất lượng di trú:
    - So sánh số lượng record giữa Silver (MongoDB) và Serving (Postgres)
    """
    logger.info(f"Checking data consistency for {city}...")

    # 1. READ SILVER COUNT FROM MONGODB
    mongo_uri = config.get('database', {}).get('mongodb_uri') or config.get('storage', {}).get('mongodb_uri')
    db_name = config.get('database', {}).get('db_name', 'smart_travel_platform')
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[db_name]
    silver_count = db["silver_pois"].count_documents({"city": city})
    mongo_client.close()

    # 2. READ POSTGRES COUNT
    conn = psycopg2.connect(**config['database']['postgres'])
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM pois WHERE city = %s", (city,))
    pg_count = cur.fetchone()[0]

    # 3. REPORT
    if silver_count == pg_count:
        logger.info(f"Consistency OK: {silver_count} records in both layers.")
    else:
        logger.error(f"Consistency FAIL: Silver(MongoDB)={silver_count}, Postgres={pg_count}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    verify_migration("hanoi", cfg)
