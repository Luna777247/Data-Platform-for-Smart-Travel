"""
POI (Point of Interest) Database Models
Định nghĩa các MongoDB document models cho POI data
Theo thiết kế: SMART_TOURISM_SCHEMAS.json - master_poi collection

Mục đích:
- Định nghĩa cấu trúc documents cho POI collections
- Cung cấp validation và type safety cho MongoDB documents
- Hỗ trợ serialization/deserialization cho API responses

Collections:
- master_poi: Unified POI data từ tất cả sources
- poi_reviews: Aggregated reviews và ratings
- poi_categories: Category definitions và mappings
"""

# Import Enum để định nghĩa các enumeration types
from enum import Enum

# Import datetime để xử lý timestamps
from datetime import datetime

# Import các types từ typing
from typing import Optional, Dict, List, Any

# Import BaseModel và Field từ pydantic
from pydantic import BaseModel, Field, ConfigDict

# Import ObjectId từ bson
from bson import ObjectId

# Import PyObjectId từ pipeline models để reuse
from src.db.models.pipeline import PyObjectId, MongoBaseModel


# ============================================
# ENUMERATIONS
# ============================================
class POICategory(str, Enum):
    """
    Enumeration cho POI categories
    
    Theo thiết kế: Category normalization trong Bronze → Silver processing
    """
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    CAFE = "cafe"
    BAR = "bar"
    MUSEUM = "museum"
    PARK = "park"
    SHOPPING_MALL = "shopping_mall"
    TOURIST_ATTRACTION = "tourist_attraction"
    HISTORICAL_SITE = "historical_site"
    ENTERTAINMENT = "entertainment"
    TRANSPORTATION = "transportation"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    RELIGIOUS_SITE = "religious_site"
    NIGHTLIFE = "nightlife"
    SPORTS = "sports"
    OTHER = "other"


class POISource(str, Enum):
    """
    Enumeration cho POI data sources
    """
    OSM = "osm"                          # OpenStreetMap
    GOOGLE_PLACES = "google_places"      # Google Places API
    TRIPADVISOR = "tripadvisor"          # TripAdvisor
    FOURSQUARE = "foursquare"            # Foursquare/Swarm
    YELP = "yelp"                        # Yelp
    BOOKING = "booking"                  # Booking.com
    CUSTOM = "custom"                    # Custom/manual input


class PriceLevel(int, Enum):
    """
    Enumeration cho price levels
    
    Google Places API style:
    0 = Free
    1 = Inexpensive ($)
    2 = Moderate ($$)
    3 = Expensive ($$$)
    4 = Very Expensive ($$$$)
    """
    FREE = 0
    INEXPENSIVE = 1
    MODERATE = 2
    EXPENSIVE = 3
    VERY_EXPENSIVE = 4


# ============================================
# GEOSPATIAL MODELS
# ============================================
class GeoLocation(BaseModel):
    """
    Model cho geospatial coordinates
    
    Theo GeoJSON Point format cho MongoDB 2dsphere index
    
    Example:
        {
            "type": "Point",
            "coordinates": [139.7454, 35.6586]  # [longitude, latitude]
        }
    """
    
    # GeoJSON type - luôn là "Point" cho single location
    type: str = Field(
        default="Point",
        description="GeoJSON type"
    )
    
    # Coordinates [longitude, latitude]
    # Theo GeoJSON spec: longitude trước, latitude sau
    # Range: longitude [-180, 180], latitude [-90, 90]
    coordinates: List[float] = Field(
        ...,
        description="[longitude, latitude]",
        examples=[[139.7454, 35.6586]]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Point",
                "coordinates": [139.7454, 35.6586]
            }
        }
    )


