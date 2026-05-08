import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.serving.postgres_loader import PostgresLoader

from src.shared.path_manager import get_path, DOTENV_PATH
from dotenv import load_dotenv

load_dotenv(DOTENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger("run_loader")

def main():
    config_path = get_path("infra/config/config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"❌ Configuration file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    try:
        minio_client = Minio(
            config['storage']['minio']['endpoint'],
            access_key=config['storage']['minio']['access_key'],
            secret_key=config['storage']['minio']['secret_key'],
            secure=False
        )
        
        db_config = config['database']['postgres']
        loader = PostgresLoader(db_config, minio_client)
        
        cities_env = os.getenv("SMART_TRAVEL_CITIES", "hanoi,hcm,danang")
        cities = [c.strip().lower() for c in cities_env.split(",") if c.strip()]
        
        logger.info(f"🚚 >>> LOADING DATA TO POSTGRES FOR {len(cities)} CITIES <<<")
        for city in cities:
            loader.load_city(city)
    except Exception as e:
        logger.error(f"❌ Postgres loading failed: {e}")

if __name__ == "__main__":
    main()
