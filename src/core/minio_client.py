"""
Bronze Storage - MongoDB Only
==============================
MinIO đã được loại bỏ. Dữ liệu Bronze được lưu trực tiếp vào MongoDB (collection bronze_pois).
Đây là stub file để giữ tương thích import, sử dụng MongoDB thông qua src.core.database.
"""
from typing import Optional, Dict, Any, List
from src.core.logging import get_logger

logger = get_logger(__name__)


class BronzeStorage:
    """Stub class - Bronze data lưu vào MongoDB (bronze_pois collection)"""
    
    def __init__(self):
        logger.warning("BronzeStorage (MinIO) is deprecated. Use MongoDB bronze_pois collection directly.")
    
    def save_bronze_record(self, *args, **kwargs):
        raise NotImplementedError("MinIO removed. Use MongoDB bronze_pois collection.")

    def get_bronze_record(self, *args, **kwargs):
        raise NotImplementedError("MinIO removed. Use MongoDB bronze_pois collection.")

    def list_bronze_records(self, *args, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError("MinIO removed. Use MongoDB bronze_pois collection.")

    def delete_bronze_record(self, *args, **kwargs) -> bool:
        raise NotImplementedError("MinIO removed. Use MongoDB bronze_pois collection.")

    def get_stats(self) -> Dict[str, Any]:
        raise NotImplementedError("MinIO removed. Use MongoDB bronze_pois collection.")


# Singleton instance
_bronze_storage: Optional[BronzeStorage] = None


def get_bronze_storage() -> BronzeStorage:
    """Get or create BronzeStorage singleton"""
    global _bronze_storage
    if _bronze_storage is None:
        _bronze_storage = BronzeStorage()
    return _bronze_storage
