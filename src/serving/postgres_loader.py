import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from minio import Minio
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class PostgresLoader:
    def __init__(self, db_config: dict, minio_client: Minio):
        self.db_config = db_config
        self.minio = minio_client
        self.bucket = "lakehouse"

    def load_city(self, city: str):
        """
        Nạp dữ liệu từ Silver Layer (Parquet) vào PostgreSQL + PostGIS.
        Sử dụng cơ chế UPSERT để tránh trùng lặp u_key.
        """
        logger.info(f"Loading {city} data into Serving Layer (PostgreSQL)...")
        
        # 1. READ FROM SILVER
        silver_path = f"silver/pois_cleaned/{city}/data.parquet"
        try:
            response = self.minio.get_object(self.bucket, silver_path)
            df = pd.read_parquet(BytesIO(response.read()))
        except Exception as e:
            logger.error(f"Failed to read silver data for {city}: {e}")
            return

        # 2. PREPARE FOR UPSERT
        # Lọc các cột cần thiết khớp với Schema PostgreSQL
        # Tables: u_key, name, city, category, rating, review_count, geom, metadata
        
        records = []
        for _, row in df.iterrows():
            # Chuyển đổi tọa độ sang WKT (Well-Known Text) cho PostGIS
            geom_wkt = f"SRID=4326;POINT({row['lon']} {row['lat']})" if pd.notnull(row['lat']) else None
            
            records.append((
                row['u_key'],
                row['name'],
                city,
                row.get('category'),
                row.get('rating'),
                row.get('reviews', 0),
                geom_wkt,
                json.dumps(row.to_dict()) # Toàn bộ data vào metadata cho GIN index search
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

import json
if __name__ == "__main__":
    # Test connection logic here
    pass
