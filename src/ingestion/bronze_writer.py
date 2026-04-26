import json
import os
import logging
from datetime import datetime
from minio import Minio
from io import BytesIO
from src.shared.data_utils import make_ukey

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class BronzeWriter:
    def __init__(self, endpoint, access_key, secret_key, secure=False):
        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            self.bucket = "lakehouse"
            self._ensure_bucket()
            self.minio_active = True
        except Exception as e:
            logger.error(f"❌ MinIO connection failed: {e}. Switching to LOCAL ONLY mode.")
            self.minio_active = False

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created bucket: {self.bucket}")

    def write_raw(self, source: str, city: str, data: list):
        """
        Ghi dữ liệu thô vào Bronze Layer. Tự động Fallback về Local nếu MinIO offline.
        """
        now = datetime.utcnow()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # 1. ÁP DỤNG CHUẨN ĐỊNH DANH (u_key)
        for item in data:
            item["u_key"] = make_ukey(item.get("name"), item.get("location", {}).get("lat"), item.get("location", {}).get("lon"))
            item["ingestion_at"] = now.isoformat()

        file_name = f"bronze/{source}/{city}/{timestamp}.json"
        
        try:
            # TRY MINIO
            if self.minio_active:
                content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
                self.client.put_object(self.bucket, file_name, BytesIO(content), length=len(content), content_type="application/json")
                logger.info(f"🚀 [MINIO] Saved {len(data)} records to {file_name}")
            else:
                raise ConnectionError("MinIO marked as inactive.")
        except Exception:
            # FALLBACK TO LOCAL
            local_path = os.path.join("storage", file_name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.warning(f"⚠️ [FALLBACK] MinIO Offline. Saved {len(data)} records to local: {local_path}")
            
        return file_name

# For local testing/integration
if __name__ == "__main__":
    # Test connection
    writer = BronzeWriter("localhost:9000", "minioadmin", "minioadminpassword")
    test_data = [{"name": "Test Place", "location": {"lat": 21.0285, "lon": 105.8542}}]
    writer.write_raw("osm", "hanoi", test_data)
