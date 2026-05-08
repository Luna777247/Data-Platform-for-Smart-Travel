import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.ingestion.silver_processor import SilverProcessor

from src.shared.path_manager import get_path, DOTENV_PATH
from dotenv import load_dotenv

load_dotenv(DOTENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger("run_silver")

def main():
    config_path = get_path("infra/config/config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"❌ Configuration file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # SilverProcessor now handles both local and MinIO fallback internally if updated, 
    # but the current implementation in src/ingestion/silver_processor.py uses PlaceRepository (MongoDB)
    processor = SilverProcessor()
    
    cities_env = os.getenv("SMART_TRAVEL_CITIES", "hanoi,hcm,danang")
    cities = [c.strip().lower() for c in cities_env.split(",") if c.strip()]
    
    for city in cities:
        logger.info(f"✨ >>> PROCESSING SILVER LAYER FOR: {city.upper()} <<<")
        try:
            processor.process_city(city)
        except Exception as e:
            logger.error(f"❌ Failed to process {city}: {e}")

if __name__ == "__main__":
    main()
