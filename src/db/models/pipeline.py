"""
Pipeline Database Models - MongoDB Document Models
Định nghĩa các MongoDB document models cho pipeline management
Theo thiết kế: SMART_TOURISM_SCHEMAS.json

Mục đích:
- Định nghĩa cấu trúc documents cho pipeline collections
- Cung cấp validation và type safety cho MongoDB documents
- Hỗ trợ serialization/deserialization

Collections:
- pipeline_registry: Định nghĩa các pipelines
- pipeline_execution: Lịch sử thực thi pipelines
- pipeline_stage_execution: Chi tiết từng stage
"""

# Import Enum để định nghĩa các enumeration types
from enum import Enum

# Import datetime để xử lý timestamps
from datetime import datetime

# Import các types từ typing để định nghĩa type hints
from typing import Optional, Dict, List, Any

# Import BaseModel từ pydantic để validation và serialization
from pydantic import BaseModel, Field, ConfigDict

# Import ObjectId từ bson để xử lý MongoDB ObjectIds
from bson import ObjectId

# Import PyObjectId từ pydantic để validate ObjectId strings
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


# ============================================
# CUSTOM PYOBJECTID TYPE
# ============================================
class PyObjectId(ObjectId):
    """
    Custom ObjectId type cho Pydantic models
    
    Cho phép Pydantic validate và serialize MongoDB ObjectId
    ObjectId được serialize sang string trong JSON
    
    Example:
        >>> from src.db.models.pipeline import PyObjectId
        >>> class MyModel(BaseModel):
        ...     id: PyObjectId
        >>> doc = MyModel(id="507f1f77bcf86cd799439011")
        >>> doc.id
        ObjectId('507f1f77bcf86cd799439011')
    """
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """
        Định nghĩa Pydantic core schema cho PyObjectId
        
        Schema này cho phép:
        1. Validate string input sang ObjectId
        2. Serialize ObjectId sang string output
        """
        return core_schema.json_or_python_schema(
            # JSON input (string) -> ObjectId
            json_schema=core_schema.str_schema(),
            # Python input (ObjectId hoặc string) -> ObjectId
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    # Validate là string 24 ký tự hex
                    core_schema.str_schema(min_length=24, max_length=24),
                    # Chuyển sang ObjectId
                    core_schema.no_info_plain_validator_function(cls.validate),
                ]),
            ]),
            # Serialize ObjectId sang string
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )
    
    @classmethod
    def validate(cls, value: Any) -> ObjectId:
        """
        Validate value là một ObjectId hợp lệ
        
        Args:
            value: String hoặc ObjectId cần validate
            
        Returns:
            ObjectId instance
            
        Raises:
            ValueError: Nếu value không phải valid ObjectId
        """
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str):
            # Kiểm tra string có phải valid ObjectId format không
            if not ObjectId.is_valid(value):
                raise ValueError(f"Invalid ObjectId: {value}")
            return ObjectId(value)
        raise ValueError(f"Invalid ObjectId type: {type(value)}")


# ============================================
# ENUMERATIONS
# ============================================
class PipelineStatus(str, Enum):
    """
    Enumeration cho pipeline execution statuses
    
    State machine cho pipeline lifecycle:
    CREATED → REGISTERED → SCHEDULED → QUEUED → INITIALIZING → RUNNING
    → VALIDATING → BRONZE → SILVER → GOLD → COMPLETED
    
    Failure path:
    ANY_STATE → FAILED → RETRY_PENDING → RETRYING → RECOVERED
                                    → FAILED_PERMANENTENTLY
    """
    # Initial states
    CREATED = "created"           # Pipeline vừa được tạo
    REGISTERED = "registered"     # Pipeline đã được đăng ký
    SCHEDULED = "scheduled"       # Pipeline được lên lịch chạy
    QUEUED = "queued"              # Pipeline trong hàng đợi
    INITIALIZING = "initializing"   # Pipeline đang khởi tạo
    
    # Running states
    RUNNING = "running"            # Pipeline đang chạy
    VALIDATING = "validating"       # Đang validate data
    BRONZE = "bronze"              # Đang xử lý bronze layer
    SILVER = "silver"              # Đang xử lý silver layer
    GOLD = "gold"                  # Đang xử lý gold layer
    
    # Completion states
    COMPLETED = "completed"         # Pipeline hoàn thành thành công
    
    # Failure states
    FAILED = "failed"              # Pipeline thất bại
    RETRY_PENDING = "retry_pending" # Đang chờ retry
    RETRYING = "retrying"          # Đang retry
    RECOVERED = "recovered"         # Đã phục hồi từ lỗi
    FAILED_PERMANENTLY = "failed_permanently"  # Retry hết lần, thất bại hoàn toàn
    
    # Control states
    PAUSED = "paused"              # Pipeline tạm dừng
    CANCELLED = "cancelled"         # Pipeline bị hủy


