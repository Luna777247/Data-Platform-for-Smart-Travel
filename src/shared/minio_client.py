from minio import Minio
import os

def get_minio_client() -> Minio:
    """Enterprise-grade MinIO client factory."""
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD", "minioadminpassword")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )
