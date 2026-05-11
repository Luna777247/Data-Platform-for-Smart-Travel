import json
import psycopg2
from psycopg2.extras import execute_values
import logging
from pymongo import MongoClient
from typing import Optional

logger = logging.getLogger(__name__)


class PostgresLoader:
    def __init__(self, db_config: dict, mongo_uri: str, mongo_db: str = "smart_travel"):
        self.db_config = db_config
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    def load_city(self, city: str):
        """
        Nạp dữ liệu từ Silver Layer (MongoDB silver_pois) vào PostgreSQL + PostGIS.
        Sử dụng cơ chế UPSERT để tránh trùng lặp u_key.
        """
        logger.info(f"Loading {city} data into Serving Layer (PostgreSQL)...")

        # 1. READ FROM SILVER (MONGODB)
        try:
            mongo_client = MongoClient(self.mongo_uri)
            db = mongo_client[self.mongo_db]
            docs = list(db["silver_pois"].find({"city": city}))
            mongo_client.close()
        except Exception as e:
            logger.error(f"Failed to read silver data for {city} from MongoDB: {e}")
            return

        # 2. PREPARE FOR UPSERT
        # Lọc các cột cần thiết khớp với Schema PostgreSQL
        # Tables: u_key, name, city, category, rating, review_count, geom, metadata
        
        records = []
        for row in docs:
            lat = row.get('lat') or row.get('location', {}).get('lat')
            lon = row.get('lon') or row.get('location', {}).get('lon')
            geom_wkt = f"SRID=4326;POINT({lon} {lat})" if lat and lon else None
            row.pop('_id', None)
            records.append((
                row.get('u_key'),
                row.get('name'),
                city,
                row.get('category'),
                row.get('rating'),
                row.get('reviews', 0),
                geom_wkt,
                json.dumps(row)
            ))

        # 3. EXECUTE BATCH UPSERT
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        upsert_query = """
            INSERT INTO pois (u_key, name, city, category, rating, review_count, geom, metadata)
            VALUES %s
            ON CONFLICT (u_key) DO UPDATE SET
                name = EXCLUDED.name,
                rating = EXCLUDED.rating,
                review_count = EXCLUDED.review_count,
                geom = EXCLUDED.geom,
                metadata = EXCLUDED.metadata,
                updated_at = NOW();
        """
        
        try:
            execute_values(cur, upsert_query, records)
            conn.commit()
            logger.info(f"Successfully upserted {len(records)} records for {city}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Postgres upsert failed: {e}")
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    pass
