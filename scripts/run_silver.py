import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.ingestion.silver_processor import SilverProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_silver")

def main():
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    client = Minio(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key'],
        secure=False
    )
    
    processor = SilverProcessor(client)
    
    cities = ["hanoi", "ho_chi_minh", "da_nang"]
    for city in cities:
        processor.process_city(city)

if __name__ == "__main__":
    main()
