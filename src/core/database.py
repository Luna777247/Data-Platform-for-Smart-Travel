"""
Database Connection Module - MongoDB và Redis Connection Management
Module quản lý kết nối database cho Smart Tourism Data Platform
Theo thiết kế: SMART_TOURISM_DATA_PLATFORM_Architecture.md Section V - Database

Mục đích:
- Quản lý kết nối MongoDB với connection pooling
- Quản lý kết nối Redis cho caching
- Hỗ trợ async operations với Motor và aioredis
- Xử lý connection lifecycle (connect, reconnect, disconnect)
"""

# Import asyncio để hỗ trợ async database operations
import asyncio

# Import TypeVar để định nghĩa generic types
from typing import TypeVar, Optional, Any

# Import motor.motor_asyncio cho async MongoDB operations
# Motor là async driver cho MongoDB, thay thế pymongo trong async context
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Import redis.asyncio cho async Redis operations
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.connection import ConnectionPool as RedisConnectionPool

# Import logging từ module logging tự tạo
from src.core.logging import get_logger, get_correlation_id

# Import settings từ config module
from src.core.config import settings

# ============================================
# LOGGER SETUP
# ============================================
# Tạo logger cho database module
# Logger này sẽ log tất cả database operations với correlation ID
logger = get_logger(__name__)


# ============================================
# TYPE VARIABLES
# ============================================
# Định nghĩa type variables cho generic typing

# Type variable cho MongoDB client
MongoClientType = TypeVar("MongoClientType", bound=AsyncIOMotorClient)

# Type variable cho MongoDB database
MongoDatabaseType = TypeVar("MongoDatabaseType", bound=AsyncIOMotorDatabase)

# Type variable cho Redis client
RedisClientType = TypeVar("RedisClientType", bound=AsyncRedis)


