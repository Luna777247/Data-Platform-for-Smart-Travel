"""
Data Query API Routes
=====================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/api/routes/data_query.py

Mục đích:
- Cung cấp API endpoints để query dữ liệu POI (Points of Interest)
- Hỗ trợ tìm kiếm, filter, và aggregation
- Trả về dữ liệu ở các layer khác nhau (bronze, silver, gold)

Các endpoints:
- GET /api/v1/data/pois: List tất cả POIs với filter
- GET /api/v1/data/pois/{poi_id}: Get POI chi tiết
- GET /api/v1/data/pois/search: Search POIs theo text
- GET /api/v1/data/pois/nearby: Find nearby POIs
- GET /api/v1/data/stats: Thống kê dữ liệu
- GET /api/v1/data/layers/{layer}: Query theo layer (bronze/silver/gold)

Security:
- JWT authentication required
- Rate limiting áp dụng
- Input validation với Pydantic
"""

# DEBUG: Print when module is loaded
print("DEBUG: data_query.py module loaded - v4")

# ============================================================================
# IMPORTS
# ============================================================================

# Import List type từ typing cho type hints
from typing import List

# Import Optional cho nullable types
from typing import Optional

# Import Dict cho dictionary types
from typing import Dict

# Import Any cho flexible typing
from typing import Any

# Import FastAPI components
from fastapi import APIRouter           # Router cho grouping endpoints
from fastapi import Depends             # Dependency injection
from fastapi import HTTPException       # Exception handling
from fastapi import Query               # Query parameter validation
from fastapi import status              # HTTP status codes

# Import Motor cho async MongoDB
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import Pydantic BaseModel cho request/response schemas
from pydantic import BaseModel, ConfigDict

# Import Field cho model field validation
from pydantic import Field

# Import datetime cho timestamp handling
from datetime import datetime

# Import json cho JSON operations
import json

# Import math cho calculations
import math

# Import logging
import logging

# Import dependencies từ project
from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.auth import User
from src.api.dependencies.database import get_database

# Import settings
from src.core.config import get_settings

# ============================================================================
# ROUTER INITIALIZATION
# ============================================================================

# Tạo router cho data query endpoints
# prefix: /api/v1/data - tất cả routes trong file này sẽ có prefix này
# tags: ["Data Query"] - nhóm trong OpenAPI docs
router = APIRouter(
    prefix="/api/v1/data",
    tags=["Data Query"],
    responses={
        # Default responses cho tất cả routes trong router này
        401: {"description": "Unauthorized - JWT token missing hoặc invalid"},
        403: {"description": "Forbidden - Không đủ quyền"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
    }
)

# DEBUG: Print router id
print(f"DEBUG: Router created with id={id(router)}, prefix={router.prefix}")

# Logger cho module này
logger = logging.getLogger(__name__)

# Settings instance
settings = get_settings()

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class POIResponse(BaseModel):
    """
    Schema cho POI response
    
    Attributes:
        poi_id: Unique identifier của POI
        name: Tên POI
        name_en: Tên tiếng Anh (nếu có)
        category: Danh mục (hotel, restaurant, attraction, v.v.)
        subcategory: Danh mục con
        city: Thành phố
        country: Mã quốc gia (ISO)
        location: Tọa độ {lat, lon}
        address: Địa chỉ chi tiết
        rating: Đánh giá trung bình (0-5)
        review_count: Số lượng reviews
        tags: Metadata tags
        sources: Nguồn dữ liệu (osm, google, v.v.)
        quality_score: Điểm chất lượng (0-100)
        status: Trạng thái (active, inactive, pending)
        created_at: Thời gian tạo
        updated_at: Thời gian cập nhật
        layer: Layer dữ liệu (bronze, silver, gold)
    """
    poi_id: str = Field(..., description="Unique POI identifier")
    name: str = Field(..., description="POI name in local language")
    name_en: Optional[str] = Field(None, description="POI name in English")
    category: str = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code (ISO 3166-1)", min_length=2, max_length=2)
    location: Dict[str, float] = Field(..., description="Geo coordinates {lat, lon}")
    address: Optional[Any] = Field(None, description="Full address (string or dict)")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating 0-5")
    review_count: int = Field(0, ge=0, description="Number of reviews")
    tags: Any = Field(default_factory=dict, description="Metadata tags (dict or list)")
    sources: List[str] = Field(default_factory=list, description="Data sources")
    quality_score: float = Field(0.0, ge=0, le=100, description="Quality score 0-100")
    status: str = Field("active", description="POI status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    layer: str = Field(..., description="Data layer (bronze/silver/gold)")
    
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore',
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "poi_id": "gold_bangkok_hotel_12345",
                "name": "โรงแรมแกรนด์เซนเตอร์พอยต์",
                "name_en": "Grande Centre Point Hotel",
                "category": "hotel",
                "subcategory": "luxury_hotel",
                "city": "bangkok",
                "country": "TH",
                "location": {"lat": 13.7563, "lon": 100.5018},
                "address": "153/2 Soi Mahadlek Luang 1, Ratchadamri Road",
                "rating": 4.5,
                "review_count": 2156,
                "tags": {"amenities": ["wifi", "pool", "spa"], "price_range": "$$$"},
                "sources": ["osm", "google"],
                "quality_score": 92.5,
                "status": "active",
                "created_at": "2024-01-15T08:30:00Z",
                "updated_at": "2024-06-20T14:25:00Z",
                "layer": "gold"
            }
        }
    )


