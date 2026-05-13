"""
Pipeline Management API Schemas
===============================
Pydantic models cho pipeline management API
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section II

Mục đích:
- Định nghĩa request/response models cho Pipeline Management API
- Cung cấp validation và serialization cho API endpoints
- Tài liệu hóa API schema cho OpenAPI/Swagger

All models kế thừa từ Pydantic BaseModel để có:
- Automatic validation
- JSON serialization/deserialization
- Type checking
- Documentation generation
"""

# Import BaseModel từ pydantic - base class cho tất cả schema models
# BaseModel cung cấp validation, serialization, và JSON schema generation
from pydantic import BaseModel, Field

# Import type hints cho type checking và documentation
# List: Danh sách items cùng type
# Optional: Type có thể None
# Dict: Dictionary với key-value pairs
# Any: Bất kỳ type nào
from typing import List, Optional, Dict, Any

# Import datetime để xử lý timestamps trong API
from datetime import datetime

# Import Enum để định nghĩa các enumeration types
# Enum giúp giới hạn giá trị có thể nhận của một field
from enum import Enum


# ============================================
# ENUMERATIONS
# ============================================
# Các enumeration types để giới hạn giá trị hợp lệ

class PipelineExecutionType(str, Enum):
    """
    Enumeration cho loại pipeline execution
    
    Giới hạn các giá trị hợp lệ cho execution_type field
    Kế thừa từ str để có thể serialize sang JSON string
    
    Values:
        FULL_SYNC: Đồng bộ toàn bộ dữ liệu từ tất cả sources
        INCREMENTAL_SYNC: Chỉ đồng bộ dữ liệu mới/thay đổi
        SPECIFIC_CITY: Chỉ xử lý một city cụ thể
        SPECIFIC_CATEGORY: Chỉ xử lý một category cụ thể
        BACKFILL: Điền dữ liệu lịch sử cho khoảng thời gian cụ thể
    """
    
    # Đồng bộ toàn bộ dữ liệu
    # Dùng cho lần chạy đầu tiên hoặc khi cần refresh toàn bộ
    FULL_SYNC = "full_sync"
    
    # Đồng bộ incremental - chỉ dữ liệu mới hoặc thay đổi
    # Hiệu quả cho scheduled runs hàng ngày/giờ
    INCREMENTAL_SYNC = "incremental_sync"
    
    # Xử lý một city cụ thể
    # Dùng khi cần cập nhật nhanh cho một city
    SPECIFIC_CITY = "specific_city"
    
    # Xử lý một category cụ thể
    # Dùng khi cần cập nhận một loại POI
    SPECIFIC_CATEGORY = "specific_category"
    
    # Backfill dữ liệu lịch sử
    # Dùng để điền dữ liệu cho khoảng thời gian trong quá khứ
    BACKFILL = "backfill"
    
    # Khởi động lại pipeline thất bại
    RESTART = "restart"


# ============================================
# REQUEST MODELS
# ============================================
# Các models để validate API request bodies

