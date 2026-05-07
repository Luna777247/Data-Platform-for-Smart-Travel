import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging() -> None:
    """
    Fix #9: Cấu hình logging với RotatingFileHandler để tránh log file quá lớn.
    Max 10MB/file, giữ 5 file backup.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Format
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    # Rotating file handler (10MB max, 5 backups)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "backend.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    # Quiet noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