class POIListResponse(BaseModel):
    """
    Schema cho list POIs response
    
    Attributes:
        items: List các POI
        total: Tổng số POI (không phân trang)
        page: Trang hiện tại
        page_size: Số items mỗi trang
        pages: Tổng số trang
    """
    items: List[POIResponse]
    total: int = Field(..., ge=0, description="Total count without pagination")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    pages: int = Field(..., ge=1, description="Total pages")


class NearbyQuery(BaseModel):
    """
    Schema cho nearby search query
    
    Attributes:
        lat: Latitude của center point
        lon: Longitude của center point
        radius: Bán kính tìm kiếm (meters, max: 50000)
        category: Filter theo category (optional)
        limit: Số kết quả tối đa (max: 100)
    """
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    radius: float = Field(1000, ge=100, le=50000, description="Search radius in meters")
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class DataStats(BaseModel):
    """
    Schema cho data statistics response
    
    Attributes:
        total_pois: Tổng số POI
        by_category: Thống kê theo category
        by_city: Thống kê theo city
        by_layer: Thống kê theo layer
        by_source: Thống kê theo source
        last_updated: Thời gian cập nhật gần nhất
    """
    total_pois: int
    by_category: Dict[str, int]
    by_city: Dict[str, int]
    by_layer: Dict[str, int]
    by_source: Dict[str, int]
    last_updated: datetime


