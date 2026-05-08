from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class BronzePlace(BaseModel):
    source_id: str
    raw_data: Dict[str, Any]
    collected_at: datetime
    city: str
    source: str  # 'osm' | 'google'


class SilverPlace(BronzePlace):
    name: str
    address: str
    latitude: float
    longitude: float
    categories: List[str]
    deduplication_key: str


class GoldPlace(SilverPlace):
    id: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    quality_score: float
    business_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
