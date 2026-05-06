import pandas as pd
import logging
import os
import json
from datetime import datetime, timezone
from app.db.client import MongoClient

logger = logging.getLogger(__name__)

class GoldServer:
    def __init__(self):
        # We assume MongoClient is already connected or will be connected by the caller
        pass

    async def load_city_to_gold(self, city: str):
        """
        Nạp dữ liệu từ Silver Layer (Parquet) vào MongoDB (Gold Layer).
        """
        logger.info(f"🚀 Loading {city} data into Gold Layer (MongoDB)...")
        
        # 1. Đọc từ Silver (Local first for now)
        from src.shared.path_manager import get_path
        silver_path = get_path(f"storage/silver/pois_cleaned/{city}/data.parquet")
        
        if not os.path.exists(silver_path):
            logger.error(f"Silver data not found for {city}")
            return
            
        df = pd.read_parquet(silver_path)
        
        # 2. Xử lý định dạng cho MongoDB (GeoJSON)
        records = []
        for _, row in df.iterrows():
            record = row.to_dict()
            # Đảm bảo có city
            record["city"] = city
            # Chuyển đổi tọa độ sang GeoJSON
            if pd.notnull(row.get("lat")) and pd.notnull(row.get("lon")):
                record["location"] = {
                    "type": "Point",
                    "coordinates": [float(row["lon"]), float(row["lat"])]
                }
            
            # Clean for BSON - Force to primitives
            def force_primitive(obj):
                if isinstance(obj, dict):
                    return {str(k): force_primitive(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [force_primitive(i) for i in obj]
                elif isinstance(obj, datetime):
                    return obj
                elif isinstance(obj, (int, float)):
                    if pd.isna(obj): return None
                    return obj
                elif obj is None:
                    return None
                else:
                    # Chuyển đổi bất kỳ thứ gì khác thành string để an toàn
                    return str(obj)

            clean = force_primitive(record)
            records.append(clean)
            
        # 3. Upsert vào MongoDB
        db = MongoClient.get_db()
        if db is None:
            logger.error("MongoDB not connected")
            return
            
        # Bulk operations
        from pymongo import UpdateOne
        operations = []
        for r in records:
            operations.append(UpdateOne(
                {"u_key": r["u_key"]},
                {"$set": {**r, "last_served_at": datetime.now(timezone.utc)}},
                upsert=True
            ))
            
        if operations:
            try:
                result = await db["places"].bulk_write(operations)
                logger.info(f"✅ Upserted {result.upserted_count + result.modified_count} POIs to Gold for {city}")
            except Exception as e:
                logger.error(f"Bulk write failed: {e}")
                raise e
        else:
            logger.warning(f"No records to load for {city}")

if __name__ == "__main__":
    import asyncio
    async def test():
        await MongoClient.connect()
        server = GoldServer()
        await server.load_city_to_gold("hanoi")
    asyncio.run(test())
