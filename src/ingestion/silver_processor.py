import pandas as pd
import json
import os
import logging
import asyncio
from typing import List, Dict
from datetime import datetime, timezone

# backend imports (using project structure)
from app.db.repository import PlaceRepository

logger = logging.getLogger(__name__)

class SilverProcessor:
    def __init__(self):
        self.repo = PlaceRepository()

    def _write_error_zone(self, city: str, stage: str, records: list[dict]):
        if not records:
            return
        from src.shared.path_manager import get_path

        # Error Zone (business rule: keep invalid records for later remediation)
        out_path = get_path(f"storage/silver/error_zone/{city}/{stage}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass

    def _record_quality_metrics(self, stage: str, df: pd.DataFrame, original_count: int, city: str):
        """Records data quality stats into MongoDB for observability."""
        total = len(df)
        dupes = original_count - total
        metrics = {
            "stage": stage,
            "city": city,
            "timestamp": datetime.now(timezone.utc),
            "total_records": total,
            "duplicates_removed": dupes,
            "completeness_score": round((1 - df['name'].isnull().mean()) * 100, 2) if 'name' in df.columns else 0,
            "missing_coordinates": int(df['lat'].isnull().sum()) if 'lat' in df.columns else 0
        }
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.repo.db["data_quality_stats"].insert_one(metrics))
            else:
                loop.run_until_complete(self.repo.db["data_quality_stats"].insert_one(metrics))
        except:
            pass

    def process_osm_to_silver(self, city: str):
        from src.shared.path_manager import get_path
        from src.shared.data_utils import make_ukey
        logger.info(f"📍 Step 1: Processing OSM -> Silver for {city}")
        
        osm_dir = get_path(f"storage/bronze/osm/{city}")
        all_data = []
        source_files = []
        if os.path.exists(osm_dir):
            for file in [f for f in os.listdir(osm_dir) if f.endswith(".json")]:
                source_files.append(file)
                with open(os.path.join(osm_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list): all_data.extend(data)
                    else: all_data.append(data)
        
        if not all_data:
            return

        error_zone = []
        
        for item in all_data:
            item["_lineage_source"] = "osm"
            lat = item.get("lat") or item.get("location", {}).get("lat")
            lon = item.get("lon") or item.get("location", {}).get("lon")
            name = item.get("name")
            if not name or lat is None or lon is None:
                error_zone.append({**item, "_error_reason": "missing_name_or_coordinates"})
                continue

            item["u_key"] = item.get("u_key") or make_ukey(name, lat, lon)
            if not item.get("u_key"):
                error_zone.append({**item, "_error_reason": "missing_u_key"})

        original_count = len(all_data)
        df = pd.DataFrame([i for i in all_data if i not in error_zone])
        df["_lineage_files"] = json.dumps(source_files)
        self._write_error_zone(city, "osm_to_silver", error_zone)
        
        if "u_key" in df.columns:
            df = df.dropna(subset=["u_key"]).drop_duplicates(subset=["u_key"])
        
        self._record_quality_metrics("osm_to_silver", df, original_count, city)
        
        output_path = get_path(f"storage/silver/pois_osm/{city}/data.parquet")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)

    def process_google_to_silver(self, city: str):
        from src.shared.path_manager import get_path
        from src.shared.data_utils import make_ukey
        logger.info(f"📍 Step 2: Processing Google Raw -> Silver Google for {city}")
        
        google_dir = get_path(f"storage/bronze/google/{city}")
        enriched_data = []
        error_zone = []
        if os.path.exists(google_dir):
            files = [f for f in os.listdir(google_dir) if f.endswith(".json")]
            for file in files:
                with open(os.path.join(google_dir, file), "r", encoding="utf-8") as f:
                    item = json.load(f)
                    items_to_process = item if isinstance(item, list) else [item]
                    for row in items_to_process:
                        raw = row.get("google_raw") or row
                        if "name" in raw:
                            loc = raw.get("geometry", {}).get("location", {})
                            lat = loc.get("lat") or raw.get("lat")
                            lon = loc.get("lng") or raw.get("lon")
                            name = raw.get("name")
                            if not name or lat is None or lon is None:
                                error_zone.append({**row, "_error_reason": "missing_name_or_coordinates"})
                                continue
                            ukey = row.get("u_key") or make_ukey(name, lat, lon)
                            if not ukey:
                                error_zone.append({**row, "_error_reason": "missing_u_key"})
                                continue
                            enriched_data.append({
                                "u_key": ukey, "name": raw.get("name"),
                                "rating": raw.get("rating"), "review_count": raw.get("user_ratings_total") or raw.get("reviews"),
                                "lat": lat, "lon": lon, "address": raw.get("formatted_address") or raw.get("address"),
                                "photos": [p.get("photo_reference") for p in raw.get("photos", [])] if raw.get("photos") else [],
                                "_lineage_source": "google",
                                "_lineage_files": json.dumps([file]),
                            })
        
        self._write_error_zone(city, "google_to_silver", error_zone)
        if not enriched_data:
            return
        df = pd.DataFrame(enriched_data).dropna(subset=["u_key"]).drop_duplicates(subset=["u_key"])
        output_path = get_path(f"storage/silver/pois_google/{city}/data.parquet")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)

    def merge_and_finalize(self, city: str):
        from src.shared.path_manager import get_path
        from src.shared.data_utils import compute_poi_hash
        logger.info(f"📍 Step 3: Merging OSM + Google for {city}")
        
        osm_path = get_path(f"storage/silver/pois_osm/{city}/data.parquet")
        google_path = get_path(f"storage/silver/pois_google/{city}/data.parquet")
        if not os.path.exists(osm_path): return
        
        df_osm = pd.read_parquet(osm_path)
        if os.path.exists(google_path):
            df_google = pd.read_parquet(google_path)
            
            # Step 1: Matching by exact u_key (Outer join to catch unique Google POIs)
            df_final = pd.merge(df_osm, df_google, on="u_key", how="outer", suffixes=('', '_google'))
            
            # Step 2: Combine columns from both sides
            for col in ["name", "lat", "lon"]:
                gcol = f"{col}_google"
                if gcol in df_final.columns and col in df_final.columns:
                    df_final[col] = df_final[col].fillna(df_final[gcol])

            # Business merge: Google enrichments override when present
            for col in ["rating", "review_count", "address", "photos"]:
                gcol = f"{col}_google"
                if gcol in df_final.columns:
                    if col not in df_final.columns:
                        df_final[col] = df_final[gcol]
                    else:
                        df_final[col] = df_final[gcol].combine_first(df_final[col])
            
            # Step 3: Fuzzy matching for remaining potential duplicates
            # (If absolute u_key match failed, they might still be the same)
            # For simplicity in this iteration, we trust u_key + outer join.
            # But we should ensure lineage is correct.
            
            def set_lineage(row):
                if pd.notnull(row.get('_lineage_source')) and pd.notnull(row.get('rating')):
                    return "osm+google"
                return row.get('_lineage_source') or "google"
            
            df_final["_lineage_source"] = df_final.apply(set_lineage, axis=1)

            # Merge lineage files (union of file lists when possible)
            if "_lineage_files_google" in df_final.columns or "_lineage_files" in df_final.columns:
                def merge_files(row):
                    files = []
                    for key in ["_lineage_files", "_lineage_files_google"]:
                        raw = row.get(key)
                        if not raw:
                            continue
                        try:
                            parsed = json.loads(raw) if isinstance(raw, str) else raw
                            if isinstance(parsed, list):
                                files.extend(parsed)
                        except Exception:
                            pass
                    # de-dup while preserving order
                    out = list(dict.fromkeys([str(f) for f in files if f]))
                    return json.dumps(out) if out else None

                df_final["_lineage_files"] = df_final.apply(merge_files, axis=1)
        else:
            df_final = df_osm
            
        df_final = df_final.dropna(subset=["name"]).drop_duplicates(subset=["u_key"])
        df_final["hash"] = df_final.apply(compute_poi_hash, axis=1)
        
        final_path = get_path(f"storage/silver/pois_cleaned/{city}/data.parquet")
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        df_final.to_parquet(final_path, index=False)
        logger.info(f"🚀 [DONE] Final POIs saved for {city}")

    def process_city(self, city: str):
        self.process_osm_to_silver(city)
        self.process_google_to_silver(city)
        self.merge_and_finalize(city)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    processor = SilverProcessor()
    processor.process_city("hanoi")
