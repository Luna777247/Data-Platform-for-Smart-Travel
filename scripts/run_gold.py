import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.analytics.gold_generator import GoldGenerator

from src.shared.path_manager import get_path, DOTENV_PATH
from dotenv import load_dotenv

load_dotenv(DOTENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger("run_gold")

def main():
    config_path = get_path("infra/config/config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"❌ Configuration file not found at {config_path}")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    try:
        client = Minio(
            config['storage']['minio']['endpoint'],
            access_key=config['storage']['minio']['access_key'],
            secret_key=config['storage']['minio']['secret_key'],
            secure=False
        )
        generator = GoldGenerator(client)
        logger.info("🏆 >>> GENERATING GOLD ANALYTICS <<<")
        generator.generate_analytics()
    except Exception as e:
        logger.error(f"❌ Gold layer generation failed: {e}")

if __name__ == "__main__":
    main()
