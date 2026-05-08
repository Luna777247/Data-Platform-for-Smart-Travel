import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import os
from src.shared.data_utils import make_ukey

def migrate_keys():
    file_path = "storage/data/pois.json"
    if not os.path.exists(file_path):
        print("No data file found to migrate.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Migrating {len(data)} records to new SHA1-NFD Key standard...")
    
    new_data = {}
    for poi in data:
        # Generate new key using the new standard
        new_key = make_ukey(poi["name"], poi["location"]["lat"], poi["location"]["lon"])
        poi["u_key"] = new_key
        # Use new_key as dictionary key to handle accidental duplicates during migration
        new_data[new_key] = poi

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(list(new_data.values()), f, ensure_ascii=False, indent=2)
    
    print(f"Migration completed. Decoupled/Unified records: {len(new_data)}")

if __name__ == "__main__":
    migrate_keys()
