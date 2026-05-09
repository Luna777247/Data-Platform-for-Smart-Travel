"""
Data Schemas cho Smart Travel Data Pipeline
Định nghĩa các schema chuẩn cho Bronze, Silver, Gold layers
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Nguồn dữ liệu"""
    OSM = "osm"
    GOOGLE = "google"
    MANUAL = "manual"


class POICategory(str, Enum):
    """Danh mục POI chuẩn hóa"""
    TOURIST_ATTRACTION = "tourist_attraction"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    CAFE = "cafe"
    SHOPPING_MALL = "shopping_mall"
    PARK = "park"
    CINEMA = "cinema"
    MUSEUM = "museum"


class ProcessingStatus(str, Enum):
    """Trạng thái xử lý"""
    RAW = "raw"
    PROCESSED = "processed"
    ENRICHED = "enriched"
    FAILED = "failed"


class BronzeMetadata(BaseModel):
    """Metadata cho Bronze layer"""
    city: str
    category: POICategory
    source: SourceType
    ingestion_at: datetime
    api_version: str = "0.6"
    record_count: int = 0
    request_url: Optional[str] = None
    processing_time_ms: Optional[int] = None


class BronzeRecord(BaseModel):
    """Schema cho Bronze layer - Raw data"""
    metadata: BronzeMetadata
    source: SourceType
    ingestion_at: datetime
    raw_response: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SilverPlace(BaseModel):
    """Schema chuẩn hóa cho Silver layer"""
    u_key: str = Field(..., description="Unique identifier")
    source_id: str = Field(..., description="ID từ source system")
    name: str = Field(..., description="Tên địa điểm")
    name_en: Optional[str] = Field(None, description="Tên tiếng Anh")
    category: POICategory = Field(..., description="Danh mục chính")
    subcategory: Optional[str] = Field(None, description="Danh mục con")
    city: str = Field(..., description="Thành phố")
    country: str = Field(..., description="Quốc gia")
    address: str = Field(default="", description="Địa chỉ")
    location: Dict[str, float] = Field(..., description="Tọa độ {lat, lon}")
    
    # Thông tin từ OSM tags
    tags: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    source: SourceType = Field(..., description="Nguồn dữ liệu")
    language: str = Field(default="vi", description="Ngôn ngữ chính")
    ingestion_at: datetime = Field(..., description="Thời gian thu thập")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian xử lý")
    raw_file: Optional[str] = Field(None, description="File raw nguồn")
    status: ProcessingStatus = Field(default=ProcessingStatus.PROCESSED, description="Trạng thái xử lý")
    
    @validator('location')
    def validate_location(cls, v):
        if not isinstance(v, dict) or 'lat' not in v or 'lon' not in v:
            raise ValueError('Location must contain lat and lon')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class BusinessMetrics(BaseModel):
    """Business metrics cho Gold layer"""
    popularity_score: float = Field(0.0, ge=0.0, le=1.0, description="Độ phổ biến (0-1)")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Điểm chất lượng (0-1)")
    trust_score: float = Field(0.0, ge=0.0, le=1.0, description="Điểm tin cậy (0-1)")
    completeness_score: float = Field(0.0, ge=0.0, le=1.0, description="Điểm đầy đủ (0-1)")
    category_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Độ tin cậy category (0-1)")
    last_verified: Optional[datetime] = Field(None, description="Lần xác nhận gần nhất")
    verification_count: int = Field(0, ge=0, description="Số lần xác nhận")


class GoldPlace(SilverPlace):
    """Schema cho Gold layer - Business ready"""
    id: str = Field(..., description="Business ID")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Đánh giá trung bình")
    review_count: Optional[int] = Field(None, ge=0, description="Số lượt đánh giá")
    
    # Business metrics
    business_metrics: BusinessMetrics = Field(..., description="Chỉ số kinh doanh")
    
    # Enrichment data
    search_keywords: List[str] = Field(default_factory=list, description="Từ khóa tìm kiếm")
    embedding_text: Optional[str] = Field(None, description="Text cho embedding")
    region_hierarchy: Dict[str, str] = Field(default_factory=dict, description="Phân cấp vùng")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian tạo")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian cập nhật")
    
    # Status
    status: ProcessingStatus = Field(default=ProcessingStatus.ENRICHED, description="Trạng thái cuối")


class DataQualityReport(BaseModel):
    """Báo cáo chất lượng dữ liệu"""
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    missing_coordinates: int
    missing_names: int
    invalid_categories: int
    quality_score: float
    processing_time_ms: int
    errors: List[str] = Field(default_factory=list)


class PipelineConfig(BaseModel):
    """Cấu hình pipeline"""
    source: SourceType
    cities: List[str]
    categories: List[POICategory]
    batch_size: int = 1000
    max_retries: int = 3
    timeout_seconds: int = 60
    enable_validation: bool = True
    enable_deduplication: bool = True
    enable_enrichment: bool = True