class PipelineExecutionRequest(BaseModel):
    """
    Request model cho POST /api/v1/pipeline/start
    
    Validate và document các parameters cần thiết để khởi động pipeline
    Tất cả fields đều có default values hoặc optional để dễ sử dụng
    
    Example JSON body:
        {
            "cities": ["tokyo", "osaka"],
            "categories": ["restaurant", "hotel"],
            "execution_type": "full_sync",
            "batch_size": 1000,
            "max_retries": 3
        }
    """
    
    # Danh sách cities cần xử lý
    # Optional: Nếu không cung cấp, sẽ xử lý tất cả cities trong config
    # Items: String identifiers (lowercase, no spaces)
    # Examples: "tokyo", "osaka", "kyoto"
    cities: Optional[List[str]] = Field(
        default=None,
        description="Danh sách cities để xử lý. Nếu None, xử lý tất cả cities trong config"
    )
    
    # Danh sách categories cần xử lý
    # Optional: Nếu không cung cấp, sẽ xử lý tất cả categories
    # Items: Category identifiers (lowercase, snake_case)
    # Examples: "restaurant", "tourist_attraction", "hotel"
    categories: Optional[List[str]] = Field(
        default=None,
        description="Danh sách categories để xử lý. Nếu None, xử lý tất cả categories"
    )
    
    # Loại execution - bắt buộc phải cung cấp
    # ... (ellipsis) nghĩa là required field
    # Chỉ chấp nhận các giá trị trong PipelineExecutionType enum
    execution_type: PipelineExecutionType = Field(
        ...,  # Required field
        description="Loại execution: full_sync, incremental_sync, specific_city, specific_category, backfill, restart"
    )
    
    # Batch size cho data processing
    # Default: 1000 records mỗi batch
    # Tối ưu: Lớn hơn cho throughput cao, nhỏ hơn cho memory thấp
    batch_size: Optional[int] = Field(
        default=1000,
        ge=100,      # Greater than or equal to 100
        le=10000,    # Less than or equal to 10000
        description="Batch size cho processing (records per batch). Default: 1000"
    )
    
    # Số lần retry tối đa khi thất bại
    # Default: 3 lần retry
    # Mỗi retry sẽ có exponential backoff delay
    max_retries: Optional[int] = Field(
        default=3,
        ge=0,
        le=10,
        description="Số lần retry tối đa khi thất bại. Default: 3"
    )
    
    # Timeout cho mỗi task (giây)
    # Default: 300 giây (5 phút)
    # Nếu task chạy lâu hơn timeout, sẽ bị cancel và retry
    timeout_seconds: Optional[int] = Field(
        default=300,
        ge=60,
        le=3600,
        description="Timeout cho mỗi task (giây). Default: 300"
    )
    
    # Số processes/tasks chạy song song
    # Default: 4 parallel processes
    # Tùy chỉnh dựa trên CPU cores và I/O capacity
    parallelism: Optional[int] = Field(
        default=4,
        ge=1,
        le=16,
        description="Số processes song song. Default: 4"
    )
    
    # Priority level cho execution
    # Default: "normal"
    # Các giá trị: "low", "normal", "high", "critical"
    # Ảnh hưởng đến queue ordering và resource allocation
    priority: Optional[str] = Field(
        default="normal",
        pattern="^(low|normal|high|critical)$",  # Regex validation
        description="Priority level: low, normal, high, critical. Default: normal"
    )


# ============================================
# RESPONSE MODELS
# ============================================
# Các models để structure API responses

class PipelineExecutionResponse(BaseModel):
    """
    Response model cho POST /api/v1/pipeline/start
    
    Trả về thông tin về pipeline execution vừa được khởi tạo
    Client dùng execution_id để theo dõi progress và query status
    
    Example JSON response:
        {
            "execution_id": "pipeline_20260509_053000_user123",
            "status": "started",
            "message": "Pipeline execution started successfully",
            "started_at": "2026-05-09T05:30:00Z",
            "cities": ["tokyo", "osaka"],
            "categories": ["restaurant"],
            "execution_type": "full_sync"
        }
    """
    
    # Unique identifier cho execution
    # Format: pipeline_{timestamp}_{user_id}
    # Client lưu lại để query status và stop nếu cần
    execution_id: str = Field(
        ...,  # Required
        description="ID unique của pipeline execution. Dùng để theo dõi và quản lý"
    )
    
    # Trạng thái hiện tại của execution
    # Ngay sau khi start, thường là "started" hoặc "pending"
    status: str = Field(
        ...,  # Required
        description="Trạng thái hiện tại: started, pending, running, completed, failed"
    )
    
    # Thông báo cho người dùng
    # Human-readable message về kết quả operation
    message: str = Field(
        ...,  # Required
        description="Thông báo cho người dùng về kết quả"
    )
    
    # Thời điểm bắt đầu execution
    # ISO 8601 format (UTC)
    # Dùng để tính duration và sort executions
    started_at: datetime = Field(
        ...,  # Required
        description="Thời gian bắt đầu (ISO 8601 UTC)"
    )
    
    # Cities được xử lý trong execution này
    # Có thể None nếu execution xử lý tất cả cities
    cities: Optional[List[str]] = Field(
        default=None,
        description="Cities được xử lý. None = tất cả cities"
    )
    
    # Categories được xử lý trong execution này
    # Có thể None nếu execution xử lý tất cả categories
    categories: Optional[List[str]] = Field(
        default=None,
        description="Categories được xử lý. None = tất cả categories"
    )
    
    # Loại execution đã chọn
    # Xác nhận lại với client loại execution được thực hiện
    execution_type: PipelineExecutionType = Field(
        ...,  # Required
        description="Loại execution được thực hiện"
    )
    
    # ID của execution gốc (chỉ có khi restart)
    # Nếu execution này là restart của execution trước đó,
    # field này chứa ID của execution gốc
    original_execution_id: Optional[str] = Field(
        default=None,
        description="ID của execution gốc (chỉ có khi restart). Dùng để trace execution chain"
    )


