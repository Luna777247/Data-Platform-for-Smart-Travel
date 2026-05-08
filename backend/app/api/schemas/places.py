from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class PlaceFilter(BaseModel):
    city: Optional[str] = None
    category: Optional[str] = None
    limit: int = 50
    offset: int = 0


class PlaceResponse(BaseModel):
    id: str
    name: str
    city: str
    address: str
    latitude: float
    longitude: float
    categories: List[str]
    rating: Optional[float] = None
    review_count: Optional[int] = None
    source: str
    quality_score: float
    created_at: datetime
    updated_at: datetime

    # Pydantic v2: from_attributes replaces orm_mode
    model_config = {"from_attributes": True}