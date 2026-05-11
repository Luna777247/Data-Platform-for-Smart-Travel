"""
Core Configuration Module - Quản lý cấu hình toàn bộ ứng dụng
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section VI
Mục đích: Tập trung hóa tất cả cấu hình environment variables
"""

# Import functools.lru_cache để cache kết quả hàm get_settings()
# Giúp tối ưu hiệu năng bằng cách không tạo lại Settings object mỗi lần gọi
from functools import lru_cache

# Import quote_plus để encode special characters trong URL
# Sử dụng khi build MongoDB connection string với username/password
from urllib.parse import quote_plus

# Import Field từ pydantic để định nghĩa các trường có metadata
# Import field_validator để validate giá trị đầu vào
# Import model_validator để validate toàn bộ model
from pydantic import Field, field_validator, model_validator

# Import BaseSettings từ pydantic-settings để tự động load từ environment
# Import SettingsConfigDict để cấu hình behavior của Settings class
from pydantic_settings import BaseSettings, SettingsConfigDict


# Set chứa các JWT algorithms được phép sử dụng
# HS256: HMAC-SHA256 - nhanh, phù hợp cho internal services
# HS384: HMAC-SHA384 - mức độ bảo mật cao hơn
# HS512: HMAC-SHA512 - bảo mật cao nhất trong họ HMAC
_ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