class PipelineStatusResponse(BaseModel):
    """Response model cho pipeline status"""
    execution_id: str = Field(..., description="ID của pipeline execution")
    pipeline_name: str = Field(..., description="Tên pipeline")
    status: str = Field(..., description="Trạng thái hiện tại")
    progress: float = Field(..., description="Tiến độ hoàn thành (%)")
    current_stage: str = Field(..., description="Stage hiện tại")
    started_at: Optional[datetime] = Field(None, description="Thời gian bắt đầu")
    completed_at: Optional[datetime] = Field(None, description="Thời gian hoàn thành")
    stages: Dict[str, Any] = Field(..., description="Chi tiết các stages")
    metrics: Dict[str, Any] = Field(..., description="Metrics của execution")
    records_processed: int = Field(..., description="Số records đã xử lý")
    records_failed: int = Field(..., description="Số records thất bại")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi")
    retry_count: int = Field(0, description="Số lần retry")
    last_retry_at: Optional[datetime] = Field(None, description="Lần retry cuối cùng")


class PipelineHistoryResponse(BaseModel):
    """Response model cho pipeline history"""
    executions: List[Dict[str, Any]] = Field(..., description="Danh sách executions")
    total_count: int = Field(..., description="Tổng số executions")
    limit: int = Field(..., description="Limit cho pagination")
    offset: int = Field(..., description="Offset cho pagination")
    has_more: bool = Field(..., description="Có thêm records không")


class PipelineControlRequest(BaseModel):
    """Request model cho pipeline control"""
    action: str = Field(..., description="Action: start, stop, pause, resume, restart")
    execution_id: Optional[str] = Field(None, description="ID của execution")
    reason: Optional[str] = Field(None, description="Lý do cho action")
    force: Optional[bool] = Field(False, description="Force action")


class PipelineDashboardResponse(BaseModel):
    """Response model cho pipeline dashboard"""
    active_pipelines: List[PipelineStatusResponse] = Field(..., description="Các pipeline đang chạy")
    recent_executions: List[Dict[str, Any]] = Field(..., description="Các executions gần đây")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    errors: List[Dict[str, Any]] = Field(..., description="Các errors gần đây")


class PipelineMetricsResponse(BaseModel):
    """Response model cho pipeline metrics"""
    time_range: str = Field(..., description="Time range cho metrics")
    period: Dict[str, str] = Field(..., description="Period information")
    execution_metrics: Dict[str, Any] = Field(..., description="Execution statistics")
    data_metrics: Dict[str, Any] = Field(..., description="Data processing statistics")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance statistics")


class PipelineConfigRequest(BaseModel):
    """Request model cho pipeline configuration"""
    source_enabled: Optional[bool] = Field(None, description="Enable/disable data source")
    category_mapping: Optional[Dict[str, str]] = Field(None, description="Mapping của categories")
    retry_policy: Optional[Dict[str, Any]] = Field(None, description="Retry policy configuration")
    timeout_config: Optional[Dict[str, int]] = Field(None, description="Timeout configuration")
    batch_size: Optional[int] = Field(None, description="Default batch size")
    parallelism: Optional[int] = Field(None, description="Default parallelism")
    schedule_interval: Optional[str] = Field(None, description="Schedule interval")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="Notification settings")