class Address(BaseModel):
    """
    Model cho địa chỉ chi tiết
    
    Hỗ trợ multiple languages và address components
    """
    
    # Street address - số nhà + tên đường
    street_address: Optional[str] = Field(
        default=None,
        description="Số nhà và tên đường",
        examples=["4 Chome-2-8 Shibakoen"]
    )
    
    # City/District
    city: str = Field(
        ...,
        description="Thành phố/Quận",
        examples=["tokyo", "minato"]
    )
    
    # Prefecture/State
    prefecture: Optional[str] = Field(
        default=None,
        description="Tỉnh/Thành phố trực thuộc trung ương",
        examples=["tokyo", "osaka"]
    )
    
    # Postal code
    postal_code: Optional[str] = Field(
        default=None,
        description="Mã bưu điện",
        examples=["105-0011"]
    )
    
    # Country
    country: str = Field(
        default="japan",
        description="Quốc gia",
        examples=["japan", "vietnam"]
    )
    
    # Country code (ISO 3166-1 alpha-2)
    country_code: Optional[str] = Field(
        default=None,
        description="Mã quốc gia ISO 3166-1 alpha-2",
        examples=["JP", "VN", "US"]
    )
    
    # Formatted address - địa chỉ đầy đủ dạng string
    formatted: Optional[str] = Field(
        default=None,
        description="Địa chỉ đầy đủ dạng string",
        examples=["4 Chome-2-8 Shibakoen, Minato City, Tokyo 105-0011, Japan"]
    )
    
    # Language của address (ISO 639-1)
    language: Optional[str] = Field(
        default=None,
        description="Ngôn ngữ của địa chỉ",
        examples=["en", "ja", "vi"]
    )


# ============================================
# RATING MODELS
# ============================================
class Rating(BaseModel):
    """
    Model cho POI ratings từ multiple sources
    
    Aggregated ratings từ OSM, Google Places, TripAdvisor, etc.
    """
    
    # Overall rating - weighted average từ tất cả sources
    # Range: 0.0 đến 5.0
    overall: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Overall rating (0-5)"
    )
    
    # OSM rating (nếu có)
    osm: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="OpenStreetMap rating"
    )
    
    # Google Places rating
    google: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Google Places rating"
    )
    
    # TripAdvisor rating
    tripadvisor: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="TripAdvisor rating"
    )
    
    # Yelp rating
    yelp: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Yelp rating"
    )
    
    # Số lượng reviews cho overall rating
    review_count: int = Field(
        default=0,
        description="Tổng số reviews"
    )
    
    # Review counts từ từng source
    review_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Review counts từ từng source",
        examples=[{
            "osm": 10,
            "google": 1500,
            "tripadvisor": 800
        }]
    )


# ============================================
# BUSINESS INFO MODELS
# ============================================
class OpeningHours(BaseModel):
    """
    Model cho opening hours
    
    Format: ISO 8601 time format hoặc human-readable strings
    """
    
    # Monday hours
    monday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 2",
        examples=["09:00-22:00", "closed"]
    )
    
    # Tuesday hours
    tuesday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 3"
    )
    
    # Wednesday hours
    wednesday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 4"
    )
    
    # Thursday hours
    thursday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 5"
    )
    
    # Friday hours
    friday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 6"
    )
    
    # Saturday hours
    saturday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa thứ 7"
    )
    
    # Sunday hours
    sunday: Optional[str] = Field(
        default=None,
        description="Giờ mở cửa chủ nhật"
    )
    
    # 24/7 flag
    open_24_7: bool = Field(
        default=False,
        description="Mở cửa 24/7"
    )
    
    # Currently open (real-time status, optional)
    currently_open: Optional[bool] = Field(
        default=None,
        description="Đang mở cửa (real-time)"
    )


