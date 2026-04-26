import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.analytics.gold_generator import GoldGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_gold")

def main():
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    client = Minio(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key'],
        secure=False
    )
    
    generator = GoldGenerator(client)
    generator.generate_analytics()

if __name__ == "__main__":
    main()
