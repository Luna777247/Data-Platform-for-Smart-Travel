"""
Base Ingestion Class - Foundation cho tất cả data ingestion engines
===============================================================
Theo thiết kế: RECOMMENDED_STRUCTURE.md - pipelines/ingestion/ section

Mục đích:
- Định nghĩa interface chung cho tất cả ingestion engines
- Cung cấp common functionality (retry, logging, error handling)
- Hỗ trợ async operations với proper resource management
- Tích hợp với pipeline orchestration system

Design Pattern: Template Method Pattern
- Subclasses override specific methods (fetch_data, parse_response)
- Base class điều khiển overall flow (ingest → parse → validate → save)

Usage:
    class OSMIngestion(BaseIngestionEngine):
        async def fetch_data(self, city: str, category: str) -> Dict:
            # Implementation cụ thể cho OSM
            ...
"""

# Import ABC (Abstract Base Class) để định nghĩa abstract methods
from abc import ABC, abstractmethod

# Import asyncio cho async operations
import asyncio

# Import logging để ghi lại ingestion process
import logging

# Import datetime để timestamps
from datetime import datetime, timezone

# Import type hints
from typing import Dict, List, Any, Optional, Tuple

# Import aiohttp cho async HTTP requests
import aiohttp

# Import tenacity cho retry logic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Import Pydantic cho data validation
from pydantic import BaseModel, Field, ValidationError

# Import logging từ src.core
from src.core.logging import get_logger, get_correlation_id

# Import settings từ src.core
from src.core.config import settings


# ============================================
# LOGGER SETUP
# ============================================
logger = get_logger(__name__)


# ============================================
# DATA MODELS
# ============================================
class IngestionRecord(BaseModel):
    """
    Model đại diện cho một record đã được ingest
    
    Đây là standardized format cho tất cả ingested data,
    giúp downstream processors xử lý đồng nhất.
    """
    
    # Unique identifier cho record
    # Format: {source}_{source_id}_{timestamp}
    record_id: str = Field(..., description="ID unique của record")
    
    # Source của data
    source: str = Field(..., description="Nguồn data (osm, google_places, etc.)")
    
    # Raw data từ source (chưa xử lý)
    raw_data: Dict[str, Any] = Field(..., description="Raw data gốc")
    
    # Metadata về ingestion
    ingestion_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata về ingestion process"
    )
    
    # Thời điểm ingest
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Thời điểm ingest"
    )


class IngestionResult(BaseModel):
    """
    Model đại diện cho kết quả của một ingestion job
    
    Trả về sau khi hoàn thành ingestion cho một city/category.
    """
    
    # Success flag
    success: bool = Field(..., description="Ingestion thành công hay không")
    
    # Số records đã ingest
    records_count: int = Field(default=0, description="Số records đã ingest")
    
    # Danh sách records
    records: List[IngestionRecord] = Field(
        default_factory=list,
        description="Danh sách records đã ingest"
    )
    
    # Errors nếu có
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách errors nếu có"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata về ingestion job"
    )
    
    # Thời gian xử lý (giây)
    duration_seconds: float = Field(
        default=0.0,
        description="Thời gian xử lý (giây)"
    )