class ContactInfo(BaseModel):
    """
    Model cho contact information
    """
    
    # Phone number
    phone: Optional[str] = Field(
        default=None,
        description="Số điện thoại",
        examples=["+81-3-3433-5111"]
    )
    
    # International phone format
    international_phone: Optional[str] = Field(
        default=None,
        description="Số điện thoại quốc tế format",
        examples=["+81 3-3433-5111"]
    )
    
    # Website URL
    website: Optional[str] = Field(
        default=None,
        description="Website URL",
        examples=["https://www.tokyotower.co.jp/"]
    )
    
    # Email
    email: Optional[str] = Field(
        default=None,
        description="Email liên hệ",
        examples=["info@example.com"]
    )
    
    # Facebook page
    facebook: Optional[str] = Field(
        default=None,
        description="Facebook page URL"
    )
    
    # Instagram
    instagram: Optional[str] = Field(
        default=None,
        description="Instagram handle hoặc URL"
    )
    
    # Twitter
    twitter: Optional[str] = Field(
        default=None,
        description="Twitter handle hoặc URL"
    )


# ============================================
# MASTER POI MODEL
# ============================================
class MasterPOI(MongoBaseModel):
    """
    Model cho master_poi collection - Unified POI data
    
    Đây là canonical representation của một POI, aggregated từ
    tất cả data sources (OSM, Google Places, TripAdvisor, etc.)
    
    Collection: master_poi
    Indexes:
    - poi_id (unique)
    - location (2dsphere) - geospatial queries
    - city + category (compound)
    - name (text) - full-text search
    - business_score (descending) - sorting
    
    Example document:
    {
        "_id": ObjectId("..."),
        "poi_id": "poi_tokyo_tower_001",
        "name": "Tokyo Tower",
        "city": "tokyo",
        "country": "japan",
        "category": "tourist_attraction",
        "location": {
            "type": "Point",
            "coordinates": [139.7454, 35.6586]
        },
        "address": {
            "street_address": "4 Chome-2-8 Shibakoen",
            "city": "minato",
            "prefecture": "tokyo",
            "country": "japan",
            "formatted": "4 Chome-2-8 Shibakoen, Minato City, Tokyo 105-0011, Japan"
        },
        "rating": {
            "overall": 4.5,
            "osm": 4.3,
            "google": 4.6,
            "tripadvisor": 4.4,
            "review_count": 12500
        },
        "sources": ["osm", "google_places", "tripadvisor"],
        "business_score": 0.92,
        "created_at": ISODate("2026-05-01T00:00:00Z"),
        "updated_at": ISODate("2026-05-09T05:27:00Z")
    }
    """
    
    # POI unique identifier
    # Format: poi_{city}_{name}_{sequence} hoặc UUID
    poi_id: str = Field(
        ...,
        description="ID unique của POI",
        examples=["poi_tokyo_tower_001"]
    )
    
    # POI name - canonical name (đã được normalize)
    name: str = Field(
        ...,
        description="Tên của POI",
        examples=["Tokyo Tower", "Sushi Dai"]
    )
    
    # Alternative names - tên khác, tên trong ngôn ngữ khác
    alternative_names: List[str] = Field(
        default_factory=list,
        description="Tên khác của POI",
        examples=[["東京タワー", "Tokyo Tower"]]
    )
    
    # City identifier (lowercase, no spaces)
    city: str = Field(
        ...,
        description="Thành phố (normalized)",
        examples=["tokyo", "osaka", "kyoto"]
    )
    
    # Country (lowercase)
    country: str = Field(
        default="japan",
        description="Quốc gia (normalized)",
        examples=["japan", "vietnam", "usa"]
    )
    
    # Category
    category: POICategory = Field(
        ...,
        description="Loại POI"
    )
    
    # Subcategories (optional)
    subcategories: List[str] = Field(
        default_factory=list,
        description="Subcategories",
        examples=[["landmark", "observation_deck"]]
    )
    
    # Geospatial location
    location: GeoLocation = Field(
        ...,
        description="Tọa độ địa lý [longitude, latitude]"
    )
    
    # Address chi tiết
    address: Address = Field(
        ...,
        description="Địa chỉ chi tiết"
    )
    
    # Ratings từ multiple sources
    rating: Rating = Field(
        default_factory=Rating,
        description="Ratings và reviews"
    )
    
    # Data sources đã cung cấp thông tin
    sources: List[POISource] = Field(
        default_factory=list,
        description="Nguồn data",
        examples=[["osm", "google_places", "tripadvisor"]]
    )
    
    # Source IDs - mapping từ source ID sang canonical ID
    # Ví dụ: {"osm": "node_123456789", "google": "ChIJ..."}
    source_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="ID của POI trong từng source"
    )
    
    # Business scoring - calculated score dựa trên popularity, rating, etc.
    # Range: 0.0 đến 1.0
    business_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Business score (0-1)"
    )
    
    # Popularity score
    popularity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Popularity score (0-1)"
    )
    
    # Relevance score (cho search ranking)
    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance score cho search (0-1)"
    )
    
    # Quality score - data quality assessment
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Data quality score (0-1)"
    )
    
    # Search keywords cho full-text search
    # Tự động generate từ name, category, tags
    search_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords cho search",
        examples=[["tokyo tower", "japan landmark", "observation deck"]]
    )
    
    # Tags cho categorization và filtering
    tags: List[str] = Field(
        default_factory=list,
        description="Tags",
        examples=[["landmark", "family-friendly", "photo-spot"]]
    )
    
    # Opening hours
    opening_hours: Optional[OpeningHours] = Field(
        default=None,
        description="Giờ mở cửa"
    )
    
    # Contact information
    contact: Optional[ContactInfo] = Field(
        default=None,
        description="Thông tin liên hệ"
    )
    
    # Price level
    price_level: Optional[PriceLevel] = Field(
        default=None,
        description="Mức giá"
    )
    
    # Amenities/features (cho hotels, restaurants, etc.)
    amenities: List[str] = Field(
        default_factory=list,
        description="Tiện ích/Features",
        examples=[["wifi", "parking", "wheelchair_accessible"]]
    )
    
    # Photos URLs
    photos: List[str] = Field(
        default_factory=list,
        description="URLs của photos"
    )
    
    # Description
    description: Optional[str] = Field(
        default=None,
        description="Mô tả POI"
    )
    
    # Metadata bổ sung
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata bổ sung"
    )
    
    # Flag: POI có được verify không
    verified: bool = Field(
        default=False,
        description="POI đã được verify"
    )
    
    # Flag: POI có active không (soft delete)
    active: bool = Field(
        default=True,
        description="POI đang active"
    )


