"""
Structured Logging Configuration Module
Module cấu hình logging có cấu trúc cho toàn bộ ứng dụng
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section VII - Monitoring

Mục đích:
- Cung cấp structured logging với JSON format
- Tích hợp correlation ID cho distributed tracing
- Hỗ trợ multiple log levels và outputs
- Tương thích với ELK Stack cho centralized logging
"""

# Import logging module từ Python standard library
# Cung cấp infrastructure cho logging
import logging

# Import sys để tương tác với stdin/stdout/stderr
# Dùng để redirect logs trong một số trường hợp đặc biệt
import sys

# Import các classes từ logging module
# Logger: Đối tượng chính để tạo log records
# LogRecord: Đại diện cho một log entry
# StreamHandler: Gửi logs đến streams (stdout, stderr)
# Formatter: Định dạng log records
from logging import Logger, LogRecord, StreamHandler, Formatter

# Import JSONEncoder để serialize log records sang JSON
# Dùng cho structured logging
from json import JSONEncoder

# Import datetime để thêm timestamp vào logs
from datetime import datetime

# Import Optional từ typing để định nghĩa optional parameters
from typing import Optional, Any, Dict

# Import contextvars để lưu trữ correlation ID trong async context
# Correlation ID giúp trace một request qua nhiều services
from contextvars import ContextVar

# Import uuid để tạo unique correlation IDs
import uuid

# ============================================
# GLOBAL CONTEXT VARIABLES
# ============================================
# Context variables để lưu trữ metadata trong async context
# Giúp trace requests qua multiple async calls

# Correlation ID - Unique identifier cho mỗi request
# Dùng để trace một request qua toàn bộ hệ thống
# Ví dụ: API call → Service → Database → Response
# Tất cả logs cùng correlation ID đều thuộc về một request
CORRELATION_ID: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", 
    default=None
)

# Request ID - Identifier cụ thể cho HTTP request
# Có thể khác với correlation ID trong một số trường hợp
REQUEST_ID: ContextVar[Optional[str]] = ContextVar(
    "request_id",
    default=None
)

# User ID - ID của user thực hiện request
# Dùng cho audit logging và security tracking
USER_ID: ContextVar[Optional[str]] = ContextVar(
    "user_id",
    default=None
)


# ============================================
# JSON LOG ENCODER
# ============================================
class JSONLogEncoder(JSONEncoder):
    """
    Custom JSON Encoder cho log records
    
    Xử lý việc serialize các Python objects không JSON-serializable
    mặc định (datetime, Exception objects, etc.) sang JSON format
    
    Attributes:
        indent: Số spaces để indent JSON output (None = compact)
        ensure_ascii: False để hỗ trợ Unicode characters
    """
    
    def default(self, obj: Any) -> Any:
        """
        Serialize objects không được hỗ trợ mặc định bởi JSONEncoder
        
        Args:
            obj: Object cần serialize
            
        Returns:
            JSON-serializable representation của object
            
        Handles:
            - datetime: ISO format string
            - Exception: Dict với type và message
            - set: List
            - bytes: Decoded string
        """
        # Xử lý datetime objects - chuyển sang ISO format
        # ISO format: "2026-05-09T05:27:00.000000"
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Xử lý Exception objects - chuyển sang dict
        # Giúp log exceptions một cách structured
        if isinstance(obj, Exception):
            return {
                "type": type(obj).__name__,
                "message": str(obj),
            }
        
        # Xử lý set objects - chuyển sang list
        # JSON không hỗ trợ set type
        if isinstance(obj, set):
            return list(obj)
        
        # Xử lý bytes - decode sang string nếu có thể
        if isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return obj.hex()
        
        # Fallback: Gọi default method của parent class
        # Nếu vẫn không serialize được, sẽ raise TypeError
        return super().default(obj)


