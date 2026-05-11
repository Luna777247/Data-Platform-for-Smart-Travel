import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GoldGenerator:
    """
    Gold Layer Analytics Generator.
    Dữ liệu được lấy từ MongoDB (silver_pois) và ghi vào gold_master_pois.
    MinIO đã được loại bỏ.
    """

    def __init__(self, db=None):
        self.db = db

    async def generate_analytics(self):
        """Tổng hợp analytics từ silver_pois vào gold_master_pois."""
        if self.db is None:
            logger.warning("No DB connection provided to GoldGenerator")
            return
        logger.info("Generating Gold Layer Analytics from MongoDB silver_pois...")
        pipeline = [
            {"$group": {
                "_id": "$city",
                "total_pois": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"},
                "total_reviews": {"$sum": "$reviews"}
            }}
        ]
        cursor = self.db["silver_pois"].aggregate(pipeline)
        results = await cursor.to_list(length=None)
        if results:
            await self.db["gold_city_stats"].drop()
            await self.db["gold_city_stats"].insert_many(results)
            logger.info(f"Gold city_stats: {len(results)} cities")
        logger.info("Gold analytics generated successfully.")

    async def generate_for_city(self, city: str) -> dict:
        """Generate analytics cho một thành phố cụ thể."""
        if self.db is None:
            return {"status": "no_db", "city": city}
        logger.info(f"Generating analytics for city: {city}")
        docs = await self.db["silver_pois"].find({"city": city}).to_list(length=None)
        if not docs:
            logger.warning(f"No silver data found for {city}")
            return {"status": "no_data", "city": city}
        total = len(docs)
        ratings = [d.get("rating", 0) for d in docs if d.get("rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        cat_dist = {}
        for d in docs:
            for cat in d.get("categories", []):
                cat_dist[cat] = cat_dist.get(cat, 0) + 1
        return {
            "city": city,
            "total_places": total,
            "avg_rating": round(avg_rating, 2),
            "category_distribution": cat_dist
        }

if __name__ == "__main__":
    pass
