"""
Celery Application Configuration
==============================
Cấu hình Celery cho background tasks và scheduled jobs.
"""
import os
from celery import Celery

# Lấy URL từ environment hoặc dùng default
broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

# Tạo Celery app
celery_app = Celery(
    "smart_tourism",
    broker=broker_url,
    backend=result_backend,
    include=[],
)

# Cấu hình Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Disable auto-import of default modules
    imports=(),
    task_default_modules=(),
    # Beat schedule file location (writable directory)
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

# Export cho Celery CLI
app = celery_app

if __name__ == "__main__":
    celery_app.start()