class PipelineExecutionType(str, Enum):
    """
    Enumeration cho loại pipeline execution
    """
    FULL_SYNC = "full_sync"                    # Đồng bộ toàn bộ data
    INCREMENTAL_SYNC = "incremental_sync"       # Đồng bộ incremental
    SPECIFIC_CITY = "specific_city"            # Chỉ xử lý một city
    SPECIFIC_CATEGORY = "specific_category"     # Chỉ xử lý một category
    BACKFILL = "backfill"                      # Backfill historical data


class SeverityLevel(str, Enum):
    """
    Enumeration cho error severity levels
    """
    CRITICAL = "critical"          # Lỗi nghiêm trọng, cần xử lý ngay
    HIGH = "high"                 # Lỗi quan trọng
    MEDIUM = "medium"             # Lỗi trung bình
    LOW = "low"                   # Lỗi nhỏ, cảnh báo
    INFO = "info"                 # Thông tin, không phải lỗi


# ============================================
# BASE MODEL
# ============================================
class MongoBaseModel(BaseModel):
    """
    Base model cho tất cả MongoDB documents
    
    Cung cấp:
    - ObjectId handling với PyObjectId
    - Created_at và updated_at timestamps
    - JSON serialization config
    
    Attributes:
        id: MongoDB ObjectId (_id field)
        created_at: Thời điểm document được tạo
        updated_at: Thời điểm document được cập nhật gần nhất
    """
    
    # ObjectId field - map tới _id trong MongoDB
    # Default None cho insert operations (MongoDB tự tạo)
    id: Optional[PyObjectId] = Field(
        default=None,
        alias="_id",  # Map sang _id field trong MongoDB
        description="MongoDB ObjectId"
    )
    
    # Timestamp khi document được tạo
    # Auto-set trong model_validator nếu không có
    created_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm document được tạo"
    )
    
    # Timestamp cập nhật gần nhất
    # Auto-update trong model_validator
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm cập nhật gần nhất"
    )
    
    model_config = ConfigDict(
        # Cho phép populate bằng field name hoặc alias
        populate_by_name=True,
        # Cho phép arbitrary types (ObjectId, datetime, etc.)
        arbitrary_types_allowed=True,
        # JSON encoders cho custom types
        json_encoders={
            ObjectId: str,  # ObjectId -> string trong JSON
            datetime: lambda v: v.isoformat(),  # datetime -> ISO string
        },
    )


# ============================================
# PIPELINE REGISTRY MODEL
# ============================================
class PipelineRegistry(MongoBaseModel):
    """
    Model cho pipeline_registry collection
    
    Lưu trữ định nghĩa của các pipelines trong hệ thống
    Mỗi document đại diện cho một loại pipeline (osm, google_places, etc.)
    
    Collection: pipeline_registry
    Indexes: pipeline_name (unique), source_name
    
    Example document:
    {
        "_id": ObjectId("..."),
        "pipeline_name": "osm_pipeline",
        "source_name": "osm",
        "version": "1.0.0",
        "enabled": true,
        "stages": ["bronze", "silver", "gold"],
        "created_at": ISODate("2026-05-09T05:27:00Z"),
        "updated_at": ISODate("2026-05-09T05:27:00Z")
    }
    """
    
    # Pipeline identifier - unique, không được null
    pipeline_name: str = Field(
        ...,
        description="Tên unique của pipeline",
        examples=["osm_pipeline", "google_pipeline"]
    )
    
    # Source identifier - nguồn data của pipeline
    source_name: str = Field(
        ...,
        description="Tên nguồn data (osm, google_places, tripadvisor)",
        examples=["osm", "google_places"]
    )
    
    # Pipeline version - semantic versioning
    version: str = Field(
        default="1.0.0",
        description="Phiên bản của pipeline",
        examples=["1.0.0", "2.1.0"]
    )
    
    # Enable/disable flag
    enabled: bool = Field(
        default=True,
        description="Pipeline có được enable không"
    )
    
    # Danh sách các stages trong pipeline
    # Thứ tự trong list = thứ tự thực thi
    stages: List[str] = Field(
        default=["bronze", "silver", "gold"],
        description="Danh sách các stages trong pipeline",
        examples=[["bronze", "silver", "gold"]]
    )
    
    # Stage configuration chi tiết
    # Key: stage name, Value: stage config dict
    stage_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Cấu hình chi tiết cho từng stage"
    )
    
    # Retry policy cho pipeline
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "backoff_type": "exponential",
            "initial_delay_ms": 1000,
            "max_delay_ms": 60000,
            "multiplier": 2.0
        },
        description="Chính sách retry khi thất bại"
    )
    
    # Schedule configuration (optional)
    # Cron expression hoặc interval
    schedule: Optional[str] = Field(
        default=None,
        description="Lịch chạy tự động (cron expression hoặc interval)",
        examples=["0 2 * * *", "1h"]
    )
    
    # Metadata bổ sung
    description: Optional[str] = Field(
        default=None,
        description="Mô tả pipeline"
    )
    
    # Tags cho categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Tags để phân loại pipeline",
        examples=[["production", "critical"]]
    )