# ============================================
# BASE INGESTION ENGINE
# ============================================
class BaseIngestionEngine(ABC):
    """
    Abstract base class cho tất cả ingestion engines
    
    Cung cấp:
    - Common configuration loading
    - Retry logic với exponential backoff
    - Rate limiting
    - Error handling và logging
    - Resource management (HTTP sessions)
    
    Subclasses phải implement:
    - fetch_data(): Lấy data từ source
    - parse_response(): Parse raw response thành standardized format
    
    Example subclass:
        class OSMIngestion(BaseIngestionEngine):
            async def fetch_data(self, city: str, category: str) -> Dict:
                # Implement OSM-specific fetching
                pass
            
            def parse_response(self, raw_data: Dict) -> List[IngestionRecord]:
                # Parse OSM data format
                pass
    """
    
    def __init__(
        self,
        source_name: str,
        api_endpoint: str,
        rate_limit_rpm: int = 60,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        """
        Khởi tạo ingestion engine
        
        Args:
            source_name: Tên của data source (osm, google_places, etc.)
            api_endpoint: Base URL của API
            rate_limit_rpm: Rate limit (requests per minute)
            max_retries: Số lần retry tối đa
            timeout_seconds: Timeout cho mỗi request
        """
        # Source identifier
        self.source_name = source_name
        
        # API endpoint
        self.api_endpoint = api_endpoint
        
        # Rate limiting
        self.rate_limit_rpm = rate_limit_rpm
        
        # Calculate delay giữa các requests (seconds)
        # 60 seconds / rate_limit = minimum delay
        self.min_request_delay = 60.0 / rate_limit_rpm
        
        # Max retries
        self.max_retries = max_retries
        
        # Timeout
        self.timeout_seconds = timeout_seconds
        
        # HTTP session (sẽ được tạo khi cần)
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Semaphore để giới hạn concurrent requests
        # Giúp tuân thủ rate limit và tránh overwhelm server
        self._semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
        
        # Last request timestamp để tính delay
        self._last_request_time: Optional[datetime] = None
        
        # Logger cho instance này
        self._logger = get_logger(f"{__name__}.{source_name}")
        
        self._logger.info(
            f"Initialized {source_name} ingestion engine",
            extra={
                "source": source_name,
                "api_endpoint": api_endpoint,
                "rate_limit_rpm": rate_limit_rpm,
            }
        )
    
    async def __aenter__(self):
        """
        Async context manager entry
        
        Tạo HTTP session khi vào context
        """
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit
        
        Đóng HTTP session khi ra khỏi context
        """
        await self.close()
    
    async def _ensure_session(self) -> None:
        """
        Ensure HTTP session được tạo
        
        Tạo session nếu chưa có hoặc đã bị đóng
        """
        if self._session is None or self._session.closed:
            # Tạo TCP connector với limit để tránh quá nhiều connections
            connector = aiohttp.TCPConnector(
                limit=20,                    # Tổng connections
                limit_per_host=10,          # Connections mỗi host
                ttl_dns_cache=300,          # DNS cache TTL (5 phút)
                use_dns_cache=True,
            )
            
            # Timeout configuration
            timeout = aiohttp.ClientTimeout(
                total=self.timeout_seconds,
                connect=10,
                sock_read=self.timeout_seconds
            )
            
            # Create session
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"SmartTourismPlatform/1.0 ({self.source_name})",
                }
            )
            
            self._logger.debug("HTTP session created")
    
    async def close(self) -> None:
        """
        Đóng ingestion engine và cleanup resources
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._logger.debug("HTTP session closed")
    
    async def _rate_limit(self) -> None:
        """
        Rate limiting - đợi để tuân thủ requests per minute
        
        Tính toán delay dựa trên thời gian request cuối cùng
        và sleep nếu cần.
        """
        if self._last_request_time is not None:
            # Calculate elapsed time
            elapsed = (datetime.now(timezone.utc) - self._last_request_time).total_seconds()
            
            # Calculate required delay
            delay = self.min_request_delay - elapsed
            
            if delay > 0:
                self._logger.debug(f"Rate limiting: sleeping for {delay:.2f}s")
                await asyncio.sleep(delay)
        
        # Update last request time
        self._last_request_time = datetime.now(timezone.utc)
    
    @retry(
        # Retry tối đa 3 lần
        stop=stop_after_attempt(3),
        
        # Exponential backoff: 1s, 2s, 4s
        wait=wait_exponential(multiplier=1, min=1, max=10),
        
        # Chỉ retry khi gặp network/server errors
        retry=retry_if_exception_type((
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ConnectionError
        )),
        
        # Log trước khi retry
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request với retry logic và rate limiting
        
        Args:
            url: Request URL
            method: HTTP method (GET, POST, etc.)
            params: URL query parameters
            headers: Additional headers
            json_data: JSON body cho POST requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            aiohttp.ClientError: Nếu request thất bại sau retries
            asyncio.TimeoutError: Nếu timeout
        """
        # Ensure session exists
        await self._ensure_session()
        
        # Rate limiting
        await self._rate_limit()
        
        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # Log request
        self._logger.debug(
            f"Making {method} request to {url}",
            extra={
                "method": method,
                "url": url,
                "params": params,
            }
        )
        
        # Make request với semaphore để giới hạn concurrent
        async with self._semaphore:
            async with self._session.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                json=json_data
            ) as response:
                # Check status code
                response.raise_for_status()
                
                # Parse JSON response
                data = await response.json()
                
                self._logger.debug(
                    f"Request successful: {response.status}",
                    extra={"status": response.status}
                )
                
                return data
    
    @abstractmethod
    async def fetch_data(
        self,
        city: str,
        category: str
    ) -> Dict[str, Any]:
        """
        Abstract method: Fetch raw data từ source
        
        Subclasses PHẢI implement method này.
        
        Args:
            city: City identifier (e.g., "tokyo", "osaka")
            category: Category identifier (e.g., "restaurant", "hotel")
            
        Returns:
            Raw data từ source (format tùy thuộc source)
            
        Raises:
            NotImplementedError: Nếu subclass không implement
        """
        pass
    
    @abstractmethod
    def parse_response(
        self,
        raw_data: Dict[str, Any]
    ) -> List[IngestionRecord]:
        """
        Abstract method: Parse raw response thành standardized records
        
        Subclasses PHẢI implement method này.
        Chuyển đổi raw data từ source-specific format sang IngestionRecord.
        
        Args:
            raw_data: Raw data từ fetch_data()
            
        Returns:
            List của IngestionRecord objects
            
        Raises:
            NotImplementedError: Nếu subclass không implement
        """
        pass
    
    async def ingest(
        self,
        city: str,
        category: str
    ) -> IngestionResult:
        """
        Main ingestion method - orchestrate entire ingestion flow
        
        Template method pattern: điều khiển overall flow,
        subclasses chỉ cần implement specific steps.
        
        Flow:
        1. Validate inputs
        2. Fetch data từ source (abstract method)
        3. Parse response (abstract method)
        4. Validate records
        5. Return kết quả
        
        Args:
            city: City cần ingest
            category: Category cần ingest
            
        Returns:
            IngestionResult với records và metadata
        """
        start_time = datetime.now(timezone.utc)
        
        self._logger.info(
            f"Starting ingestion: {city}/{category}",
            extra={
                "city": city,
                "category": category,
                "source": self.source_name,
                "correlation_id": get_correlation_id(),
            }
        )
        
        try:
            # Step 1: Validate inputs
            if not city or not category:
                raise ValueError("City và category không được để trống")
            
            # Step 2: Fetch data từ source
            # Method này được implement bởi subclass
            raw_data = await self.fetch_data(city, category)
            
            self._logger.debug(
                f"Fetched raw data",
                extra={
                    "data_size": len(str(raw_data)),
                    "has_data": bool(raw_data)
                }
            )
            
            # Step 3: Parse response
            # Method này được implement bởi subclass
            records = self.parse_response(raw_data)
            
            self._logger.info(
                f"Parsed {len(records)} records",
                extra={"records_count": len(records)}
            )
            
            # Step 4: Validate records (Pydantic validation đã xảy ra trong parse_response)
            
            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Step 5: Return kết quả
            result = IngestionResult(
                success=True,
                records_count=len(records),
                records=records,
                metadata={
                    "city": city,
                    "category": category,
                    "source": self.source_name,
                    "duration_seconds": duration,
                },
                duration_seconds=duration
            )
            
            self._logger.info(
                f"Ingestion completed successfully: {len(records)} records in {duration:.2f}s",
                extra={
                    "success": True,
                    "records_count": len(records),
                    "duration_seconds": duration,
                }
            )
            
            return result
            
        except Exception as e:
            # Calculate duration even for failed attempts
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            self._logger.error(
                f"Ingestion failed: {e}",
                extra={
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration_seconds": duration,
                },
                exc_info=True
            )
            
            return IngestionResult(
                success=False,
                records_count=0,
                records=[],
                errors=[{
                    "error": str(e),
                    "type": type(e).__name__,
                    "city": city,
                    "category": category,
                }],
                metadata={
                    "city": city,
                    "category": category,
                    "source": self.source_name,
                    "duration_seconds": duration,
                },
                duration_seconds=duration
            )
    
    async def ingest_batch(
        self,
        cities: List[str],
        categories: List[str]
    ) -> List[IngestionResult]:
        """
        Ingest nhiều city/category combinations
        
        Chạy concurrent ingestion cho tất cả combinations,
        nhưng vẫn tuân thủ rate limits.
        
        Args:
            cities: Danh sách cities
            categories: Danh sách categories
            
        Returns:
            List của IngestionResult cho mỗi combination
        """
        self._logger.info(
            f"Starting batch ingestion: {len(cities)} cities x {len(categories)} categories",
            extra={
                "cities_count": len(cities),
                "categories_count": len(categories),
                "total_jobs": len(cities) * len(categories),
            }
        )
        
        # Tạo list của tất cả combinations
        tasks = []
        for city in cities:
            for category in categories:
                task = self.ingest(city, category)
                tasks.append(task)
        
        # Chạy tất cả tasks concurrently
        # Semaphore trong _make_request sẽ giới hạn concurrent requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Xử lý exceptions (nếu có)
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception thành failed IngestionResult
                city = cities[i // len(categories)]
                category = categories[i % len(categories)]
                processed_results.append(IngestionResult(
                    success=False,
                    records_count=0,
                    errors=[{
                        "error": str(result),
                        "type": type(result).__name__,
                        "city": city,
                        "category": category,
                    }]
                ))
            else:
                processed_results.append(result)
        
        # Log summary
        success_count = sum(1 for r in processed_results if r.success)
        total_records = sum(r.records_count for r in processed_results)
        
        self._logger.info(
            f"Batch ingestion completed: {success_count}/{len(processed_results)} successful, "
            f"{total_records} total records",
            extra={
                "successful_jobs": success_count,
                "failed_jobs": len(processed_results) - success_count,
                "total_records": total_records,
            }
        )
        
        return processed_results


# ============================================
# UTILITY FUNCTIONS
# ============================================
def create_ingestion_engine(
    source_type: str,
    **kwargs
) -> BaseIngestionEngine:
    """
    Factory function để tạo ingestion engine theo source type
    
    Args:
        source_type: Loại source (osm, google_places, tripadvisor)
        **kwargs: Additional arguments cho engine
        
    Returns:
        BaseIngestionEngine instance
        
    Raises:
        ValueError: Nếu source_type không được hỗ trợ
    """
    # Import specific engines (để tránh circular imports)
    if source_type == "osm":
        from .osm_ingestion import OSMIngestionEngine
        return OSMIngestionEngine(**kwargs)
    elif source_type == "google_places":
        # from .google_ingestion import GoogleIngestionEngine
        # return GoogleIngestionEngine(**kwargs)
        raise NotImplementedError("Google Places ingestion chưa được implement")
    elif source_type == "tripadvisor":
        # from .tripadvisor_ingestion import TripAdvisorIngestionEngine
        # return TripAdvisorIngestionEngine(**kwargs)
        raise NotImplementedError("TripAdvisor ingestion chưa được implement")
    else:
        raise ValueError(f"Unknown source type: {source_type}")


# ============================================
# MODULE EXPORTS
# ============================================
__all__ = [
    "BaseIngestionEngine",
    "IngestionRecord",
    "IngestionResult",
    "create_ingestion_engine",
]
