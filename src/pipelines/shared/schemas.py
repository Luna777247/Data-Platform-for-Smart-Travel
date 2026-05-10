"""
Pipeline Data Schemas
=====================

Data contracts cho bronze/silver/gold layers.
Theo medallion architecture pattern.

Classes:
- BronzeRecord: Raw data từ collectors
- SilverRecord: Cleaned và enriched data
- GoldRecord: Aggregated business-ready data
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class BronzeRecord:
    """
    Bronze layer data record.
    
    Raw data từ collectors, chưa qua xử lý.
    Lưu trữ ở dạng gần như nguyên bản từ source.
    
    Attributes:
        place_id: Unique identifier từ source
        name: Tên địa điểm
        location: Geo coordinates
        category: Loại POI
        raw_data: Toàn bộ raw response
        source: Nguồn dữ liệu (google_places, osm, etc.)
        collected_at: Thời điểm collect
    """
    place_id: str
    name: str
    location: Dict[str, float]  # {"lat": float, "lng": float}
    category: str
    raw_data: Dict[str, Any]
    source: str
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Optional fields
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    business_status: Optional[str] = None
    photos: Optional[List[Dict]] = None
    opening_hours: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "place_id": self.place_id,
            "name": self.name,
            "location": self.location,
            "category": self.category,
            "raw_data": self.raw_data,
            "source": self.source,
            "collected_at": self.collected_at,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "rating": self.rating,
            "user_ratings_total": self.user_ratings_total,
            "price_level": self.price_level,
            "business_status": self.business_status,
            "photos": self.photos,
            "opening_hours": self.opening_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BronzeRecord":
        """Create from dictionary."""
        return cls(
            place_id=data.get("place_id", ""),
            name=data.get("name", ""),
            location=data.get("location", {}),
            category=data.get("category", ""),
            raw_data=data.get("raw_data", {}),
            source=data.get("source", ""),
            collected_at=data.get("collected_at", datetime.utcnow().isoformat()),
            address=data.get("address"),
            phone=data.get("phone"),
            website=data.get("website"),
            rating=data.get("rating"),
            user_ratings_total=data.get("user_ratings_total"),
            price_level=data.get("price_level"),
            business_status=data.get("business_status"),
            photos=data.get("photos"),
            opening_hours=data.get("opening_hours")
        )


@dataclass
class SilverRecord:
    """
    Silver layer data record.
    
    Cleaned và enriched data từ bronze layer.
    Đã qua xử lý: validation, normalization, enrichment.
    
    Attributes:
        place_id: Unique identifier (giữ nguyên từ bronze)
        name: Tên đã chuẩn hóa
        location: Geo coordinates đã validate
        category: Category đã enrich
        sub_categories: Danh sách sub-categories
        attributes: Các thuộc tính đã trích xuất
        source: Nguồn dữ liệu
        quality_score: Điểm chất lượng (0-1)
        processed_at: Thời điểm xử lý
    """
    place_id: str
    name: str
    location: Dict[str, float]
    category: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    quality_score: float = 0.0
    processed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Enriched fields
    sub_categories: List[str] = field(default_factory=list)
    business_score: Optional[float] = None
    popularity_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    
    # Normalized fields
    address_normalized: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    # Enrichment metadata
    enrichment_version: str = "1.0"
    enrichment_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "place_id": self.place_id,
            "name": self.name,
            "location": self.location,
            "category": self.category,
            "sub_categories": self.sub_categories,
            "attributes": self.attributes,
            "source": self.source,
            "quality_score": self.quality_score,
            "processed_at": self.processed_at,
            "business_score": self.business_score,
            "popularity_score": self.popularity_score,
            "accessibility_score": self.accessibility_score,
            "address_normalized": self.address_normalized,
            "district": self.district,
            "city": self.city,
            "country": self.country,
            "enrichment_version": self.enrichment_version,
            "enrichment_sources": self.enrichment_sources
        }


@dataclass
class GoldRecord:
    """
    Gold layer data record.
    
    Aggregated business-ready data.
    Đã qua aggregation và tính toán business metrics.
    
    Attributes:
        city: Thành phố
        category_stats: Statistics by category
        district_stats: Statistics by district
        top_places: Top rated places
        insights: Business insights
        aggregated_at: Thời điểm aggregate
    """
    city: str
    total_places: int
    category_stats: Dict[str, Any] = field(default_factory=dict)
    district_stats: Dict[str, Any] = field(default_factory=dict)
    top_places: List[Dict[str, Any]] = field(default_factory=list)
    insights: Dict[str, Any] = field(default_factory=dict)
    aggregated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Quality metrics
    data_quality_score: float = 0.0
    coverage_percentage: float = 0.0
    freshness_days: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "city": self.city,
            "total_places": self.total_places,
            "category_stats": self.category_stats,
            "district_stats": self.district_stats,
            "top_places": self.top_places,
            "insights": self.insights,
            "aggregated_at": self.aggregated_at,
            "data_quality_score": self.data_quality_score,
            "coverage_percentage": self.coverage_percentage,
            "freshness_days": self.freshness_days
        }