# ============================================
# POI REVIEW MODEL
# ============================================
class POIReview(MongoBaseModel):
    """
    Model cho poi_reviews collection
    
    Lưu trữ individual reviews từ các sources
    Aggregated trong Gold layer để tính ratings
    
    Collection: poi_reviews
    Indexes: poi_id, source, created_at
    """
    
    # Reference đến POI
    poi_id: str = Field(
        ...,
        description="ID của POI"
    )
    
    # Source của review
    source: POISource = Field(
        ...,
        description="Nguồn review"
    )
    
    # Source review ID
    source_review_id: Optional[str] = Field(
        default=None,
        description="ID của review trong source"
    )
    
    # Author/Reviewer
    author_name: Optional[str] = Field(
        default=None,
        description="Tên người review"
    )
    
    # Author ID trong source (nếu có)
    author_id: Optional[str] = Field(
        default=None,
        description="ID của author"
    )
    
    # Rating (1-5)
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating (1-5)"
    )
    
    # Review text
    text: Optional[str] = Field(
        default=None,
        description="Nội dung review"
    )
    
    # Language của review (ISO 639-1)
    language: Optional[str] = Field(
        default=None,
        description="Ngôn ngữ của review",
        examples=["en", "ja", "vi"]
    )
    
    # Review timestamp trong source
    review_time: Optional[datetime] = Field(
        default=None,
        description="Thời điểm review trong source"
    )
    
    # Likes/helpful votes
    helpful_votes: int = Field(
        default=0,
        description="Số lượt helpful/like"
    )
    
    # Photos trong review
    photos: List[str] = Field(
        default_factory=list,
        description="URLs của photos trong review"
    )
    
    # Sentiment analysis result (optional)
    sentiment: Optional[str] = Field(
        default=None,
        description="Sentiment của review",
        examples=["positive", "neutral", "negative"]
    )
    
    # Flag: Review đã được verify không
    verified: bool = Field(
        default=False,
        description="Review đã được verify"
    )


