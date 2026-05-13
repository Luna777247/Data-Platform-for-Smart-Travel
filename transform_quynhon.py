import asyncio
import os
import sys
from dotenv import load_dotenv

# load_dotenv MUST be before any local imports that use settings
load_dotenv()

# Thêm đường dẫn để import src
sys.path.append(os.getcwd())

from src.services.silver_gold_pipeline import SilverGoldPipeline
from src.core.config import settings

async def transform_quynhon():
    print(f"🚀 Starting transformation for Quy Nhơn city...")
    pipeline = SilverGoldPipeline()
    
    city_code = "quynhon"
    
    # 1. Bronze -> Silver (chỉ cho Quy Nhơn)
    print(f"Step 1: Transforming Bronze -> Silver for {city_code}...")
    # Vì service bronze_to_silver hỗ trợ filter city
    result_silver = await pipeline.bronze_to_silver(city=city_code, batch_size=500)
    print(f"  Transformed to Silver: {result_silver['transformed']} records")
    
    # 2. Silver -> Gold (chỉ cho Quy Nhơn)
    print(f"Step 2: Enriched Silver -> Gold for {city_code}...")
    result_gold = await pipeline.silver_to_gold(city=city_code, batch_size=500)
    print(f"  Enriched to Gold: {result_gold['enriched']} records")
    
    print("\n" + "="*40)
    print("  TRANSFORMATION SUMMARY - QUY NHON")
    print("="*40)
    print(f"  Silver Layer: {result_silver['transformed']} records")
    print(f"  Gold Layer  : {result_gold['enriched']} records")
    print("="*40)
    print("🎉 Transformation for Quy Nhơn completed!")

if __name__ == "__main__":
    try:
        asyncio.run(transform_quynhon())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
