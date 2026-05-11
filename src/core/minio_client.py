"""
MinIO Client for Bronze Layer Storage
======================================
Lưu trữ raw data (Bronze) trong MinIO object storage
Schema giữ nguyên như storage/ hiện tại
"""
import json
import io
from typing import Optional, Dict, Any, List
from datetime import datetime

from minio import Minio
from minio.error import S3Error

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class BronzeStorage:
    """
    Lưu trữ Bronze layer trong MinIO
    - Giữ nguyên cấu trúc: {city}/{category}/{timestamp}_{hash}.json
    - Hỗ trợ cả Google Places và OSM formats
    """
    
    def __init__(self):
        self.client = None
        self.bucket = "smart-travel-bronze"
        self._connect()
    
    def _connect(self):
        """Kết nối MinIO"""
        try:
            endpoint = settings.minio_endpoint
            # Remove http/https prefix if present
            if endpoint.startswith(('http://', 'https://')):
                endpoint = endpoint.split('://', 1)[1]
            
            secure = settings.minio_secure or endpoint.startswith('https')
            
            self.client = Minio(
                endpoint=endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=secure
            )
            
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            
            logger.info(f"Connected to MinIO at {settings.minio_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to connect MinIO: {e}")
            raise
    
    def save_bronze_record(
        self,
        data: Dict[str, Any],
        city: str,
        source: str,  # 'google' hoặc 'osm'
        category: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Lưu bronze record vào MinIO
        
        Path structure: bronze/{source}/{city}/{filename}
        Ví dụ: bronze/google/hanoi/restaurant_20260510_143022_a1b2c3.json
        
        Args:
            data: Raw JSON data từ API
            city: Tên thành phố
            source: 'google' hoặc 'osm'
            category: Loại POI (restaurant, hotel, v.v.)
            filename: Tên file tùy chỉnh (auto-generated nếu None)
        
        Returns:
            Object path trong MinIO
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                import hashlib
                data_hash = hashlib.md5(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()[:8]
                
                if category:
                    filename = f"{category}_{timestamp}_{data_hash}.json"
                else:
                    filename = f"{timestamp}_{data_hash}.json"
            
            # Build object path
            category_path = category if category else "general"
            object_path = f"bronze/{source}/{city}/{category_path}/{filename}"
            
            # Convert data to JSON bytes
            json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            data_stream = io.BytesIO(json_bytes)
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_path,
                data=data_stream,
                length=len(json_bytes),
                content_type="application/json",
                metadata={
                    "x-amz-meta-city": city,
                    "x-amz-meta-source": source,
                    "x-amz-meta-category": category or "general",
                    "x-amz-meta-collected_at": datetime.now().isoformat(),
                }
            )
            
            logger.debug(f"Saved bronze record: {object_path}")
            return object_path
            
        except S3Error as e:
            logger.error(f"MinIO S3 error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving bronze record: {e}")
            raise
    
    def get_bronze_record(self, object_path: str) -> Optional[Dict[str, Any]]:
        """Đọc bronze record từ MinIO"""
        try:
            response = self.client.get_object(self.bucket, object_path)
            data = json.loads(response.read().decode('utf-8'))
            response.close()
            response.release_conn()
            return data
            
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"Error reading {object_path}: {e}")
            raise
    
    def list_bronze_records(
        self,
        city: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Liệt kê bronze records trong MinIO
        
        Args:
            city: Filter theo thành phố
            source: Filter theo nguồn ('google' hoặc 'osm')
            category: Filter theo category
            prefix: Custom prefix path
        
        Returns:
            List of objects với metadata
        """
        try:
            # Build search prefix
            if prefix:
                search_prefix = prefix
            else:
                parts = ["bronze"]
                if source:
                    parts.append(source)
                if city:
                    parts.append(city)
                if category:
                    parts.append(category)
                search_prefix = "/".join(parts)
                if search_prefix:
                    search_prefix += "/"
            
            objects = []
            for obj in self.client.list_objects(self.bucket, prefix=search_prefix, recursive=True):
                if obj.object_name.endswith('.json'):
                    # Parse metadata from path
                    path_parts = obj.object_name.split('/')
                    
                    record_info = {
                        "path": obj.object_name,
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                    }
                    
                    # Extract from path: bronze/{source}/{city}/{category}/{filename}
                    if len(path_parts) >= 4:
                        record_info["source"] = path_parts[1]
                        record_info["city"] = path_parts[2]
                        if len(path_parts) >= 5:
                            record_info["category"] = path_parts[3]
                    
                    objects.append(record_info)
            
            return objects
            
        except Exception as e:
            logger.error(f"Error listing bronze records: {e}")
            raise
    
    def delete_bronze_record(self, object_path: str) -> bool:
        """Xóa bronze record"""
        try:
            self.client.remove_object(self.bucket, object_path)
            logger.info(f"Deleted: {object_path}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting {object_path}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Thống kê bronze storage"""
        try:
            stats = {
                "total_objects": 0,
                "total_size": 0,
                "by_source": {},
                "by_city": {},
            }
            
            for obj in self.client.list_objects(self.bucket, prefix="bronze/", recursive=True):
                if obj.object_name.endswith('.json'):
                    stats["total_objects"] += 1
                    stats["total_size"] += obj.size
                    
                    # Parse path
                    parts = obj.object_name.split('/')
                    if len(parts) >= 3:
                        source = parts[1]
                        city = parts[2]
                        
                        stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
                        stats["by_city"][city] = stats["by_city"].get(city, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Singleton instance
_bronze_storage: Optional[BronzeStorage] = None


def get_bronze_storage() -> BronzeStorage:
    """Get or create BronzeStorage singleton"""
    global _bronze_storage
    if _bronze_storage is None:
        _bronze_storage = BronzeStorage()
    return _bronze_storage