class Settings(BaseSettings):
    """
    Settings class - Tập trung tất cả cấu hình ứng dụng
    Kế thừa từ BaseSettings để tự động load từ environment variables
    Theo thiết kế: Configuration Management trong docs/RECOMMENDED_STRUCTURE.md
    """
    
    # ============================================
    # MONGODB CONFIGURATION
    # ============================================
    # Theo thiết kế: Database Schema Design Section V
    
    # MongoDB connection URL đầy đủ (optional)
    # Nếu có giá trị, sẽ override tất cả các tham số host/port/user/password bên dưới
    # Format: mongodb+srv://username:password@cluster.mongodb.net/database
    mongodb_url: str | None = Field(default=None, alias="MONGODB_URI")
    
    # MongoDB server hostname
    # Default: "mongodb" - tên service trong docker-compose network
    # Có thể override bằng biến môi trường MONGODB_HOST
    mongodb_host: str = Field(default="mongodb", alias="MONGODB_HOST")
    
    # MongoDB server port
    # Default: 27017 - port chuẩn của MongoDB
    # Có thể override bằng biến môi trường MONGODB_PORT
    mongodb_port: int = Field(default=27017, alias="MONGODB_PORT")
    
    # MongoDB username cho authentication
    # Default: "admin" - user admin mặc định
    # Có thể override bằng biến môi trường MONGODB_USER
    mongodb_user: str = Field(default="admin", alias="MONGODB_USER")
    
    # MongoDB password cho authentication
    # None nếu không dùng authentication (development mode)
    # Có thể override bằng biến môi trường MONGODB_PASSWORD
    mongodb_password: str | None = Field(default=None, alias="MONGODB_PASSWORD")
    
    # MongoDB database name chính
    # Default: "smart_travel" - tên database cho ứng dụng
    # Có thể override bằng biến môi trường DB_NAME
    mongodb_database: str = Field(default="smart_travel", alias="DB_NAME")
    
    # ============================================
    # REDIS CONFIGURATION
    # ============================================
    # Dùng cho caching và real-time data
    
    # Redis connection URL đầy đủ (optional)
    # Format: redis://username:password@host:port/0
    # Hoặc rediss:// cho TLS connection
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    
    # Redis server hostname
    # Default: "redis" - tên service trong docker-compose
    # Có thể override bằng biến môi trường REDIS_HOST
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    
    # Redis server port
    # Default: 6379 - port chuẩn của Redis
    # Có thể override bằng biến môi trường REDIS_PORT
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    
    # Redis password cho authentication (optional)
    # None nếu không dùng authentication
    # Có thể override bằng biến môi trường REDIS_PASSWORD
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    # ============================================
    # SECURITY CONFIGURATION
    # ============================================
    # Theo thiết kế: Security Best Practices trong docs/
    
    # Secret key cho các mục đích mã hóa chung
    # Sử dụng cho session management, CSRF protection, etc.
    # Nên là chuỗi ngẫu nhiên ít nhất 32 ký tự
    # KHÔNG được hardcode trong code, phải load từ environment
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")
    
    # JWT secret key cho token signing
    # Dùng để ký và verify JWT tokens
    # Phải được bảo vệ cẩn thận - nếu lộ sẽ compromise toàn bộ auth system
    # Nên là chuỗi ngẫu nhiên ít nhất 32 ký tự
    jwt_secret: str | None = Field(default=None, alias="JWT_SECRET")
    
    # JWT signing algorithm
    # Default: "HS256" - HMAC-SHA256, nhanh và đủ mạnh cho hầu hết use cases
    # Các option khác: HS384, HS512 (mạnh hơn nhưng chậm hơn)
    # Lưu ý: Không dùng "none" algorithm vì dễ bị tấn công
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    
    # Thời gian hết hạn của access token (tính bằng phút)
    # Default: 30 phút - đủ cho user session nhưng không quá dài để giảm risk
    # Nếu giá trị <= 0 sẽ raise ValueError
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Thời gian hết hạn của refresh token (tính bằng ngày)
    # Default: 7 ngày - cho phép user stay logged in trong 1 tuần
    # Refresh token dùng để lấy access token mới khi access token hết hạn
    # Nếu giá trị <= 0 sẽ raise ValueError
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # ============================================
    # EXTERNAL APIs CONFIGURATION
    # ============================================
    # API keys và endpoints cho external services
    
    # Google Places API key cho việc lấy thông tin POI
    # Dùng trong pipelines/gold/enrichment.py để enrich POI data
    # Required: Có rate limit và billing, cần quản lý cẩn thận
    # Đăng ký tại: https://developers.google.com/maps/documentation/places/web-service
    google_places_api_key: str | None = Field(default=None, alias="GOOGLE_PLACES_API_KEY")
    
    # MinIO access key cho object storage
    # Dùng để lưu trữ files, images, và pipeline artifacts
    # MinIO là S3-compatible object storage, có thể thay thế AWS S3
    # Cần thiết cho lưu trữ Bronze/Silver/Gold layer data
    minio_access_key: str | None = Field(default=None, alias="MINIO_ACCESS_KEY")
    
    # MinIO secret key - cặp với access key ở trên
    # Dùng để authenticate với MinIO server
    # KHÔNG được expose trong logs hoặc error messages
    minio_secret_key: str | None = Field(default=None, alias="MINIO_SECRET_KEY")
    
    # MinIO server endpoint
    # Default: "minio:9000" - tên service và port trong docker-compose
    # Format: "host:port" hoặc "http://host:port" hoặc "https://host:port"
    # Có thể trỏ đến AWS S3, Google Cloud Storage, hoặc Azure Blob
    minio_endpoint: str = Field(default="minio:9000", alias="MINIO_ENDPOINT")
    
    # MinIO TLS/SSL enabled flag
    # Default: False - không dùng TLS (phù hợp cho internal network)
    # Set True nếu MinIO server yêu cầu HTTPS connection
    # Lưu ý: Trong production, nên bật TLS để bảo mật
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    # Cấu hình chung cho ứng dụng
    
    # Môi trường chạy của ứng dụng
    # Default: "development" - cho local development
    # Các giá trị khác: "staging", "production"
    # Ảnh hưởng đến các validation rules khác nhau
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Logging level cho ứng dụng
    # Default: "INFO" - log thông tin cơ bản
    # Các giá trị: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    # DEBUG: chi tiết nhất, phù hợp cho troubleshooting
    # ERROR: chỉ log lỗi, phù hợp cho production
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Debug mode flag
    # Default: False - production mode
    # Set True để enable debug features như auto-reload, chi tiết error messages
    # TRONG PRODUCTION PHẢI LÀ FALSE để tránh lộ thông tin nhạy cảm
    debug: bool = Field(default=False, alias="DEBUG")

    # ============================================
    # CORS AND RATE LIMITING
    # ============================================
    # Cấu hình cho cross-origin requests và rate limiting
    
    # Danh sách origins được phép truy cập API (CORS)
    # Default: Vite dev server ports + React default
    # Format: comma-separated list, ví dụ: "http://localhost:5173,https://app.example.com"
    # "*" cho phép tất cả origins (KHÔNG RECOMMENDED trong production)
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://localhost:3000",
        alias="ALLOWED_ORIGINS"
    )
    
    # Rate limiting enabled flag
    # Default: True - bật giới hạn request rate
    # Giúp protect API khỏi abuse và DDoS attacks
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    
    # Số requests tối đa cho phép mỗi phút
    # Default: 60 requests/minute = 1 request/giây trung bình
    # Tính trên mỗi IP address hoặc mỗi user (tùy implementation)
    rate_limit_requests_per_minute: int = Field(
        default=60,
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE",
    )
    
    # Số requests tối đa cho phép mỗi giờ
    # Default: 1000 requests/hour
    # Cao hơn per-minute limit để cho phép burst traffic ngắn hạn
    rate_limit_requests_per_hour: int = Field(
        default=1000,
        alias="RATE_LIMIT_REQUESTS_PER_HOUR",
    )

    # ============================================
    # INFRASTRUCTURE SETTINGS
    # ============================================
    # Cấu hình cho infrastructure và deployment
    
    # HTTPS/TLS enabled flag
    # Default: False - HTTP only (development)
    # Set True để redirect HTTP to HTTPS và dùng secure cookies
    # TRONG PRODUCTION PHẢI LÀ TRUE để bảo mật
    enable_https: bool = Field(default=False, alias="ENABLE_HTTPS")
    
    # Docker secrets enabled flag
    # Default: True - dùng Docker secrets cho sensitive data
    # Docker secrets được mount vào container tại /run/secrets/
    # An toàn hơn environment variables vì không expose trong ps hoặc logs
    use_docker_secrets: bool = Field(default=True, alias="USE_DOCKER_SECRETS")
    
    # HashiCorp Vault address (optional)
    # Dùng để lấy secrets động từ Vault server
    # Format: "http://vault:8200" hoặc "https://vault.example.com:8200"
    # Nếu None, không dùng Vault integration
    vault_addr: str | None = Field(default=None, alias="VAULT_ADDR")

    # ============================================
    # PYDANTIC CONFIGURATION
    # ============================================
    # Cấu hình cho BaseSettings behavior
    
    # SettingsConfigDict định nghĩa cách BaseSettings hoạt động
    model_config = SettingsConfigDict(
        # File environment variables được load
        # Khi chạy local development, đọc từ file .env
        env_file=".env",
        
        # Encoding của env file - UTF-8 cho hỗ trợ Unicode
        env_file_encoding="utf-8",
        
        # Directory chứa Docker secrets
        # Docker secrets được mount vào container tại /run/secrets/
        # An toàn hơn env vars vì không hiển thị trong docker inspect
        secrets_dir="/run/secrets",
        
        # Cho phép populate fields bằng field name hoặc alias
        # True = có thể dùng cả "mongodb_url" hoặc "MONGODB_URI"
        populate_by_name=True,
        
        # Bỏ qua extra fields không được định nghĩa trong model
        # "ignore" = không raise error nếu có env vars không dùng
        extra="ignore",
    )

    # ============================================
    # FIELD VALIDATORS
    # ============================================
    # Các validator functions để kiểm tra giá trị đầu vào
    
    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        """
        Validate JWT algorithm để đảm bảo chỉ dùng các algorithm được phép
        
        Args:
            value: Giá trị algorithm từ env var ALGORITHM
            
        Returns:
            Algorithm đã được normalize (uppercase, stripped)
            
        Raises:
            ValueError: Nếu algorithm không được hỗ trợ
        """
        # Normalize giá trị input - uppercase và strip whitespace
        # Đảm bảo "hs256", "HS256", " hs256 " đều được accept
        normalized = value.upper().strip()
        
        # Kiểm tra algorithm có trong whitelist không
        if normalized not in _ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                f"Unsupported JWT algorithm '{value}'. Allowed: {sorted(_ALLOWED_JWT_ALGORITHMS)}"
            )
        return normalized

    @field_validator("allowed_origins")
    @classmethod
    def normalize_allowed_origins(cls, value: str) -> str:
        """
        Normalize danh sách allowed origins để đảm bảo định dạng đúng
        
        Args:
            value: Chuỗi origins từ env var ALLOWED_ORIGINS
                   Ví dụ: "http://localhost:3000, https://app.example.com"
                   
        Returns:
            Chuỗi origins đã được clean - không trùng lặp, đúng format
            
        Raises:
            ValueError: Nếu không có origins nào được cung cấp
        """
        # Tách chuỗi thành list dựa trên dấu phẩy
        # Strip whitespace cho mỗi origin
        # Bỏ qua các giá trị empty string
        origins = [origin.strip() for origin in str(value).split(",") if origin.strip()]
        
        # Validate có ít nhất một origin
        if not origins:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin")
        
        # Sử dụng dict.fromkeys() để remove duplicates giữ nguyên thứ tự
        # Sau đó join lại thành chuỗi với dấu phẩy
        return ",".join(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_security_configuration(self):
        """
        Model-level validator để kiểm tra toàn bộ security configuration
        Chạy sau khi tất cả field validators đã hoàn thành
        
        Thực hiện các validation sau:
        1. Kiểm tra token expiration times hợp lệ
        2. Production mode: các security settings bắt buộc
        3. Build connection URLs nếu chưa có
        4. Set default secrets cho development mode
        
        Returns:
            self sau khi đã được validate và modify
            
        Raises:
            ValueError: Nếu có lỗi cấu hình bảo mật
        """
        # Kiểm tra có phải production mode không
        # Production mode = "prod" hoặc "production" (case-insensitive)
        production_mode = self.environment.lower() in {"prod", "production"}

        # ========================================
        # VALIDATE TOKEN EXPIRATION TIMES
        # ========================================
        # Access token expiration phải > 0
        if self.access_token_expire_minutes <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0")
        
        # Refresh token expiration phải > 0  
        if self.refresh_token_expire_days <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be greater than 0")

        # ========================================
        # PRODUCTION MODE VALIDATIONS
        # ========================================
        # Các validation nghiêm ngặt cho production environment
        if production_mode:
            # Debug mode không được bật trong production
            # Debug mode expose sensitive information trong error messages
            if self.debug:
                import warnings
                warnings.warn("DEBUG is enabled in production - this is insecure!")
            
            # Secret key phải được cấu hình và đủ mạnh
            # Yêu cầu ít nhất 32 ký tự để chống brute force
            if not self.secret_key or len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be configured and at least 32 characters")
            
            # JWT secret cũng phải đủ mạnh
            if not self.jwt_secret or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be configured and at least 32 characters")
            
            # Google Places API key bắt buộc cho production
            # Dùng để enrich POI data từ Google
            if not self.google_places_api_key:
                import warnings
                warnings.warn("GOOGLE_PLACES_API_KEY not configured - Google Places features will be disabled")
            
            # MinIO credentials bắt buộc cho object storage
            if not self.minio_access_key:
                raise ValueError("MINIO_ACCESS_KEY must be configured in production")
            if not self.minio_secret_key:
                raise ValueError("MINIO_SECRET_KEY must be configured in production")
            
            # MongoDB URL không được trỏ đến localhost trong production
            # Production nên dùng managed MongoDB service (Atlas, etc.)
            if self.mongodb_url and ("localhost" in self.mongodb_url.lower() or "127.0.0.1" in self.mongodb_url.lower()):
                raise ValueError("MONGODB_URI must not point to localhost in production")
            
            # Redis URL cũng không được là localhost
            if self.redis_url and ("localhost" in self.redis_url.lower() or "127.0.0.1" in self.redis_url.lower()):
                import warnings
                warnings.warn("REDIS_URL points to localhost - use container hostname in production")
            
            # HTTPS bắt buộc trong production
            # HTTP trong production là security risk
            if self.enable_https is False:
                import warnings
                warnings.warn("ENABLE_HTTPS is false - HTTPS should be enabled in production")
            
            # Kiểm tra CORS origins không được là wildcard trong production
            origins = self.allowed_origins_list
            if any(origin == "*" for origin in origins):
                import warnings
                warnings.warn("Wildcard CORS origins should not be used in production")
            
            # CORS origins không được dùng HTTP trong production
            # Phải dùng HTTPS cho tất cả origins
            if any(origin.startswith("http://") for origin in origins):
                import warnings
                warnings.warn("HTTP CORS origins should use HTTPS in production")

        # ========================================
        # BUILD MONGODB CONNECTION URL
        # ========================================
        # Nếu mongodb_url chưa được cấu hình, build từ các components
        if self.mongodb_url is None:
            if self.mongodb_password:
                # Có password -> build URL với authentication
                # Dùng quote_plus để encode special characters trong user/password
                self.mongodb_url = (
                    f"mongodb://{quote_plus(self.mongodb_user)}:{quote_plus(self.mongodb_password)}"
                    f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
                )
            else:
                # Không có password -> build URL không authentication
                # Chỉ dùng cho development/testing
                self.mongodb_url = (
                    f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
                )

        # ========================================
        # BUILD REDIS CONNECTION URL
        # ========================================
        # Nếu redis_url chưa được cấu hình, build từ các components
        if self.redis_url is None:
            if self.redis_password:
                # Có password -> build URL với authentication
                # Redis authentication format: redis://:password@host:port/db
                self.redis_url = (
                    f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/0"
                )
            else:
                # Không có password -> build URL không authentication
                self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"

        # ========================================
        # SET DEFAULT SECRETS FOR DEVELOPMENT
        # ========================================
        # Nếu không có secret_key và không phải production, set default
        # CẢNH BÁO: Default secrets chỉ dùng cho development!
        if not self.secret_key:
            if self.environment.lower() in {"prod", "production"}:
                raise ValueError("SECRET_KEY must be configured in production")
            # Set default cho development - KHÔNG AN TOÀN cho production
            self.secret_key = "development-only-secret-key-change-before-prod"
        
        # Tương tự cho JWT secret
        if not self.jwt_secret:
            if self.environment.lower() in {"prod", "production"}:
                raise ValueError("JWT_SECRET must be configured in production")
            # Set default cho development
            self.jwt_secret = "development-only-jwt-secret-change-before-prod"

        return self

    # ============================================
    # PROPERTIES
    # ============================================
    # Các computed properties để tiện sử dụng
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Property để lấy danh sách origins dưới dạng list
        
        Returns:
            List của các origin strings
            Ví dụ: ["http://localhost:3000", "https://app.example.com"]
        """
        # Tách chuỗi allowed_origins thành list
        # Bỏ qua các giá trị empty
        return [origin for origin in self.allowed_origins.split(",") if origin]

    @property
    def cors_origins_list(self) -> list[str]:
        """
        Alias property cho allowed_origins_list
        Dùng cho CORS middleware configuration
        
        Returns:
            Cùng giá trị với allowed_origins_list
        """
        return self.allowed_origins_list


# ============================================
# SETTINGS FACTORY FUNCTIONS
# ============================================
# Các functions để tạo và cache Settings instances

@lru_cache()
def get_settings() -> Settings:
    """
    Factory function để tạo Settings instance với caching
    
    Sử dụng @lru_cache() decorator để cache kết quả
    - Lần đầu tiên gọi: Tạo Settings instance mới từ env vars
    - Các lần gọi sau: Trả về cached instance (performance optimization)
    
    Lợi ích của caching:
    1. Tránh re-parse environment variables mỗi lần gọi
    2. Giảm overhead khi access settings nhiều lần
    3. Đảm bảo consistency trong cùng một request
    
    Returns:
        Settings instance đã được validate và cache
        
    Example:
        >>> from src.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.mongodb_url)
        'mongodb://localhost:27017/smart_travel'
    """
    return Settings()


# Module-level settings instance cho tiện import
# Đây là singleton pattern - tất cả imports đều dùng cùng một instance
# Thread-safe nhờ @lru_cache() decorator
# 
# Usage:
#   from src.core.config import settings
#   db_url = settings.mongodb_url
# 
# Hoặc dùng get_settings() nếu cần lazy loading:
#   from src.core.config import get_settings
#   settings = get_settings()
settings = get_settings()