# ============================================
# STRUCTURED LOG FORMATTER
# ============================================
class StructuredLogFormatter(Formatter):
    """
    Custom log formatter cho structured JSON logging
    
    Chuyển đổi LogRecord objects sang JSON format với tất cả
    metadata cần thiết cho observability và debugging
    
    JSON structure bao gồm:
    - timestamp: ISO format
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Tên của logger
    - message: Log message
    - correlation_id: Request correlation ID
    - request_id: HTTP request ID
    - user_id: User ID (nếu có)
    - source: File và line number nơi log được tạo
    - extra: Extra fields từ log record
    
    Attributes:
        encoder: JSONEncoder instance để serialize logs
    """
    
    def __init__(self, indent: Optional[int] = None):
        """
        Khởi tạo StructuredLogFormatter
        
        Args:
            indent: Số spaces để format JSON (None = compact)
                   Dùng indent cho development, không indent cho production
        """
        super().__init__()
        # Tạo JSON encoder với custom default handler
        self.encoder = JSONLogEncoder(indent=indent, ensure_ascii=False)
    
    def format(self, record: LogRecord) -> str:
        """
        Format LogRecord sang JSON string
        
        Args:
            record: LogRecord object cần format
            
        Returns:
            JSON string đại diện cho log entry
            
        Example output:
            {
                "timestamp": "2026-05-09T05:27:00.123456",
                "level": "INFO",
                "logger": "src.services.pipeline",
                "message": "Pipeline started",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "source": {"file": "pipeline.py", "line": 42, "function": "start"}
            }
        """
        # Tạo dict chứa tất cả log data
        log_data: Dict[str, Any] = {
            # Timestamp khi log được tạo
            # record.created là timestamp (seconds since epoch)
            # Chuyển sang datetime object rồi ISO format
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            
            # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            "level": record.levelname,
            
            # Tên của logger (thường là module path)
            "logger": record.name,
            
            # Log message đã được format với arguments
            # getMessage() thực hiện: record.msg % record.args
            "message": record.getMessage(),
        }
        
        # Thêm correlation ID từ context variable nếu có
        # Giúp trace request qua multiple services
        correlation_id = CORRELATION_ID.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Thêm request ID từ context variable
        request_id = REQUEST_ID.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Thêm user ID cho audit logging
        user_id = USER_ID.get()
        if user_id:
            log_data["user_id"] = user_id
        
        # Thêm source information - nơi log được tạo
        # Giúp debug bằng cách biết chính xác file và line
        log_data["source"] = {
            "file": record.pathname,      # Absolute path của file
            "line": record.lineno,        # Line number trong file
            "function": record.funcName,  # Function name
            "module": record.module,      # Module name
        }
        
        # Thêm exception info nếu log được tạo với exception
        # record.exc_info chứa (type, value, traceback) tuple
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
            }
        
        # Thêm extra fields từ record
        # LogRecord có nhiều attributes mặc định, chỉ lấy những cái custom
        standard_attrs = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
            'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'getMessage'
        }
        
        # Lấy tất cả attributes không thuộc standard_attrs
        extra_fields = {}
        for attr, value in record.__dict__.items():
            if attr not in standard_attrs and not attr.startswith('_'):
                extra_fields[attr] = value
        
        # Chỉ thêm extra_fields nếu có dữ liệu
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Serialize log_data sang JSON string
        try:
            return self.encoder.encode(log_data)
        except Exception as e:
            # Fallback: Nếu JSON serialization thất bại
            # Return simple string để không crash ứng dụng
            return f'{{"timestamp": "{log_data["timestamp"]}", "level": "ERROR", "message": "Log serialization failed: {e}"}}'


