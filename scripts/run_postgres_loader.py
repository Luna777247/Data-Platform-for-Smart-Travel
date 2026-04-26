import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from minio import Minio
from src.serving.postgres_loader import PostgresLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_loader")

def main():
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    minio_client = Minio(
        config['storage']['minio']['endpoint'],
        config['storage']['minio']['access_key'],
        config['storage']['minio']['secret_key'],
        secure=False
    )
    
    db_config = config['database']['postgres']
    loader = PostgresLoader(db_config, minio_client)
    
    cities = ["hanoi", "ho_chi_minh", "da_nang"]
    for city in cities:
        loader.load_city(city)

if __name__ == "__main__":
    main()
