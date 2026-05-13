import asyncio
import os
import sys
from dotenv import load_dotenv

# load_dotenv MUST be before any local imports that use settings
load_dotenv()

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

# Thêm đường dẫn để import src
sys.path.append(os.getcwd())

from src.services.silver_gold_pipeline import SilverGoldPipeline
from src.core.config import settings

async def run_transform():
    print(f"🚀 Using database: {settings.mongodb_database}")
    print(f"🚀 Using URL: {settings.mongodb_url[:50]}...")
    
    pipeline = SilverGoldPipeline()
    db = pipeline.db
    
    # 1. Bronze -> Silver
    print("Step 1: Transforming Bronze to Silver using Bulk Ops...")
    total_bronze = await db["bronze_pois"].count_documents({})
    print(f"Total Bronze records: {total_bronze}")
    
    if total_bronze == 0:
        print("❌ No Bronze records found. Check database name/collection.")
        return

    cursor = db["bronze_pois"].find({"$or": [{"has_osm_data": True}, {"has_google_data": True}]})
    
    from pymongo import UpdateOne
    batch_size = 500
    ops = []
    count = 0
    transformed = 0
    
    async for bronze_doc in cursor:
        try:
            silver_doc = pipeline._transform_to_silver(bronze_doc)
            ops.append(UpdateOne(
                {"place_id": silver_doc["place_id"], "city": silver_doc["city"]},
                {"$set": silver_doc},
                upsert=True
            ))
            
            if len(ops) >= batch_size:
                result = await db["silver_pois"].bulk_write(ops)
                transformed += (result.upserted_count + result.modified_count)
                count += len(ops)
                print(f"  Processed {count}/{total_bronze} records...")
                ops = []
        except Exception as e:
            print(f"  Error record {bronze_doc.get('_id')}: {e}")
    
    if ops:
        result = await db["silver_pois"].bulk_write(ops)
        transformed += (result.upserted_count + result.modified_count)
        count += len(ops)
        print(f"  Processed {count}/{total_bronze} records...")

    print(f"✅ Successfully processed {count} records to Silver.")

    # 2. Silver -> Gold
    print("\nStep 2: Transforming Silver to Gold using Bulk Ops...")
    total_silver = await db["silver_pois"].count_documents({"layer": "silver"})
    print(f"Total Silver records to process: {total_silver}")

    if total_silver == 0:
        print("⚠️ No Silver records found to process to Gold.")
    else:
        cursor = db["silver_pois"].find({"layer": "silver"})
        ops = []
        count = 0
        enriched = 0
        
        async for silver_doc in cursor:
            try:
                gold_doc = pipeline._transform_to_gold(silver_doc)
                ops.append(UpdateOne(
                    {"place_id": gold_doc["place_id"]},
                    {"$set": gold_doc},
                    upsert=True
                ))
                
                if len(ops) >= batch_size:
                    result = await db["gold_master_pois"].bulk_write(ops)
                    enriched += (result.upserted_count + result.modified_count)
                    count += len(ops)
                    print(f"  Enriched {count}/{total_silver} records...")
                    ops = []
            except Exception as e:
                print(f"  Error record {silver_doc.get('place_id')}: {e}")
        
        if ops:
            result = await db["gold_master_pois"].bulk_write(ops)
            enriched += (result.upserted_count + result.modified_count)
            count += len(ops)
            print(f"  Enriched {count}/{total_silver} records...")

    # Final stats
    stats = await pipeline.get_pipeline_stats()
    print("\n--- Final Statistics ---")
    print(f"Bronze: {stats['bronze']['total']}")
    print(f"Silver: {stats['silver']['total']}")
    print(f"Gold: {stats['gold']['total']}")
    print("------------------------")
    print("🎉 Pipeline transformation completed!")

if __name__ == "__main__":
    try:
        asyncio.run(run_transform())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