# ============================================
# CORRELATION ID MANAGEMENT
# ============================================
def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID cho current async context
    
    Nếu không cung cấp correlation_id, tự động tạo UUID mới
    Correlation ID giúp trace một request qua toàn bộ hệ thống
    
    Args:
        correlation_id: ID để set (None = auto-generate UUID)
        
    Returns:
        Correlation ID đã được set (có thể là ID mới tạo)
        
    Example:
        >>> from src.core.logging import set_correlation_id
        >>> cid = set_correlation_id()
        >>> print(cid)
        '550e8400-e29b-41d4-a716-446655440000'
        
        >>> set_correlation_id("my-custom-id")
        'my-custom-id'
    """
    # Nếu không có correlation_id, tạo UUID mới
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    # Set context variable
    # ContextVar.set() trả về Token có thể dùng để reset sau này
    CORRELATION_ID.set(correlation_id)
    
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID của current async context
    
    Returns:
        Correlation ID hiện tại hoặc None nếu chưa được set
        
    Example:
        >>> from src.core.logging import get_correlation_id
        >>> cid = get_correlation_id()
        >>> print(cid)
        '550e8400-e29b-41d4-a716-446655440000'
    """
    return CORRELATION_ID.get()


def clear_correlation_id() -> None:
    """
    Clear correlation ID khỏi current async context
    
    Nên gọi sau khi request kết thúc để tránh leak sang request khác
    trong cùng một async worker
    
    Example:
        >>> from src.core.logging import clear_correlation_id
        >>> clear_correlation_id()
        >>> get_correlation_id()
        None
    """
    # Reset context variable về default (None)
    CORRELATION_ID.set(None)


# ============================================
# LOGGER SETUP
# ============================================
def setup_logging(
    level: str = "INFO",
    indent: Optional[int] = None,
    format_json: bool = True
) -> None:
    """
    Setup structured logging cho toàn bộ ứng dụng
    
    Cấu hình root logger để sử dụng structured JSON logging
    Thay thế default formatting với custom JSON formatter
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        indent: JSON indent spaces (None = compact, 2 = readable)
        format_json: True = JSON format, False = plain text
        
    Example:
        >>> from src.core.logging import setup_logging
        >>> setup_logging(level="DEBUG", indent=2)
        # Tất cả logs sau đây sẽ ở JSON format
        
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
        # Output: {"timestamp": "2026-05-09T05:27:00", "level": "INFO", ...}
    """
    # Lấy root logger
    # Root logger là ancestor của tất cả loggers khác
    root_logger = logging.getLogger()
    
    # Set log level
    # Chuyển string level sang numeric constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Xóa tất cả existing handlers để tránh duplicate logs
    # Mỗi handler có thể gây duplicate output nếu không xóa
    root_logger.handlers.clear()
    
    # Tạo stream handler ghi ra stdout
    # StreamHandler là simplest handler, ghi logs đến console
    console_handler = StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Set formatter cho handler
    if format_json:
        # Dùng structured JSON formatter
        formatter = StructuredLogFormatter(indent=indent)
    else:
        # Dùng plain text formatter cho development
        # Format: "2026-05-09 05:27:00,123 - INFO - module - message"
        formatter = Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    
    # Add handler vào root logger
    root_logger.addHandler(console_handler)
    
    # Log thông báo setup thành công
    root_logger.info(
        "Logging setup complete",
        extra={
            "level": level,
            "format": "json" if format_json else "text",
            "indent": indent,
        }
    )


# ============================================
# GET LOGGER
# ============================================
def get_logger(name: str) -> Logger:
    """
    Get logger instance với tên được chỉ định
    
    Wrapper function để lấy logger với tên đầy đủ
    Tự động thêm correlation ID vào tất cả logs
    
    Args:
        name: Tên của logger (thường là __name__ của module)
        
    Returns:
        Logger instance đã được cấu hình
        
    Example:
        >>> from src.core.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


# ============================================
# MODULE INITIALIZATION
# ============================================
# Setup logging mặc định khi module được import
# Đảm bảo logging luôn available ngay cả khi chưa gọi setup_logging()

# Chỉ setup nếu chưa có handlers (tránh duplicate setup)
if not logging.getLogger().handlers:
    setup_logging(
        level="INFO",      # Default level
        indent=None,       # Compact JSON cho production
        format_json=True,  # Structured logging
    )