# ============================================
# MONGODB CONNECTION MANAGER
# ============================================
class MongoDBManager:
    """
    Manager class cho MongoDB connections
    
    Quản lý lifecycle của MongoDB connection bao gồm:
    - Tạo connection với pooling
    - Reconnect tự động khi mất kết nối
    - Đóng connection gracefully khi shutdown
    - Cung cấp database instance cho các repositories
    
    Attributes:
        _client: Motor async client instance (singleton)
        _database: Database instance cho smart_travel
        _is_connected: Trạng thái kết nối hiện tại
        
    Example:
        >>> from src.core.database import mongodb_manager
        >>> await mongodb_manager.connect()
        >>> db = mongodb_manager.get_database()
        >>> await db.master_poi.find_one({"city": "tokyo"})
    """
    
    def __init__(self):
        """
        Khởi tạo MongoDBManager với default values
        
        Chưa tạo connection thực tế - chỉ khởi tạo attributes
        Connection thực sự được tạo khi gọi connect()
        """
        # Client instance - chưa khởi tạo
        self._client: Optional[AsyncIOMotorClient] = None
        
        # Database instance - chưa khởi tạo
        self._database: Optional[AsyncIOMotorDatabase] = None
        
        # Connection state tracking
        self._is_connected: bool = False
        
        # Server selection timeout (ms) - thời gian chờ tìm server
        self._server_selection_timeout_ms: int = 5000
        
        # Connection timeout (ms) - thời gian chờ kết nối
        self._connect_timeout_ms: int = 10000
        
        # Socket timeout (ms) - thời gian chờ socket operations
        self._socket_timeout_ms: int = 30000
    
    async def connect(self) -> None:
        """
        Thiết lập kết nối đến MongoDB
        
        Tạo Motor client với connection pooling và cấu hình tối ưu
        Nên gọi method này trong application startup event
        
        Raises:
            ConnectionError: Nếu không thể kết nối đến MongoDB
            
        Example:
            >>> await mongodb_manager.connect()
            >>> print(mongodb_manager.is_connected)
            True
        """
        # Kiểm tra đã kết nối chưa để tránh duplicate connections
        if self._is_connected and self._client:
            logger.warning("MongoDB already connected")
            return
        
        try:
            # Log bắt đầu kết nối với correlation ID
            cid = get_correlation_id()
            logger.info(
                "Connecting to MongoDB",
                extra={
                    "host": settings.mongodb_host,
                    "port": settings.mongodb_port,
                    "database": settings.mongodb_database,
                    "correlation_id": cid,
                }
            )
            
            # Lấy connection URL từ settings
            # URL đã được build trong config.py validate_security_configuration
            mongo_url = settings.mongodb_url
            
            # Kiểm tra URL có tồn tại không
            if not mongo_url:
                raise ValueError("MONGODB_URL is not configured")
            
            # Tạo Motor client với tối ưu cho production
            self._client = AsyncIOMotorClient(
                mongo_url,
                # Server selection timeout - thời gian chờ tìm server
                serverSelectionTimeoutMS=self._server_selection_timeout_ms,
                # Connection timeout - thời gian chờ kết nối
                connectTimeoutMS=self._connect_timeout_ms,
                # Socket timeout - thời gian chờ socket operations
                socketTimeoutMS=self._socket_timeout_ms,
                # Max pool size - số connections tối đa trong pool
                maxPoolSize=50,
                # Min pool size - số connections tối thiểu duy trì
                minPoolSize=10,
                # Max idle time - thời gian connection idle trước khi đóng
                maxIdleTimeMS=60000,
                # Wait queue timeout - thời gian chờ connection từ pool
                waitQueueTimeoutMS=5000,
                # Heartbeat frequency - tần suất kiểm tra server health
                heartbeatFrequencyMS=10000,
                # Retry writes - tự động retry khi write thất bại
                retryWrites=True,
                # Read preference - đọc từ primary replica set member
                readPreference="primary",
            )
            
            # Verify kết nối bằng cách ping server
            # server_info() trả về thông tin server, raise exception nếu fail
            server_info = await self._client.server_info()
            
            # Lấy database instance
            self._database = self._client[settings.mongodb_database]
            
            # Đánh dấu đã kết nối thành công
            self._is_connected = True
            
            # Log kết nối thành công với version info
            logger.info(
                "MongoDB connected successfully",
                extra={
                    "version": server_info.get("version"),
                    "host": settings.mongodb_host,
                    "database": settings.mongodb_database,
                    "correlation_id": cid,
                }
            )
            
        except Exception as e:
            # Log lỗi kết nối với chi tiết
            logger.error(
                f"Failed to connect to MongoDB: {e}",
                extra={
                    "host": settings.mongodb_host,
                    "port": settings.mongodb_port,
                    "error_type": type(e).__name__,
                    "correlation_id": get_correlation_id(),
                },
                exc_info=True
            )
            # Raise ConnectionError với context
            raise ConnectionError(f"MongoDB connection failed: {e}") from e
    
    async def disconnect(self) -> None:
        """
        Đóng kết nối MongoDB gracefully
        
        Nên gọi method này trong application shutdown event
        Đảm bảo tất cả pending operations hoàn thành trước khi đóng
        
        Example:
            >>> await mongodb_manager.disconnect()
            >>> print(mongodb_manager.is_connected)
            False
        """
        # Kiểm tra có client để đóng không
        if self._client:
            try:
                logger.info("Disconnecting from MongoDB")
                
                # Close client - đóng tất cả connections trong pool
                # close() là async operation trong Motor
                self._client.close()
                
                # Reset attributes
                self._client = None
                self._database = None
                self._is_connected = False
                
                logger.info("MongoDB disconnected successfully")
                
            except Exception as e:
                logger.error(
                    f"Error during MongoDB disconnect: {e}",
                    exc_info=True
                )
                # Không raise exception - cho phép shutdown tiếp tục
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Get MongoDB database instance
        
        Returns:
            AsyncIOMotorDatabase instance cho smart_travel database
            
        Raises:
            ConnectionError: Nếu chưa kết nối đến MongoDB
            
        Example:
            >>> db = mongodb_manager.get_database()
            >>> collection = db.master_poi
            >>> await collection.find_one({"city": "tokyo"})
        """
        # Kiểm tra đã kết nối chưa
        if not self._is_connected or not self._database:
            raise ConnectionError(
                "MongoDB not connected. Call connect() first."
            )
        
        return self._database
    
    def get_collection(self, collection_name: str) -> Any:
        """
        Get MongoDB collection instance
        
        Args:
            collection_name: Tên của collection cần lấy
            
        Returns:
            Collection instance từ database
            
        Raises:
            ConnectionError: Nếu chưa kết nối đến MongoDB
            
        Example:
            >>> collection = mongodb_manager.get_collection("master_poi")
            >>> await collection.find_one({"city": "tokyo"})
        """
        # Get database trước (sẽ raise nếu chưa connect)
        db = self.get_database()
        
        # Trả về collection
        return db[collection_name]
    
    @property
    def is_connected(self) -> bool:
        """
        Property để kiểm tra trạng thái kết nối
        
        Returns:
            True nếu đã kết nối, False nếu chưa
        """
        return self._is_connected
    
    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """
        Property để truy cập Motor client instance
        
        Returns:
            AsyncIOMotorClient instance hoặc None nếu chưa kết nối
            
        Warning:
            Nên dùng get_database() hoặc get_collection() thay vì truy cập
            client trực tiếp để đảm bảo error handling đúng
        """
        return self._client


# ============================================
# REDIS CONNECTION MANAGER
# ============================================
class RedisManager:
    """
    Manager class cho Redis connections
    
    Quản lý lifecycle của Redis connection bao gồm:
    - Tạo connection với connection pooling
    - Tự động reconnect khi mất kết nối
    - Cung cấp Redis client cho caching và real-time data
    
    Attributes:
        _client: Redis async client instance
        _pool: Connection pool cho Redis
        _is_connected: Trạng thái kết nối
        
    Example:
        >>> from src.core.database import redis_manager
        >>> await redis_manager.connect()
        >>> await redis_manager.client.set("key", "value")
        >>> value = await redis_manager.client.get("key")
    """
    
    def __init__(self):
        """
        Khởi tạo RedisManager với default values
        """
        # Client instance
        self._client: Optional[AsyncRedis] = None
        
        # Connection pool
        self._pool: Optional[RedisConnectionPool] = None
        
        # Connection state
        self._is_connected: bool = False
        
        # Connection timeout (seconds)
        self._socket_connect_timeout: float = 5.0
        
        # Socket timeout (seconds)
        self._socket_timeout: float = 10.0
    
    async def connect(self) -> None:
        """
        Thiết lập kết nối đến Redis
        
        Raises:
            ConnectionError: Nếu không thể kết nối đến Redis
            
        Example:
            >>> await redis_manager.connect()
            >>> print(redis_manager.is_connected)
            True
        """
        # Kiểm tra đã kết nối chưa
        if self._is_connected and self._client:
            logger.warning("Redis already connected")
            return
        
        try:
            # Log bắt đầu kết nối
            cid = get_correlation_id()
            logger.info(
                "Connecting to Redis",
                extra={
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "correlation_id": cid,
                }
            )
            
            # Parse Redis URL để lấy connection info
            redis_url = settings.redis_url
            
            if not redis_url:
                raise ValueError("REDIS_URL is not configured")
            
            # Tạo connection pool
            self._pool = RedisConnectionPool.from_url(
                redis_url,
                # Decode responses sang string thay vì bytes
                decode_responses=True,
                # Connection timeout
                socket_connect_timeout=self._socket_connect_timeout,
                # Socket timeout
                socket_timeout=self._socket_timeout,
                # Retry on timeout
                retry_on_timeout=True,
                # Health check interval
                health_check_interval=30,
                # Max connections trong pool
                max_connections=50,
            )
            
            # Tạo Redis client từ pool
            self._client = AsyncRedis(connection_pool=self._pool)
            
            # Verify kết nối bằng cách ping
            await self._client.ping()
            
            # Đánh dấu đã kết nối
            self._is_connected = True
            
            logger.info(
                "Redis connected successfully",
                extra={
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "correlation_id": cid,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to connect to Redis: {e}",
                extra={
                    "host": settings.redis_host,
                    "port": settings.redis_port,
                    "error_type": type(e).__name__,
                    "correlation_id": get_correlation_id(),
                },
                exc_info=True
            )
            raise ConnectionError(f"Redis connection failed: {e}") from e
    
    async def disconnect(self) -> None:
        """
        Đóng kết nối Redis gracefully
        
        Example:
            >>> await redis_manager.disconnect()
            >>> print(redis_manager.is_connected)
            False
        """
        if self._client:
            try:
                logger.info("Disconnecting from Redis")
                
                # Close client
                await self._client.close()
                
                # Reset attributes
                self._client = None
                self._pool = None
                self._is_connected = False
                
                logger.info("Redis disconnected successfully")
                
            except Exception as e:
                logger.error(
                    f"Error during Redis disconnect: {e}",
                    exc_info=True
                )
    
    @property
    def client(self) -> AsyncRedis:
        """
        Get Redis client instance
        
        Returns:
            AsyncRedis instance đã kết nối
            
        Raises:
            ConnectionError: Nếu chưa kết nối
            
        Example:
            >>> client = redis_manager.client
            >>> await client.set("key", "value", ex=3600)
        """
        if not self._is_connected or not self._client:
            raise ConnectionError(
                "Redis not connected. Call connect() first."
            )
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối"""
        return self._is_connected


# ============================================
# SINGLETON INSTANCES
# ============================================
# Tạo singleton instances cho toàn bộ ứng dụng
# Các modules khác import và dùng các instances này

# MongoDB manager singleton
mongodb_manager = MongoDBManager()

# Redis manager singleton
redis_manager = RedisManager()


# ============================================
# LIFECYCLE MANAGEMENT
# ============================================
async def connect_databases() -> None:
    """
    Connect tất cả databases trong một call
    
    Nên gọi trong application startup event
    
    Example:
        >>> from src.core.database import connect_databases
        >>> await connect_databases()
        # MongoDB và Redis đều đã kết nối
    """
    await mongodb_manager.connect()
    await redis_manager.connect()
    logger.info("All databases connected")


async def disconnect_databases() -> None:
    """
    Disconnect tất cả databases trong một call
    
    Nên gọi trong application shutdown event
    
    Example:
        >>> from src.core.database import disconnect_databases
        >>> await disconnect_databases()
        # MongoDB và Redis đều đã đóng
    """
    await mongodb_manager.disconnect()
    await redis_manager.disconnect()
    logger.info("All databases disconnected")
