import asyncio
import os
import sys
from dotenv import load_dotenv

# load_dotenv MUST be before any local imports that use settings
load_dotenv()

# Thêm đường dẫn để import src
sys.path.append(os.getcwd())

from src.services.bronze_pipeline import BronzePipeline
from src.core.config import settings

async def collect_quynhon():
    print(f"🚀 Starting collection for Quy Nhơn city...")
    print(f"🚀 Using database: {settings.mongodb_database}")
    
    pipeline = BronzePipeline()
    
    # Cấu hình cho Quy Nhơn
    city_name = "Quy Nhơn"
    city_code = "quynhon"
    lat = 13.7764
    lng = 109.2243
    
    # Các loại hình cần thu thập
    categories = ["restaurant", "tourist_attraction", "hotel"]
    
    results = []
    for category in categories:
        print(f"\n--- Collecting category: {category} ---")
        result = await pipeline.collect_city_category(
            city=city_name,
            city_code=city_code,
            lat=lat,
            lng=lng,
            category=category,
            radius=5000 # Quét trong bán kính 5km
        )
        results.append({"category": category, **result})
        print(f"  Inserted: {result['inserted']}")
        print(f"  Skipped: {result['skipped']}")
    
    print("\n" + "="*40)
    print("  COLLECTION SUMMARY - QUY NHON")
    print("="*40)
    total_new = sum(r['inserted'] for r in results)
    for r in results:
        print(f"  - {r['category']}: {r['inserted']} new records")
    print(f"\n  Total new records added to Bronze: {total_new}")
    print("="*40)
    print("🎉 Collection for Quy Nhơn completed!")

if __name__ == "__main__":
    try:
        asyncio.run(collect_quynhon())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
