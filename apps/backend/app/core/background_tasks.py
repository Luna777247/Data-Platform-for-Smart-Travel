"""
Background task utilities for proper lifecycle management.

Ensures background tasks are properly tracked and awaited during shutdown,
preventing orphaned coroutines and ensuring data consistency.
"""

import asyncio
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

# Global task registry - populated by create_background_task()
_pending_tasks: set = set()


def get_pending_tasks() -> set:
    """Get the set of currently pending background tasks."""
    return _pending_tasks.copy()


async def wait_for_pending_tasks(timeout: float = 30.0) -> None:
    """
    Wait for all pending background tasks to complete.
    
    Used during application shutdown to ensure graceful cleanup.
    """
    if not _pending_tasks:
        return
    
    logger.info(f"Waiting for {len(_pending_tasks)} pending background tasks...")
    try:
        await asyncio.wait_for(
            asyncio.gather(*_pending_tasks, return_exceptions=True),
            timeout=timeout
        )
        logger.info("✅ All background tasks completed")
    except asyncio.TimeoutError:
        logger.warning(
            f"⚠️  {len(_pending_tasks)} background tasks did not complete within {timeout}s"
        )


def create_background_task(
    coro: Any,
    name: Optional[str] = None,
    error_callback: Optional[Callable[[Exception], None]] = None
) -> asyncio.Task:
    """
    Create a background task that is properly tracked for shutdown.
    
    Usage:
    ```python
    task = create_background_task(
        service.long_running_operation(),
        name="pipeline_execution",
        error_callback=lambda e: logger.error(f"Task failed: {e}")
    )
    ```
    
    Args:
        coro: The coroutine to run in the background
        name: Optional task name for logging
        error_callback: Optional callback if task fails
    
    Returns:
        The asyncio Task object
    """
    task = asyncio.create_task(coro, name=name)
    _pending_tasks.add(task)
    
    # Cleanup callback: remove task when done
    def task_done_callback(t: asyncio.Task) -> None:
        _pending_tasks.discard(t)
        try:
            if t.exception():
                exception = t.exception()
                logger.error(
                    f"Background task {name or 'unnamed'} failed: {exception}",
                    exc_info=(type(exception), exception, exception.__traceback__)
                )
                if error_callback:
                    try:
                        error_callback(exception)
                    except Exception as e:
                        logger.error(f"Error in error callback: {e}")
        except asyncio.CancelledError:
            logger.info(f"Background task {name or 'unnamed'} was cancelled")
        except Exception:
            pass  # Task result already handled above
    
    task.add_done_callback(task_done_callback)
    return task
