import os
import json
import pandas as pd
import sys
import logging

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.shared.path_manager import get_path

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATUS_FILE = get_path("storage/metadata/pipeline_status.json")

def sync_dashboard_metrics():
    """Sync real file counts from Lakehouse to Dashboard metadata."""
    if not os.path.exists(STATUS_FILE):
        logger.warning(f"Status file not found at {STATUS_FILE}")
        return

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read status file: {e}")
        return

    cities = ["hanoi", "danang", "dalat", "cantho", "haiphong", "hue", "nhatrang", "vungtau"]
    
    # Pre-calculate enriched counts per city to avoid repeated disk IO
    enriched_counts = {}
    for city in cities:
        google_dir = get_path(f"storage/bronze/google/{city}")
        if os.path.exists(google_dir):
            enriched_counts[city] = len([f for f in os.listdir(google_dir) if f.endswith(".json")])
        else:
            enriched_counts[city] = 0

    # Pre-calculate OSM counts from Silver
    osm_counts = {}
    for city in cities:
        osm_path = get_path(f"storage/silver/pois_osm/{city}/data.parquet")
        if os.path.exists(osm_path):
            try:
                df_osm = pd.read_parquet(osm_path)
                if 'type' in df_osm.columns:
                    # Count by type
                    for p_type in df_osm['type'].unique():
                        osm_counts[f"{city}_{p_type}"] = len(df_osm[df_osm['type'] == p_type])
                else:
                    # Fallback to total if type column missing
                    osm_counts[f"{city}_total"] = len(df_osm)
            except Exception as e:
                logger.error(f"Error reading {osm_path}: {e}")

    # Update metadata
    updated_count = 0
    for item in status_data:
        city = item.get('city')
        p_type = item.get('type')
        
        # 1. Update Collected (OSM)
        key = f"{city}_{p_type}"
        if key in osm_counts:
            item['collected'] = osm_counts[key]
        
        # 2. Update Enriched (Google) - This is tricky since Google data isn't typed yet
        # We'll use a heuristic: attribute enriched counts proportionally or just show city total
        # For simplicity and accuracy in dashboard, we add a global city-level enriched field
        # if it doesn't already exist.
        item['enriched'] = enriched_counts.get(city, 0)
        
        # 3. Update Status
        if item['collected'] > 0:
            if item.get('enriched', 0) >= item['collected']:
                item['status'] = 'done'
            else:
                item['status'] = 'enriching'
        
        updated_count += 1

    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Successfully synced {updated_count} dashboard metrics.")
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")

if __name__ == "__main__":
    sync_dashboard_metrics()
