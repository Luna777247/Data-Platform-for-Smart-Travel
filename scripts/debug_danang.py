import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
import logging
from src.shared.path_manager import get_path
from src.ingestion.silver_processor import SilverProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_danang")

if __name__ == "__main__":
    processor = SilverProcessor(None)
    processor.process_city("danang")