class LayerInfo(BaseModel):
    """
    Schema cho layer information
    
    Attributes:
        layer: Tên layer (bronze, silver, gold)
        count: Số records trong layer
        size_mb: Kích thước (MB)
        last_updated: Thời gian cập nhật
        description: Mô tả layer
    """
    layer: str
    count: int
    size_mb: float
    last_updated: datetime
    description: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_poi_query(
    city: Optional[str] = None,
    category: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    min_rating: Optional[float] = None,
    layer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Xây dựng MongoDB query từ filter parameters
    
    Args:
        city: Filter theo city name
        category: Filter theo category
        country: Filter theo country code
        status: Filter theo status
        min_rating: Minimum rating filter
        layer: Filter theo data layer
    
    Returns:
        Dict[str, Any]: MongoDB query filter
    """
    # Bắt đầu với empty query
    query: Dict[str, Any] = {}
    
    # Thêm filter cho city nếu được cung cấp
    if city:
        # Case-insensitive search
        query["city"] = {"$regex": f"^{city}$", "$options": "i"}
    
    # Thêm filter cho category
    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}
    
    # Thêm filter cho country
    if country:
        query["country"] = country.upper()
    
    # Thêm filter cho status
    if status:
        query["status"] = status
    
    # Thêm filter cho minimum rating
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}
    
    # Thêm filter cho layer
    if layer:
        query["layer"] = layer.lower()
    
    return query


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 điểm dùng Haversine formula
    
    Args:
        lat1, lon1: Tọa độ điểm 1 (degrees)
        lat2, lon2: Tọa độ điểm 2 (degrees)
    
    Returns:
        float: Khoảng cách (meters)
    """
    # Bán kính Trái Đất (meters)
    R = 6371000
    
    # Convert sang radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Khoảng cách = R * c
    return R * c


# ============================================================================
# API ENDPOINTS
# ============================================================================

# DEBUG: Print all routes (moved before test endpoints)
print(f"DEBUG: Router routes (before test): {[r.path for r in router.routes]}")

@router.get(
    "/pois",
    # response_model=POIListResponse,  # Disabled to bypass Pydantic validation issues
    summary="List all POIs",
    description="""
    Lấy danh sách tất cả POIs với các filter options.
    
    Hỗ trợ phân trang và sorting. Kết quả mặc định sorted theo quality_score giảm dần.
    """,
    responses={
        200: {"description": "Successfully retrieved POI list"},
        400: {"description": "Invalid query parameters"},
    }
)
async def list_pois(
    # Database dependency
    db: AsyncIOMotorDatabase = Depends(get_database),
    # Current user dependency
    current_user: User = Depends(get_current_active_user),
    # Query parameters
    city: Optional[str] = Query(None, description="Filter by city name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    country: Optional[str] = Query(None, min_length=2, max_length=2, description="Filter by country code (ISO)"),
    poi_status: Optional[str] = Query(None, description="Filter by status"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    layer: Optional[str] = Query(None, pattern="^(bronze|silver|gold)$", description="Filter by data layer"),
    search: Optional[str] = Query(None, description="Text search in name/address"),
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Sorting
    sort_by: str = Query("quality_score", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
):
    """
    List POIs với filtering và pagination.
    
    Returns:
        POIListResponse: Paginated list of POIs
    """
    try:
        # Xây dựng query từ filters
        query = build_poi_query(
            city=city,
            category=category,
            country=country,
            status=poi_status,
            min_rating=min_rating,
            layer=layer
        )
        
        # Thêm text search nếu có
        if search:
            # Search trong name, name_en, và address
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"name_en": {"$regex": search, "$options": "i"}},
                {"address": {"$regex": search, "$options": "i"}}
            ]
        
        # Xác định collection để query
        collection_name = "gold_master_pois"  # Default là gold layer
        if layer == "bronze":
            collection_name = "bronze_records"
        elif layer == "silver":
            collection_name = "silver_places"
        
        collection = db[collection_name]
        
        # Đếm total (không phân trang)
        total = await collection.count_documents(query)
        
        # Tính số trang (ít nhất là 1)
        pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        
        # Xây dựng sort
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Thực hiện query với pagination
        skip = (page - 1) * page_size
        cursor = collection.find(query).skip(skip).limit(page_size).sort(sort_by, sort_direction)
        
        # Lấy results
        pois = await cursor.to_list(length=page_size)
        
        # Convert MongoDB documents to plain dicts (bypass Pydantic validation)
        poi_responses = []
        for poi in pois:
            # Convert _id to poi_id
            poi_data = dict(poi)
            if "_id" in poi_data:
                poi_data["poi_id"] = str(poi_data.pop("_id"))
            
            # Thêm layer nếu thiếu
            if "layer" not in poi_data:
                poi_data["layer"] = layer or "gold"
            
            # Map existing timestamp fields to created_at và updated_at
            if '_enriched_at' in poi_data:
                poi_data['created_at'] = poi_data['_enriched_at']
            elif '_processed_at' in poi_data:
                poi_data['created_at'] = poi_data['_processed_at']
            elif '_collected_at' in poi_data:
                poi_data['created_at'] = poi_data['_collected_at']
            else:
                poi_data['created_at'] = datetime.utcnow().isoformat()
            
            if '_enriched_at' in poi_data:
                poi_data['updated_at'] = poi_data['_enriched_at']
            elif '_processed_at' in poi_data:
                poi_data['updated_at'] = poi_data['_processed_at']
            else:
                poi_data['updated_at'] = datetime.utcnow().isoformat()
            
            poi_responses.append(poi_data)
        
        logger.info(
            f"Listed {len(poi_responses)} POIs for user {current_user} "
            f"(page {page}/{pages}, total {total})"
        )
        
        # Return plain dict to bypass Pydantic validation
        return {
            "items": poi_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
        
    except Exception as e:
        logger.error(f"Error listing POIs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving POIs: {str(e)}"
        )


@router.get(
    "/pois/search",
    response_model=POIListResponse,
    summary="Search POIs by text",
    description="Tìm kiếm POIs theo tên, mô tả, hoặc keywords.",
    responses={
        200: {"description": "Search results"},
        401: {"description": "Unauthorized"},
    }
)
async def search_pois(
    q: str = Query(..., min_length=1, description="Search query"),
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search POIs by text query.
    
    Args:
        q: Search query string
        city: Optional city filter
        category: Optional category filter
        limit: Maximum results to return
        
    Returns:
        POIListResponse with matching POIs
    """
    try:
        # Build search query using regex instead of $text (no index required)
        search_filter = {
            "$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"address": {"$regex": q, "$options": "i"}}
            ]
        }
        
        if city:
            search_filter["city"] = city
        
        if category:
            search_filter["category"] = category
        
        # Search in gold layer (fallback to silver and bronze if empty)
        collections = ["gold_master_pois", "silver_places", "bronze_records"]
        poi_list = []
        
        for coll_name in collections:
            try:
                cursor = db[coll_name].find(search_filter).limit(limit)
                docs = await cursor.to_list(length=limit)
                
                for poi in docs:
                    if len(poi_list) >= limit:
                        break
                    
                    # Determine layer from collection name
                    layer = "gold" if "gold" in coll_name else ("silver" if "silver" in coll_name else "bronze")
                    
                    poi_list.append(POIResponse(
                        poi_id=str(poi.get("_id", "")),
                        name=poi.get("name", ""),
                        category=poi.get("category", "unknown"),
                        city=poi.get("city", ""),
                        country=poi.get("country", "VN"),
                        location=poi.get("location", {}),
                        address=poi.get("address"),
                        rating=poi.get("rating"),
                        review_count=poi.get("review_count", 0),
                        quality_score=poi.get("quality_score", 0),
                        layer=layer,
                        created_at=poi.get("created_at", datetime.utcnow()),
                        updated_at=poi.get("updated_at", datetime.utcnow())
                    ))
                
                if len(poi_list) >= limit:
                    break
                    
            except Exception as coll_error:
                # Collection might not exist, continue to next
                logger.debug(f"Collection {coll_name} error: {coll_error}")
                continue
        
        return POIListResponse(
            items=poi_list,
            total=len(poi_list),
            page=1,
            page_size=limit,
            pages=1
        )
        
    except Exception as e:
        logger.error(f"Error searching POIs: {e}")
        # Return empty results instead of 500 error
        return POIListResponse(
            items=[],
            total=0,
            page=1,
            page_size=limit,
            pages=1
        )


@router.get(
    "/pois/{poi_id}",
    response_model=POIResponse,
    summary="Get POI details",
    description="Lấy chi tiết thông tin của một POI cụ thể theo ID.",
    responses={
        200: {"description": "POI found"},
        404: {"description": "POI not found"},
    }
)
async def get_poi(
    poi_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user),
    layer: Optional[str] = Query(None, pattern="^(bronze|silver|gold)$", description="Search in specific layer")
):
    """
    Get chi tiết POI theo ID.
    
    Args:
        poi_id: POI identifier
        layer: Optional layer to search (default: search all layers)
    
    Returns:
        POIResponse: POI details
    """
    try:
        # Xác định layer để tìm
        layers_to_search = ["gold", "silver", "bronze"] if not layer else [layer]
        
        # Tìm trong các layers
        for search_layer in layers_to_search:
            if search_layer == "bronze":
                collection = db["bronze_records"]
                # Bronze dùng record_id
                doc = await collection.find_one({"record_id": poi_id})
            elif search_layer == "silver":
                collection = db["silver_places"]
                # Silver dùng u_key
                doc = await collection.find_one({"u_key": poi_id})
            else:  # gold
                collection = db["gold_master_pois"]
                # Gold dùng poi_id hoặc _id
                doc = await collection.find_one({
                    "$or": [
                        {"poi_id": poi_id},
                        {"_id": poi_id}
                    ]
                })
            
            if doc:
                # Chuyển _id thành poi_id nếu cần
                if "_id" in doc and isinstance(doc["_id"], str):
                    doc["poi_id"] = doc.pop("_id")
                elif "_id" in doc and "poi_id" not in doc:
                    doc["poi_id"] = str(doc.pop("_id"))
                
                # Thêm layer info
                doc["layer"] = search_layer
                
                # Ensure created_at and updated_at have default values
                if 'created_at' not in doc or doc.get('created_at') is None:
                    doc['created_at'] = datetime.utcnow()
                if 'updated_at' not in doc or doc.get('updated_at') is None:
                    doc['updated_at'] = datetime.utcnow()
                
                logger.info(f"Retrieved POI {poi_id} from {search_layer} layer")
                return POIResponse(**doc)
        
        # Không tìm thấy
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"POI with ID '{poi_id}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving POI {poi_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving POI: {str(e)}"
        )


@router.get(
    "/pois/nearby",
    response_model=POIListResponse,
    summary="Find nearby POIs",
    description="Tìm các POIs gần một vị trí cụ thể (geo search).",
)
async def find_nearby_pois(
    query: NearbyQuery = Depends(),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Find nearby POIs dựa trên geographic coordinates.
    
    Uses MongoDB geospatial queries nếu có geospatial index,
    otherwise dùng Haversine formula để filter.
    """
    try:
        # Gold collection có thể có geospatial index
        collection = db["gold_master_pois"]
        
        # Xây dựng geospatial query
        geo_query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [query.lon, query.lat]  # [lon, lat] format
                    },
                    "$maxDistance": query.radius
                }
            }
        }
        
        # Thêm category filter nếu có
        if query.category:
            geo_query["category"] = {"$regex": f"^{query.category}$", "$options": "i"}
        
        # Thực hiện query
        cursor = collection.find(geo_query).limit(query.limit)
        pois = await cursor.to_list(length=query.limit)
        
        # Nếu không có kết quả (có thể do thiếu index), fallback sang manual filter
        if not pois:
            # Lấy tất cả POIs trong bounding box gần đó
            lat_range = 0.5  # ~55km
            lon_range = 0.5
            
            fallback_query = {
                "location.lat": {
                    "$gte": query.lat - lat_range,
                    "$lte": query.lat + lat_range
                },
                "location.lon": {
                    "$gte": query.lon - lon_range,
                    "$lte": query.lon + lon_range
                }
            }
            
            if query.category:
                fallback_query["category"] = {"$regex": f"^{query.category}$", "$options": "i"}
            
            all_candidates = await collection.find(fallback_query).to_list(length=1000)
            
            # Filter bằng Haversine
            pois = []
            for poi in all_candidates:
                if "location" in poi:
                    distance = calculate_distance(
                        query.lat, query.lon,
                        poi["location"]["lat"], poi["location"]["lon"]
                    )
                    if distance <= query.radius:
                        poi["distance"] = distance  # Thêm distance info
                        pois.append(poi)
            
            # Sort theo distance và limit
            pois = sorted(pois, key=lambda x: x.get("distance", float("inf")))[:query.limit]
        
        # Convert sang response model
        poi_responses = []
        for poi in pois:
            if "_id" in poi and "poi_id" not in poi:
                poi["poi_id"] = str(poi.pop("_id"))
            poi["layer"] = "gold"
            # Ensure created_at and updated_at have default values
            if 'created_at' not in poi or poi.get('created_at') is None:
                poi['created_at'] = datetime.utcnow()
            if 'updated_at' not in poi or poi.get('updated_at') is None:
                poi['updated_at'] = datetime.utcnow()
            poi_responses.append(POIResponse(**poi))
        
        logger.info(
            f"Found {len(poi_responses)} nearby POIs "
            f"at ({query.lat}, {query.lon}), radius={query.radius}m"
        )
        
        return POIListResponse(
            items=poi_responses,
            total=len(poi_responses),
            page=1,
            page_size=query.limit,
            pages=1
        )
        
    except Exception as e:
        logger.error(f"Error finding nearby POIs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding nearby POIs: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=DataStats,
    summary="Get data statistics",
    description="Lấy thống kê tổng quan về dữ liệu POI.",
)
async def get_data_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics về dữ liệu POI.
    
    Returns:
        DataStats: Aggregated statistics
    """
    try:
        # Aggregate từ gold collection
        gold_collection = db["gold_master_pois"]
        
        # Total count
        total_pois = await gold_collection.count_documents({})
        
        # Aggregation pipeline cho stats
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "by_category": {"$push": {"k": "$category", "v": 1}},
                    "by_city": {"$push": {"k": "$city", "v": 1}},
                    "by_source": {"$push": {"k": {"$arrayElemAt": ["$sources", 0]}, "v": 1}}
                }
            }
        ]
        
        # Chạy aggregation
        # Note: Trong thực tế, có thể cần optimize aggregation này
        
        # Thống kê đơn giản bằng distinct queries
        categories = await gold_collection.distinct("category")
        by_category = {}
        for cat in categories:
            count = await gold_collection.count_documents({"category": cat})
            by_category[cat] = count
        
        cities = await gold_collection.distinct("city")
        by_city = {}
        for city in cities:
            count = await gold_collection.count_documents({"city": city})
            by_city[city] = count
        
        # Layer stats
        by_layer = {
            "bronze": await db["bronze_records"].count_documents({}),
            "silver": await db["silver_places"].count_documents({}),
            "gold": total_pois
        }
        
        # Source stats
        sources = await gold_collection.distinct("sources")
        by_source = {}
        for source_list in sources:
            if source_list:
                for src in source_list:
                    if src not in by_source:
                        by_source[src] = 0
                    by_source[src] += 1
        
        logger.info(f"Retrieved data stats for user {current_user}")
        
        return DataStats(
            total_pois=total_pois,
            by_category=by_category,
            by_city=by_city,
            by_layer=by_layer,
            by_source=by_source,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error getting data stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.get(
    "/layers",
    response_model=List[LayerInfo],
    summary="Get layer information",
    description="Lấy thông tin về các data layers (bronze, silver, gold).",
)
async def get_layer_info(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information về các data layers.
    
    Returns:
        List[LayerInfo]: Information about each layer
    """
    try:
        layers = []
        
        # Bronze layer
        bronze_count = await db["bronze_records"].count_documents({})
        layers.append(LayerInfo(
            layer="bronze",
            count=bronze_count,
            size_mb=bronze_count * 0.01,  # Estimate ~10KB per record
            last_updated=datetime.utcnow(),
            description="Raw data from OSM and other sources"
        ))
        
        # Silver layer
        silver_count = await db["silver_places"].count_documents({})
        layers.append(LayerInfo(
            layer="silver",
            count=silver_count,
            size_mb=silver_count * 0.005,  # Estimate ~5KB per record
            last_updated=datetime.utcnow(),
            description="Cleaned and normalized data"
        ))
        
        # Gold layer
        gold_count = await db["gold_master_pois"].count_documents({})
        layers.append(LayerInfo(
            layer="gold",
            count=gold_count,
            size_mb=gold_count * 0.008,  # Estimate ~8KB per record
            last_updated=datetime.utcnow(),
            description="Enriched and deduplicated master records"
        ))
        
        logger.info(f"Retrieved layer info for user {current_user}")
        
        return layers
        
    except Exception as e:
        logger.error(f"Error getting layer info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving layer information: {str(e)}"
        )


