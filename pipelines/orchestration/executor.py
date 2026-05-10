"""
Pipeline Executor
=================

Pipeline execution engine cho Smart Tourism Platform.
Theo RECOMMENDED_STRUCTURE.md - pipelines/orchestration/executor.py
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result của pipeline execution."""
    execution_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PipelineExecutor:
    """
    Execute pipeline stages với error handling và retry logic.
    
    Features:
    - Concurrent execution
    - Retry with exponential backoff
    - Circuit breaker pattern
    - Execution tracking
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        max_concurrent: int = 5,
        enable_circuit_breaker: bool = True
    ):
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent
        self.enable_circuit_breaker = enable_circuit_breaker
        
        self.executions: Dict[str, ExecutionResult] = {}
        self.circuit_states: Dict[str, str] = {}
        self.failure_counts: Dict[str, int] = {}
        
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info(
            f"PipelineExecutor initialized (retries={max_retries}, "
            f"concurrent={max_concurrent})"
        )
    
    async def execute_stage(
        self,
        stage_name: str,
        processor: Callable,
        data: Any,
        city: str,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute một pipeline stage.
        
        Args:
            stage_name: Name of the stage (bronze, silver, gold)
            processor: Processing function
            data: Input data
            city: Target city
            **kwargs: Additional arguments cho processor
            
        Returns:
            ExecutionResult
        """
        execution_id = f"{stage_name}_{city}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            start_time=datetime.utcnow()
        )
        
        self.executions[execution_id] = result
        
        # Check circuit breaker
        if self.enable_circuit_breaker:
            if not self._can_execute(stage_name):
                result.status = ExecutionStatus.FAILED
                result.error_message = f"Circuit breaker open for {stage_name}"
                return result
        
        async with self.semaphore:
            result.status = ExecutionStatus.RUNNING
            
            try:
                # Execute with retry logic
                output_data = await self._execute_with_retry(
                    processor, data, city, **kwargs
                )
                
                # Success
                result.status = ExecutionStatus.COMPLETED
                result.end_time = datetime.utcnow()
                
                # Count records if available
                if isinstance(output_data, list):
                    result.records_processed = len(output_data)
                elif isinstance(output_data, dict):
                    result.records_processed = output_data.get("count", 1)
                
                # Reset circuit breaker on success
                if self.enable_circuit_breaker:
                    self._record_success(stage_name)
                
                logger.info(
                    f"Stage {stage_name} completed: "
                    f"{result.records_processed} records"
                )
                
            except Exception as e:
                result.status = ExecutionStatus.FAILED
                result.end_time = datetime.utcnow()
                result.error_message = str(e)
                result.records_failed = len(data) if isinstance(data, list) else 1
                
                # Record failure for circuit breaker
                if self.enable_circuit_breaker:
                    self._record_failure(stage_name)
                
                logger.error(f"Stage {stage_name} failed: {e}")
        
        return result
    
    async def execute_pipeline(
        self,
        city: str,
        bronze_processor: Callable,
        silver_processor: Optional[Callable] = None,
        gold_processor: Optional[Callable] = None,
        raw_data: Any = None
    ) -> Dict[str, ExecutionResult]:
        """
        Execute full pipeline: bronze -> silver -> gold.
        
        Args:
            city: Target city
            bronze_processor: Bronze stage processor
            silver_processor: Silver stage processor (optional)
            gold_processor: Gold stage processor (optional)
            raw_data: Input data cho bronze
            
        Returns:
            Dict of stage -> ExecutionResult
        """
        results = {}
        
        # Bronze stage
        bronze_result = await self.execute_stage(
            "bronze", bronze_processor, raw_data, city
        )
        results["bronze"] = bronze_result
        
        if bronze_result.status != ExecutionStatus.COMPLETED:
            logger.error("Bronze stage failed, stopping pipeline")
            return results
        
        # Silver stage (if processor provided)
        if silver_processor:
            silver_data = bronze_result.metadata.get("output_data", [])
            silver_result = await self.execute_stage(
                "silver", silver_processor, silver_data, city
            )
            results["silver"] = silver_result
            
            if silver_result.status != ExecutionStatus.COMPLETED:
                logger.error("Silver stage failed, stopping pipeline")
                return results
        
        # Gold stage (if processor provided)
        if gold_processor and silver_processor:
            silver_data = results["silver"].metadata.get("output_data", [])
            gold_result = await self.execute_stage(
                "gold", gold_processor, silver_data, city
            )
            results["gold"] = gold_result
        
        return results
    
    async def _execute_with_retry(
        self,
        processor: Callable,
        data: Any,
        city: str,
        **kwargs
    ) -> Any:
        """Execute processor với retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Try to execute
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(data, city, **kwargs)
                else:
                    result = processor(data, city, **kwargs)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate backoff delay
                    delay = min(2 ** attempt, 30)  # Max 30s
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
        
        # All retries exhausted
        raise last_exception
    
    def _can_execute(self, stage_name: str) -> bool:
        """Check if circuit breaker allows execution."""
        state = self.circuit_states.get(stage_name, "closed")
        
        if state == "open":
            return False
        
        return True
    
    def _record_failure(self, stage_name: str):
        """Record failure cho circuit breaker."""
        self.failure_counts[stage_name] = self.failure_counts.get(stage_name, 0) + 1
        
        # Open circuit after 5 failures
        if self.failure_counts[stage_name] >= 5:
            self.circuit_states[stage_name] = "open"
            logger.warning(f"Circuit breaker opened for {stage_name}")
    
    def _record_success(self, stage_name: str):
        """Record success cho circuit breaker."""
        self.failure_counts[stage_name] = 0
        self.circuit_states[stage_name] = "closed"
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get status của một execution."""
        return self.executions.get(execution_id)
    
    def get_all_executions(
        self,
        status: Optional[ExecutionStatus] = None
    ) -> List[ExecutionResult]:
        """Get all executions with optional status filter."""
        executions = list(self.executions.values())
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        return executions
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary của tất cả executions."""
        total = len(self.executions)
        by_status = {
            status.value: sum(
                1 for e in self.executions.values() if e.status == status
            )
            for status in ExecutionStatus
        }
        
        total_processed = sum(
            e.records_processed for e in self.executions.values()
        )
        total_failed = sum(
            e.records_failed for e in self.executions.values()
        )
        
        return {
            "total_executions": total,
            "by_status": by_status,
            "total_records_processed": total_processed,
            "total_records_failed": total_failed,
            "circuit_breaker_states": self.circuit_states.copy()
        }
