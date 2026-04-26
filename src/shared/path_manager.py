import os

# ROOT_DIR is 3 levels up from this file (src/shared/path_manager.py)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_path(relative_path: str) -> str:
    """Returns absolute path given a path relative to project root."""
    return os.path.join(ROOT_DIR, relative_path)

# Standard paths
STORAGE_DIR = get_path("storage")
BRONZE_DIR = os.path.join(STORAGE_DIR, "bronze")
SILVER_DIR = os.path.join(STORAGE_DIR, "silver")
GOLD_DIR = os.path.join(STORAGE_DIR, "gold")
CONFIG_DIR = get_path("storage/configs")
LOGS_DIR = get_path("storage/logs")
KEY_REPORT_PATH = os.path.join(LOGS_DIR, "key_report.json")
DOTENV_PATH = get_path(".env")
