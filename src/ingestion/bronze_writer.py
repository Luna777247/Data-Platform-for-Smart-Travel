import json
import os
import logging
from datetime import datetime, timezone
from src.shared.data_utils import make_ukey

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class BronzeWriter:
    """Ghi dữ liệu Bronze vào local storage (MinIO đã bị loại bỏ)."""

    def write_raw(self, source: str, city: str, data: list):
        """
        Ghi dữ liệu thô vào Bronze Layer dưới dạng file local JSON.
        """
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        for item in data:
            lat = item.get("lat") or item.get("location", {}).get("lat")
            lon = item.get("lon") or item.get("lng") or item.get("location", {}).get("lon") or item.get("location", {}).get("lng")
            if item.get("name") and lat is not None and lon is not None:
                item["u_key"] = make_ukey(item.get("name"), lat, lon)
            item["ingestion_at"] = now.isoformat()

        file_name = f"bronze/{source}/{city}/{timestamp}.json"
        local_path = os.path.join("storage", file_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data)} records to local: {local_path}")
        return file_name


if __name__ == "__main__":
    writer = BronzeWriter()
    test_data = [{"name": "Test Place", "location": {"lat": 21.0285, "lon": 105.8542}}]
    writer.write_raw("osm", "hanoi", test_data)