class PipelineConfigResponse(BaseModel):
    """Response model cho pipeline configuration"""
    config_id: str = Field(..., description="ID của configuration")
    config_name: str = Field(..., description="Tên configuration")
    config: PipelineConfigRequest = Field(..., description="Configuration details")
    created_at: datetime = Field(..., description="Thời gian tạo")
    updated_at: datetime = Field(..., description="Thời gian cập nhật")
    created_by: str = Field(..., description="Người tạo")
    updated_by: str = Field(..., description="Người cập nhật")
    is_active: bool = Field(..., description="Configuration có active không")


class DataQualityReport(BaseModel):
    """Response model cho data quality report"""
    time_range: str = Field(..., description="Time range cho report")
    period: Dict[str, str] = Field(..., description="Period information")
    quality_summary: Dict[str, Any] = Field(..., description="Quality summary statistics")
    quality_trends: Dict[str, str] = Field(..., description="Quality trends")
    detailed_metrics: Dict[str, Any] = Field(..., description="Detailed quality metrics")


class PipelineError(BaseModel):
    """Model cho pipeline error"""
    error_id: str = Field(..., description="ID của error")
    execution_id: str = Field(..., description="ID của execution")
    error_type: str = Field(..., description="Loại error")
    error_message: str = Field(..., description="Thông báo lỗi")
    severity: str = Field(..., description="Severity level")
    timestamp: datetime = Field(..., description="Thời gian xảy ra")
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    context: Dict[str, Any] = Field(..., description="Context information")
    resolved: bool = Field(False, description="Error đã được resolve chưa")
    resolved_at: Optional[datetime] = Field(None, description="Thời gian resolve")
    resolved_by: Optional[str] = Field(None, description="Người resolve")


class PipelineHealthResponse(BaseModel):
    """Response model cho pipeline health check"""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Thời gian check")
    checks: Dict[str, Any] = Field(..., description="Health check details")
    uptime_percentage: Optional[float] = Field(None, description="Uptime percentage")
    last_error: Optional[Dict[str, Any]] = Field(None, description="Error gần nhất")
    performance_score: Optional[float] = Field(None, description="Performance score")


class PipelineNotification(BaseModel):
    """Model cho pipeline notification"""
    notification_id: str = Field(..., description="ID của notification")
    execution_id: str = Field(..., description="ID của execution")
    notification_type: str = Field(..., description="Loại notification")
    title: str = Field(..., description="Tiêu đề notification")
    message: str = Field(..., description="Nội dung notification")
    severity: str = Field(..., description="Severity level")
    timestamp: datetime = Field(..., description="Thời gian tạo")
    acknowledged: bool = Field(False, description="Đã được acknowledge chưa")
    acknowledged_at: Optional[datetime] = Field(None, description="Thời gian acknowledge")
    channels: List[str] = Field(..., description="Notification channels")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class PipelineStage(BaseModel):
    """Model cho pipeline stage"""
    stage_id: str = Field(..., description="ID của stage")
    stage_name: str = Field(..., description="Tên stage")
    stage_order: int = Field(..., description="Thứ tự của stage")
    status: str = Field(..., description="Trạng thái của stage")
    started_at: Optional[datetime] = Field(None, description="Thời gian bắt đầu")
    completed_at: Optional[datetime] = Field(None, description="Thời gian hoàn thành")
    duration_seconds: Optional[float] = Field(None, description="Duration trong giây")
    input_records: int = Field(0, description="Số records input")
    output_records: int = Field(0, description="Số records output")
    error_records: int = Field(0, description="Số records error")
    metrics: Dict[str, Any] = Field(..., description="Stage metrics")
    logs: List[str] = Field(..., description="Stage logs")
    retry_count: int = Field(0, description="Số lần retry")
    last_retry_at: Optional[datetime] = Field(None, description="Lần retry cuối cùng")


