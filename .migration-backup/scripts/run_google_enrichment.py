import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import asyncio
import pandas as pd
import logging
import json
from dotenv import load_dotenv
from src.shared.path_manager import get_path, KEY_REPORT_PATH, DOTENV_PATH
from src.collectors.google_enrichor import GoogleEnrichor

# Nạp API Keys từ .env
load_dotenv(DOTENV_PATH)

# LỌC KEY: Chỉ lấy những Key trả về 200 trong báo cáo mới nhất
try:
    with open(KEY_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)
    keys_to_use = [os.getenv(k) for k, status in report.items() if status == 200]
except:
    keys_to_use = [os.getenv(f"RAPID_API_KEY{i}") for i in range(1, 21) if os.getenv(f"RAPID_API_KEY{i}")]

logging.info(f"🔑 Final Key Selection: {len(keys_to_use)} working keys ready.")

# Override environment for GoogleEnrichor to pick up only these
os.environ["WORKING_KEYS"] = ",".join(keys_to_use)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    enrichor = GoogleEnrichor()
    
    # 1. READ SILVER DATA (UNIQUE POIs)
    cities_env = os.getenv("SMART_TRAVEL_CITIES", "hanoi,danang,hcm,dalat")
    cities = [c.strip() for c in cities_env.split(",") if c.strip()]

    
    for city in cities:
        logger.info(f"🔍 Starting Google Enrichment for {city}...")
        silver_path = f"storage/silver/pois_cleaned/{city}/data.parquet"
        
        if not os.path.exists(silver_path):
            logger.warning(f"No silver data for {city}, skipping...")
            continue
            
        df = pd.read_parquet(silver_path)
        places = df.to_dict('records')
        
        # 2. RUN ENRICHMENT (Concurrency 5 handled by enrich_batch)
        # enrich_batch will automatically handle checkpointing (skipping if file exists)
        await enrichor.enrich_batch(places, city)
        
    logger.info("🏆 Google Enrichment Batch Finished.")

if __name__ == "__main__":
    asyncio.run(main())