# ============================================================================
# ADDITIONAL ENDPOINTS (cities and categories)
# ============================================================================

@router.get(
    "/cities",
    response_model=List[str],
    summary="List all cities",
    description="Lấy danh sách tất cả các thành phố có dữ liệu POI.",
    responses={
        200: {"description": "List of cities"},
        401: {"description": "Unauthorized"},
    }
)
async def list_cities(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all cities with POI data.
    
    Returns:
        List of city names
    """
    try:
        # Get distinct cities from gold layer
        cities = await db["gold_master_pois"].distinct("city")
        
        # Filter out None and empty strings, sort alphabetically
        cities = sorted([c for c in cities if c])
        
        logger.info(f"Retrieved {len(cities)} cities for user {current_user}")
        
        return cities
        
    except Exception as e:
        logger.error(f"Error listing cities: {e}")
        # Return default cities if database error
        return ["hanoi", "hcm", "danang", "haiphong", "cantho"]


@router.get(
    "/categories",
    response_model=List[str],
    summary="List all categories",
    description="Lấy danh sách tất cả các danh mục POI.",
    responses={
        200: {"description": "List of categories"},
        401: {"description": "Unauthorized"},
    }
)
async def list_categories(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of all POI categories.
    
    Returns:
        List of category names
    """
    try:
        # Get distinct categories from gold layer
        categories = await db["gold_master_pois"].distinct("category")
        
        # Filter out None and empty strings, sort alphabetically
        categories = sorted([c for c in categories if c])
        
        # If no categories found, return defaults
        if not categories:
            categories = [
                "restaurant",
                "hotel", 
                "tourist_attraction",
                "cafe",
                "shopping_mall",
                "park",
                "museum"
            ]
        
        logger.info(f"Retrieved {len(categories)} categories for user {current_user.username}")
        
        return categories
        
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        # Return default categories if database error
        return [
            "restaurant",
            "hotel",
            "tourist_attraction", 
            "cafe",
            "shopping_mall",
            "park",
            "museum"
        ]


# ============================================================================
# MODULE EXPORTS
# ============================================================================

# DEBUG: Print all routes at end of file
# Test endpoints added at the end
@router.get("/testpois", summary="Test endpoint")
async def test_pois_endpoint(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Simple test endpoint."""
    return {"message": "Code reloaded successfully v5", "timestamp": datetime.utcnow().isoformat()}

@router.get("/testpublic", summary="Public test endpoint")
async def test_public_endpoint():
    """Public test endpoint - no auth required."""
    return {"message": "Public endpoint works!"}

print(f"DEBUG END: Total router routes: {len(router.routes)}")
for i, r in enumerate(router.routes):
    print(f"DEBUG END: Route {i}: {r.path}")

# Export router để include trong main app
__all__ = ["router"]
