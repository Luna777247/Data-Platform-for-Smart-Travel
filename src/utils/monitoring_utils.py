"""
Monitoring Utilities
====================

Helper functions for monitoring and metrics.
"""

import time
import functools
from typing import Callable, Any
from contextlib import contextmanager


@contextmanager
def timer(metric_name: str, collector=None):
    """
    Context manager to time operations.
    
    Usage:
        with timer("database_query"):
            result = db.query()
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        if collector:
            collector.record_timing(metric_name, duration)


def timed(metric_name: str, collector=None):
    """
    Decorator to time function execution.
    
    Usage:
        @timed("api_request")
        def handle_request():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if collector:
                    collector.record_timing(metric_name, duration)
        return wrapper
    return decorator


def calculate_percentile(values: list, percentile: float) -> float:
    """Calculate percentile from a list of values."""
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * percentile / 100
    
    lower = int(index)
    upper = lower + 1
    
    if upper >= len(sorted_values):
        return sorted_values[-1]
    
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration to human readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