# ============================================
# PIPELINE EXECUTION MODEL
# ============================================
class PipelineExecution(MongoBaseModel):
    """
    Model cho pipeline_execution collection
    
    Lưu trữ lịch sử thực thi của các pipelines
    Mỗi document đại diện cho một lần chạy pipeline
    
    Collection: pipeline_execution
    Indexes: execution_id (unique), pipeline_name, status, started_at
    
    Example document:
    {
        "_id": ObjectId("..."),
        "execution_id": "exec_20260509_052700",
        "pipeline_name": "osm_pipeline",
        "source_name": "osm",
        "status": "COMPLETED",
        "execution_type": "full_sync",
        "started_at": ISODate("2026-05-09T05:27:00Z"),
        "completed_at": ISODate("2026-05-09T06:15:00Z"),
        "duration_ms": 2880000,
        "records": {
            "total_processed": 15000,
            "successfully_processed": 14968,
            "failed": 32
        },
        "artifacts": {
            "bronze_location": "s3://bucket/bronze/osm/2026-05-09/",
            "silver_location": "s3://bucket/silver/osm/2026-05-09/"
        }
    }
    """
    
    # Execution identifier - unique, human-readable
    execution_id: str = Field(
        ...,
        description="ID unique của execution",
        examples=["exec_20260509_052700"]
    )
    
    # Reference đến pipeline definition
    pipeline_name: str = Field(
        ...,
        description="Tên pipeline được thực thi"
    )
    
    # Source name (denormalized để tiện query)
    source_name: str = Field(
        ...,
        description="Tên nguồn data"
    )
    
    # Execution type
    execution_type: PipelineExecutionType = Field(
        ...,
        description="Loại execution"
    )
    
    # Current status
    status: PipelineStatus = Field(
        default=PipelineStatus.CREATED,
        description="Trạng thái hiện tại của execution"
    )
    
    # Stage hiện tại đang chạy
    current_stage: Optional[str] = Field(
        default=None,
        description="Stage đang chạy"
    )
    
    # Cities được xử lý trong execution này
    cities: List[str] = Field(
        default_factory=list,
        description="Danh sách cities được xử lý",
        examples=[["tokyo", "osaka", "kyoto"]]
    )
    
    # Categories được xử lý
    categories: List[str] = Field(
        default_factory=list,
        description="Danh sách categories được xử lý",
        examples=[["restaurant", "hotel", "tourist_attraction"]]
    )
    
    # Thời điểm bắt đầu
    started_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm bắt đầu execution"
    )
    
    # Thời điểm hoàn thành
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm hoàn thành execution"
    )
    
    # Duration tính bằng milliseconds
    duration_ms: Optional[int] = Field(
        default=None,
        description="Tổng thời gian thực thi (milliseconds)"
    )
    
    # Thông tin records xử lý
    records: Dict[str, int] = Field(
        default_factory=lambda: {
            "total_processed": 0,
            "successfully_processed": 0,
            "failed": 0,
        },
        description="Thống kê records xử lý"
    )
    
    # Error rate percentage
    error_rate: float = Field(
        default=0.0,
        description="Tỷ lệ lỗi (%)"
    )
    
    # Số lần đã retry
    retry_count: int = Field(
        default=0,
        description="Số lần retry"
    )
    
    # Lần retry cuối cùng
    last_retry_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm retry cuối cùng"
    )
    
    # Artifact locations
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Đường dẫn đến các artifacts tạo ra",
        examples=[{
            "bronze_location": "s3://bucket/bronze/osm/2026-05-09/",
            "silver_location": "s3://bucket/silver/osm/2026-05-09/",
            "gold_location": "s3://bucket/gold/2026-05-09/"
        }]
    )
    
    # Metadata bổ sung
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata bổ sung cho execution"
    )
    
    # Error message nếu thất bại
    error_message: Optional[str] = Field(
        default=None,
        description="Thông báo lỗi nếu execution thất bại"
    )
    
    # Stack trace nếu có exception
    stack_trace: Optional[str] = Field(
        default=None,
        description="Stack trace nếu có exception"
    )