class PipelineResource(BaseModel):
    """Model cho pipeline resource"""
    resource_id: str = Field(..., description="ID của resource")
    resource_type: str = Field(..., description="Loại resource")
    resource_name: str = Field(..., description="Tên resource")
    status: str = Field(..., description="Trạng thái")
    created_at: datetime = Field(..., description="Thời gian tạo")
    updated_at: datetime = Field(..., description="Thời gian cập nhật")
    usage_count: int = Field(0, description="Số lần sử dụng")
    last_used_at: Optional[datetime] = Field(None, description="Lần sử dụng cuối cùng")
    metadata: Dict[str, Any] = Field(..., description="Resource metadata")
    cleanup_policy: Optional[Dict[str, Any]] = Field(None, description="Cleanup policy")


class PipelineAlert(BaseModel):
    """Model cho pipeline alert"""
    alert_id: str = Field(..., description="ID của alert")
    alert_type: str = Field(..., description="Loại alert")
    severity: str = Field(..., description="Severity level")
    title: str = Field(..., description="Tiêu đề alert")
    message: str = Field(..., description="Nội dung alert")
    execution_id: Optional[str] = Field(None, description="ID của execution liên quan")
    metric_name: Optional[str] = Field(None, description="Tên metric liên quan")
    threshold_value: Optional[float] = Field(None, description="Giá trị threshold")
    actual_value: Optional[float] = Field(None, description="Giá trị thực tế")
    triggered_at: datetime = Field(..., description="Thời gian trigger")
    acknowledged: bool = Field(False, description="Đã được acknowledge chưa")
    acknowledged_at: Optional[datetime] = Field(None, description="Thời gian acknowledge")
    resolved: bool = Field(False, description="Đã được resolve chưa")
    resolved_at: Optional[datetime] = Field(None, description="Thời gian resolve")
    notification_sent: bool = Field(False, description="Notification đã được gửi chưa")
    metadata: Dict[str, Any] = Field(..., description="Alert metadata")


class PipelineBackup(BaseModel):
    """Model cho pipeline backup"""
    backup_id: str = Field(..., description="ID của backup")
    backup_type: str = Field(..., description="Loại backup")
    execution_id: Optional[str] = Field(None, description="ID của execution liên quan")
    backup_name: str = Field(..., description="Tên backup")
    description: Optional[str] = Field(None, description="Mô tả backup")
    status: str = Field(..., description="Trạng thái backup")
    created_at: datetime = Field(..., description="Thời gian tạo")
    completed_at: Optional[datetime] = Field(None, description="Thời gian hoàn thành")
    file_size_bytes: Optional[int] = Field(None, description="Kích thước file (bytes)")
    file_count: int = Field(0, description="Số file")
    storage_location: str = Field(..., description="Vị trí lưu trữ")
    retention_days: int = Field(30, description="Số ngày retention")
    metadata: Dict[str, Any] = Field(..., description="Backup metadata")


class PipelineSchedule(BaseModel):
    """Model cho pipeline schedule"""
    schedule_id: str = Field(..., description="ID của schedule")
    schedule_name: str = Field(..., description="Tên schedule")
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field(..., description="Timezone")
    is_active: bool = Field(True, description="Schedule có active không")
    execution_type: PipelineExecutionType = Field(..., description="Loại execution")
    cities: Optional[List[str]] = Field(None, description="Cities để xử lý")
    categories: Optional[List[str]] = Field(None, description="Categories để xử lý")
    last_run_at: Optional[datetime] = Field(None, description="Lần chạy cuối cùng")
    next_run_at: Optional[datetime] = Field(None, description="Lần chạy tiếp theo")
    run_count: int = Field(0, description="Số lần đã chạy")
    success_count: int = Field(0, description="Số lần thành công")
    failure_count: int = Field(0, description="Số lần thất bại")
    created_at: datetime = Field(..., description="Thời gian tạo")
    updated_at: datetime = Field(..., description="Thời gian cập nhật")
    created_by: str = Field(..., description="Người tạo")
    updated_by: str = Field(..., description="Người cập nhật")
    metadata: Dict[str, Any] = Field(..., description="Schedule metadata")
