"""
Pipeline Executor
=================

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/orchestration/executor.py

Execution engine cho pipelines với retry logic và error handling.

Features:
- Concurrent execution control
- Retry logic với exponential backoff
- Circuit breaker pattern
- Resource limits
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import functools
import time

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Trạng thái execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Kết quả của một execution."""
    task_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CircuitBreaker:
    """
    Circuit breaker pattern để tránh cascade failures.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failing fast, không gọi service
    - HALF_OPEN: Thử lại xem service đã recover chưa
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        async with breaker:
            result = await some_async_operation()
    """
    
    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> State:
        """Current state của circuit breaker."""
        if self._state == self.State.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = self.State.HALF_OPEN
        return self._state
    
    async def __aenter__(self):
        """Enter context manager."""
        current_state = self.state
        
        if current_state == self.State.OPEN:
            raise Exception(f"Circuit breaker is OPEN for {self.expected_exception}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - record success/failure."""
        async with self._lock:
            if exc_type is None:
                # Success
                if self._state == self.State.HALF_OPEN:
                    self._state = self.State.CLOSED
                    self._failure_count = 0
                    logger.info("Circuit breaker closed after successful test")
                return True
            
            # Failure
            if issubclass(exc_type, self.expected_exception):
                self._failure_count += 1
                self._last_failure_time = time.time()
                
                if self._failure_count >= self.failure_threshold:
                    self._state = self.State.OPEN
                    logger.warning(f"Circuit breaker opened after {self._failure_count} failures")
                
                return False  # Don't suppress the exception
            
            # Unexpected exception - don't count
            return False


class PipelineExecutor:
    """
    Executor cho pipeline tasks với retry và circuit breaker.
    
    Features:
    - Concurrent execution với semaphore
    - Exponential backoff retry
    - Circuit breaker cho external services
    - Resource tracking
    
    Usage:
        executor = PipelineExecutor(max_concurrent=5, max_retries=3)
        
        result = await executor.execute(
            task_id="collect_hanoi",
            func=collector.collect_city_data,
            city="hanoi"
        )
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        circuit_breaker_threshold: int = 5
    ):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._results: Dict[str, ExecutionResult] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._cb_threshold = circuit_breaker_threshold
        
        logger.info(f"PipelineExecutor initialized (max_concurrent={max_concurrent}, "
                   f"max_retries={max_retries})")
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker cho service."""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=self._cb_threshold,
                recovery_timeout=60
            )
        return self._circuit_breakers[service_name]
    
    async def execute(
        self,
        task_id: str,
        func: Callable,
        *args,
        use_circuit_breaker: bool = False,
        circuit_breaker_name: Optional[str] = None,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute một task với retry và circuit breaker.
        
        Args:
            task_id: Unique task ID
            func: Async function to execute
            args: Positional arguments cho func
            use_circuit_breaker: Enable circuit breaker
            circuit_breaker_name: Circuit breaker identifier
            kwargs: Keyword arguments cho func
            
        Returns:
            ExecutionResult với kết quả hoặc error
        """
        started_at = datetime.utcnow()
        retry_count = 0
        
        async with self._semaphore:
            while retry_count <= self.max_retries:
                try:
                    # Execute with circuit breaker if enabled
                    if use_circuit_breaker:
                        cb_name = circuit_breaker_name or task_id
                        breaker = self.get_circuit_breaker(cb_name)
                        
                        async with breaker:
                            result = await func(*args, **kwargs)
                    else:
                        result = await func(*args, **kwargs)
                    
                    # Success
                    completed_at = datetime.utcnow()
                    duration = (completed_at - started_at).total_seconds()
                    
                    exec_result = ExecutionResult(
                        task_id=task_id,
                        status=ExecutionStatus.SUCCESS,
                        started_at=started_at,
                        completed_at=completed_at,
                        result=result,
                        retry_count=retry_count,
                        duration_seconds=duration
                    )
                    
                    self._results[task_id] = exec_result
                    logger.info(f"Task {task_id} completed successfully "
                               f"(duration={duration:.2f}s, retries={retry_count})")
                    return exec_result
                    
                except Exception as e:
                    retry_count += 1
                    
                    if retry_count > self.max_retries:
                        # Max retries reached - fail
                        completed_at = datetime.utcnow()
                        duration = (completed_at - started_at).total_seconds()
                        
                        exec_result = ExecutionResult(
                            task_id=task_id,
                            status=ExecutionStatus.FAILED,
                            started_at=started_at,
                            completed_at=completed_at,
                            error=str(e),
                            retry_count=retry_count - 1,
                            duration_seconds=duration
                        )
                        
                        self._results[task_id] = exec_result
                        logger.error(f"Task {task_id} failed after {retry_count} retries: {e}")
                        return exec_result
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.base_delay * (2 ** (retry_count - 1)),
                        self.max_delay
                    )
                    
                    logger.warning(f"Task {task_id} failed (attempt {retry_count}), "
                                  f"retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
    
    async def execute_many(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: Optional[int] = None
    ) -> List[ExecutionResult]:
        """
        Execute nhiều tasks concurrently.
        
        Args:
            tasks: List of task dicts with keys: task_id, func, args, kwargs
            max_concurrent: Override concurrent limit
            
        Returns:
            List of ExecutionResult
        """
        semaphore = asyncio.Semaphore(
            max_concurrent or self.max_concurrent
        )
        
        async def run_task(task_def):
            async with semaphore:
                return await self.execute(
                    task_id=task_def["task_id"],
                    func=task_def["func"],
                    *task_def.get("args", []),
                    use_circuit_breaker=task_def.get("use_circuit_breaker", False),
                    circuit_breaker_name=task_def.get("circuit_breaker_name"),
                    **task_def.get("kwargs", {})
                )
        
        # Run all tasks concurrently
        results = await asyncio.gather(
            *[run_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_id = tasks[i]["task_id"]
                processed_results.append(ExecutionResult(
                    task_id=task_id,
                    status=ExecutionStatus.FAILED,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    error=str(result),
                    retry_count=self.max_retries
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_result(self, task_id: str) -> Optional[ExecutionResult]:
        """Lấy kết quả của một task."""
        return self._results.get(task_id)
    
    def get_all_results(
        self,
        status: Optional[ExecutionStatus] = None
    ) -> List[ExecutionResult]:
        """Lấy tất cả results, optionally filter by status."""
        results = list(self._results.values())
        if status:
            results = [r for r in results if r.status == status]
        return results
    
    def cleanup_old_results(self, max_age_hours: int = 24) -> int:
        """Xóa old execution results."""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(hours=max_age_hours)
        
        to_remove = [
            task_id for task_id, result in self._results.items()
            if result.completed_at and result.completed_at < cutoff
        ]
        
        for task_id in to_remove:
            del self._results[task_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old execution results")
        return len(to_remove)
    
    def get_circuit_breaker_status(self) -> Dict[str, str]:
        """Lấy status của tất cả circuit breakers."""
        return {
            name: breaker.state.value
            for name, breaker in self._circuit_breakers.items()
        }