# ============================================
# POI CATEGORY MODEL
# ============================================
class POICategoryInfo(MongoBaseModel):
    """
    Model cho poi_categories collection
    
    Lưu trữ category definitions và mappings
    
    Collection: poi_categories
    Indexes: category_id, canonical_name
    """
    
    # Category unique identifier
    category_id: str = Field(
        ...,
        description="ID unique của category"
    )
    
    # Canonical name
    canonical_name: str = Field(
        ...,
        description="Tên chuẩn của category",
        examples=["restaurant", "tourist_attraction"]
    )
    
    # Display name trong nhiều languages
    display_names: Dict[str, str] = Field(
        default_factory=dict,
        description="Display names theo ngôn ngữ",
        examples=[{
            "en": "Restaurant",
            "ja": "レストラン",
            "vi": "Nhà hàng"
        }]
    )
    
    # Category hierarchy
    parent_category: Optional[str] = Field(
        default=None,
        description="Parent category ID"
    )
    
    # Subcategories
    subcategories: List[str] = Field(
        default_factory=list,
        description="Danh sách subcategories"
    )
    
    # Mappings từ source categories sang canonical
    # Ví dụ: {"google": ["restaurant", "food"], "osm": ["amenity=restaurant"]}
    source_mappings: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping từ source categories"
    )
    
    # Keywords cho auto-categorization
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords để nhận diện category"
    )
    
    # Icon/Emoji cho category
    icon: Optional[str] = Field(
        default=None,
        description="Icon hoặc emoji",
        examples=["🍽️", "🏨", "🗼"]
    )
    
    # Color cho UI
    color: Optional[str] = Field(
        default=None,
        description="Mã màu cho UI",
        examples=[["#FF6B6B", "#4ECDC4"]]
    )
    
    # Description
    description: Optional[str] = Field(
        default=None,
        description="Mô tả category"
    )
    
    # Metadata bổ sung
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata bổ sung"
    )


# ============================================
# API RESPONSE MODELS
# ============================================
class POIListResponse(BaseModel):
    """
    Model cho API response khi list POIs
    """
    
    pois: List[MasterPOI] = Field(
        ...,
        description="Danh sách POIs"
    )
    
    total_count: int = Field(
        ...,
        description="Tổng số POIs (cho pagination)"
    )
    
    page: int = Field(
        default=1,
        description="Page hiện tại"
    )
    
    page_size: int = Field(
        default=20,
        description="Số items mỗi page"
    )


class POINearbyRequest(BaseModel):
    """
    Model cho nearby POI search request
    """
    
    # Center location [longitude, latitude]
    location: List[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[longitude, latitude]"
    )
    
    # Radius tính bằng meters
    radius: int = Field(
        default=1000,
        ge=100,
        le=50000,
        description="Bán kính tìm kiếm (meters)"
    )
    
    # Category filter (optional)
    category: Optional[POICategory] = Field(
        default=None,
        description="Lọc theo category"
    )
    
    # Limit kết quả
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Số kết quả tối đa"
    )


# ============================================
# MODULE EXPORTS
# ============================================
__all__ = [
    "MasterPOI",
    "POIReview",
    "POICategoryInfo",
    "POICategory",
    "POISource",
    "PriceLevel",
    "GeoLocation",
    "Address",
    "Rating",
    "OpeningHours",
    "ContactInfo",
    "POIListResponse",
    "POINearbyRequest",
]
