# backend/app/models/place.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Location(BaseModel):
    lat: float
    lon: float

class PlaceModel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    type: str  # attraction | restaurant | hotel
    city: str  # hanoi | hcm | danang
    address: str
    rating: float = 0.0
    reviews: int = 0
    price_level: Optional[int] = 0
    location: Location
    source: str = "osm|google"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    hash: Optional[str] = None
    u_key: Optional[str] = None # Unique Key for dedup

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PipelineStatus(BaseModel):
    city: str
    type: str
    status: str  # running | done | failed
    collected: int = 0
    target: int = 150
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
