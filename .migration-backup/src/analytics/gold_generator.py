import pandas as pd
import logging
from minio import Minio
from io import BytesIO

logger = logging.getLogger(__name__)

class GoldGenerator:
    def __init__(self, minio_client: Minio):
        self.minio = minio_client
        self.bucket = "lakehouse"

    def generate_analytics(self):
        """
        Tổng hợp dữ liệu từ toàn bộ Silver layer để tạo Gold Layer (Parquet).
        - Top Rated POIs
        - City Statistics
        """
        logger.info("Generating Gold Layer Analytics...")
        
        # 1. LOAD ALL SILVER DATA
        all_dfs = []
        objects = self.minio.list_objects(self.bucket, prefix="silver/pois_cleaned/", recursive=True)
        for obj in objects:
            if obj.object_name.endswith(".parquet"):
                response = self.minio.get_object(self.bucket, obj.object_name)
                all_dfs.append(pd.read_parquet(BytesIO(response.read())))
        
        if not all_dfs:
            logger.warning("No silver data found for analytics")
            return
            
        df_full = pd.concat(all_dfs, ignore_index=True)

        # 2. ANALYTICS 1: CITY STATS
        city_stats = df_full.groupby('city').agg(
            total_pois=('u_key', 'count'),
            avg_rating=('rating', 'mean'),
            total_reviews=('reviews', 'sum')
        ).reset_index()
        self._write_gold("city_stats", city_stats)

        # 3. ANALYTICS 2: TOP POIs (Rating > 4.5)
        top_pois = df_full[df_full['rating'] >= 4.5].sort_values(by='reviews', ascending=False).head(100)
        self._write_gold("top_rated_pois", top_pois)

        logger.info("Gold analytics generated successfully.")

    def _write_gold(self, name: str, df: pd.DataFrame):
        path = f"gold/analytics/{name}.parquet"
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        content = buffer.getvalue()
        
        self.minio.put_object(
            self.bucket,
            path,
            BytesIO(content),
            length=len(content),
            content_type="application/x-parquet"
        )
        logger.info(f"Saved Gold table: {path}")

    async def generate_for_city(self, city: str) -> dict:
        """Generate analytics specific to a city."""
        logger.info(f"Generating analytics for city: {city}")
        
        # Load silver data for this city
        obj_name = f"silver/pois_cleaned/{city}.parquet"
        try:
            response = self.minio.get_object(self.bucket, obj_name)
            df = pd.read_parquet(BytesIO(response.read()))
        except Exception:
            logger.warning(f"No silver data found for {city}")
            return {"status": "no_data", "city": city}

        # Example city-specific analytics: Category distribution
        cat_dist = df.explode('categories')['categories'].value_counts().to_dict()
        
        result = {
            "city": city,
            "total_places": len(df),
            "avg_rating": float(df['rating'].mean()) if 'rating' in df.columns else 0.0,
            "category_distribution": cat_dist
        }
        
        # Write to gold
        self._write_gold(f"city_analytics_{city}", pd.DataFrame([result]))
        
        return result

if __name__ == "__main__":
    pass
