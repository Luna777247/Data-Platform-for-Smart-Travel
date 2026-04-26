import pandas as pd
import logging
import os
import json
from minio import Minio
from io import BytesIO
from datetime import datetime

# Configure Logging
logger = logging.getLogger(__name__)

class SilverProcessor:
    def __init__(self, minio_client: Minio, bucket="lakehouse"):
        self.client = minio_client
        self.bucket = bucket

    def process_city(self, city: str):
        """
        Xử lý dữ liệu từ Bronze sang Silver: Hỗ trợ cả MinIO và Local Storage.
        """
        logger.info(f"✨ Processing Silver layer for city: {city}")
        all_data = []

        # 1. TRY MINIO FIRST
        try:
            folders = [f"bronze/osm/{city}/", f"bronze/google/{city}/"]
            for prefix in folders:
                objects = self.client.list_objects(self.bucket, prefix=prefix, recursive=True)
                for obj in objects:
                    response = self.client.get_object(self.bucket, obj.object_name)
                    all_data.extend(json.loads(response.read().decode('utf-8')))
            logger.info(f"Loaded data from MinIO for {city}")
        except Exception:
            # 2. FALLBACK TO LOCAL STORAGE
            logger.warning(f"MinIO unavailable, checking local storage for {city}...")
            local_base = os.path.join("storage", "bronze")
            sources = ["osm", "google"]
            for src in sources:
                city_dir = os.path.join(local_base, src, city)
                if os.path.exists(city_dir):
                    for file in os.listdir(city_dir):
                        if file.endswith(".json"):
                            with open(os.path.join(city_dir, file), "r", encoding="utf-8") as f:
                                all_data.extend(json.load(f))
            logger.info(f"🚀 Loaded {len(all_data)} records from LOCAL storage for {city}")

        if not all_data:
            logger.warning(f"No Bronze data found for {city}")
            return

        # 2. CONVERT TO DATAFRAME
        df = pd.DataFrame(all_data)
        df['ingestion_at'] = pd.to_datetime(df['ingestion_at'])
        df = df.sort_values(by="ingestion_at", ascending=False)

        # 3. LOGIC CỨU VÃN (RECOVERY STRATEGY)
        # Tách riêng tập dữ liệu Google xịn để làm nguồn đối soát
        google_ref = df[df['source'] == 'google'][['location', 'name', 'u_key']].copy()
        
        def recover_name(row):
            # Nếu tên là rác (unknown/unnamed)
            is_trash_name = str(row['name']).lower() in ['unknown', 'unnamed', 'n/a', 'none']
            
            if is_trash_name and row['source'] == 'osm':
                # Tìm kiếm trong tập Google xem có thằng nào cùng u_key không
                # (Vì u_key được tạo từ tọa độ làm tròn nên cùng vị trí sẽ cùng u_key)
                match = google_ref[google_ref['u_key'] == row['u_key']]
                if not match.empty:
                    new_name = match.iloc[0]['name']
                    logger.info(f"💡 RECOVERED: '{row['name']}' -> '{new_name}' via Google lookup.")
                    return new_name
            return row['name']

        df['name'] = df.apply(recover_name, axis=1)

        # 4. DEDUPLICATE & CLEAN
        df_silver = df.drop_duplicates(subset=["u_key"], keep="first")
        
        # Loại bỏ những thằng vẫn unknown sau khi đã cố cứu vãn
        df_silver = df_silver[~df_silver['name'].str.lower().isin(['unknown', 'unnamed'])]
        
        # 3. SCHEMA STANDARDIZATION
        # { u_key, name, city, category, rating, reviews, lat, lon, metadata }
        standard_cols = ['u_key', 'name', 'rating', 'reviews', 'category', 'status']
        # Đảm bảo các cột tồn tại
        for col in standard_cols:
            if col not in df_silver.columns:
                df_silver[col] = None
        
        # Extract lat/lon from location dict if needed
        if 'location' in df_silver.columns:
            df_silver['lat'] = df_silver['location'].apply(lambda x: x.get('lat') if isinstance(x, dict) else None)
            df_silver['lon'] = df_silver['location'].apply(lambda x: x.get('lon') if isinstance(x, dict) else None)

        # 4. QUALITY CHECK (GREAT EXPECTATIONS - Simplified for script)
        self._validate_quality(df_silver)

        # 5. WRITE TO SILVER LAYER (PARQUET)
        silver_path = f"silver/pois_cleaned/{city}/data.parquet"
        
        try:
            # 5a. TRY MINIO
            parquet_buffer = BytesIO()
            df_silver.to_parquet(parquet_buffer, index=False)
            parquet_content = parquet_buffer.getvalue()
            
            self.client.put_object(
                self.bucket,
                silver_path,
                BytesIO(parquet_content),
                length=len(parquet_content),
                content_type="application/x-parquet"
            )
            logger.info(f"🚀 [MINIO] Silver data saved to {silver_path}")
        except Exception:
            # 5b. FALLBACK TO LOCAL
            local_silver_path = os.path.join("storage", silver_path)
            os.makedirs(os.path.dirname(local_silver_path), exist_ok=True)
            df_silver.to_parquet(local_silver_path, index=False)
            logger.warning(f"⚠️ [FALLBACK] Silver data saved to local: {local_silver_path}")

    def _validate_quality(self, df):
        """Tổ chức các chốt kiểm tra chất lượng (Data Quality Gates)."""
        logger.info("Running Data Quality Checks...")
        
        # Check nulls
        missing_names = df['name'].isnull().sum()
        if missing_names > 0:
            logger.warning(f"Found {missing_names} records with missing names!")
            
        # Check rating range
        if 'rating' in df.columns:
            invalid_ratings = df[(df['rating'] < 0) | (df['rating'] > 5)].shape[0]
            if invalid_ratings > 0:
                logger.error(f"Found {invalid_ratings} records with invalid ratings!")
        
        # TODO: Link with actual Great Expectations Checkpoints here

if __name__ == "__main__":
    from minio import Minio
    client = Minio("localhost:9000", "minioadmin", "minioadminpassword", secure=False)
    processor = SilverProcessor(client)
    processor.process_city("hanoi")