# ============================================
# PIPELINE STAGE EXECUTION MODEL
# ============================================
class PipelineStageExecution(MongoBaseModel):
    """
    Model cho pipeline_stage_execution collection
    
    Lưu trữ chi tiết thực thi của từng stage trong pipeline
    Mỗi document đại diện cho một stage trong một execution
    
    Collection: pipeline_stage_execution
    Indexes: execution_id, stage_name, started_at
    
    Example document:
    {
        "_id": ObjectId("..."),
        "execution_id": "exec_20260509_052700",
        "stage_name": "bronze",
        "stage_order": 1,
        "status": "COMPLETED",
        "started_at": ISODate("2026-05-09T05:27:00Z"),
        "completed_at": ISODate("2026-05-09T05:35:00Z"),
        "duration_ms": 480000,
        "records": {
            "input": 15000,
            "output": 15000,
            "failed": 0
        }
    }
    """
    
    # Reference đến parent execution
    execution_id: str = Field(
        ...,
        description="ID của execution cha"
    )
    
    # Stage identifier
    stage_name: str = Field(
        ...,
        description="Tên của stage",
        examples=["bronze", "silver", "gold"]
    )
    
    # Thứ tự của stage trong pipeline
    stage_order: int = Field(
        ...,
        description="Thứ tự của stage (1, 2, 3, ...)"
    )
    
    # Stage status
    status: PipelineStatus = Field(
        ...,
        description="Trạng thái của stage"
    )
    
    # Thời điểm bắt đầu stage
    started_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm bắt đầu stage"
    )
    
    # Thời điểm hoàn thành stage
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm hoàn thành stage"
    )
    
    # Duration của stage (milliseconds)
    duration_ms: Optional[int] = Field(
        default=None,
        description="Thời gian thực thi stage (ms)"
    )
    
    # Records input vào stage
    input_records: int = Field(
        default=0,
        description="Số records đầu vào"
    )
    
    # Records output từ stage
    output_records: int = Field(
        default=0,
        description="Số records đầu ra"
    )
    
    # Records lỗi
    error_records: int = Field(
        default=0,
        description="Số records bị lỗi"
    )
    
    # Processing metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics chi tiết của stage",
        examples=[{
            "throughput_per_second": 100,
            "memory_mb": 512,
            "cpu_percent": 45
        }]
    )
    
    # Logs của stage
    logs: List[str] = Field(
        default_factory=list,
        description="Logs từ stage execution"
    )
    
    # Retry count
    retry_count: int = Field(
        default=0,
        description="Số lần retry của stage"
    )
    
    # Last retry timestamp
    last_retry_at: Optional[datetime] = Field(
        default=None,
        description="Lần retry cuối cùng"
    )


# ============================================
# PIPELINE ERROR MODEL
# ============================================
class PipelineError(MongoBaseModel):
    """
    Model cho pipeline_errors collection
    
    Lưu trữ lỗi xảy ra trong pipeline execution
    
    Collection: pipeline_errors
    Indexes: execution_id, error_type, severity, timestamp
    """
    
    # Error identifier
    error_id: str = Field(
        ...,
        description="ID unique của error"
    )
    
    # Reference đến execution
    execution_id: str = Field(
        ...,
        description="ID của execution liên quan"
    )
    
    # Error type/category
    error_type: str = Field(
        ...,
        description="Loại lỗi",
        examples=["ConnectionError", "ValidationError", "TimeoutError"]
    )
    
    # Error message
    error_message: str = Field(
        ...,
        description="Thông báo lỗi"
    )
    
    # Severity level
    severity: SeverityLevel = Field(
        ...,
        description="Mức độ nghiêm trọng"
    )
    
    # Thời điểm xảy ra lỗi
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Thời điểm xảy ra lỗi"
    )
    
    # Stack trace
    stack_trace: Optional[str] = Field(
        default=None,
        description="Stack trace đầy đủ"
    )
    
    # Context information
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context khi lỗi xảy ra",
        examples=[{
            "city": "tokyo",
            "category": "restaurant",
            "record_id": "osm_12345"
        }]
    )
    
    # Resolved flag
    resolved: bool = Field(
        default=False,
        description="Lỗi đã được resolve chưa"
    )
    
    # Resolution timestamp
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm resolve"
    )
    
    # Resolved by user
    resolved_by: Optional[str] = Field(
        default=None,
        description="Người resolve lỗi"
    )
