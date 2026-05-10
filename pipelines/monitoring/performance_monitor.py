"""
Performance Monitor
==================

Performance monitoring cho pipeline execution.
Theo RECOMMENDED_STRUCTURE.md - pipelines/monitoring/performance_monitor.py
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at một point in time."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    records_per_second: float
    latency_ms: float


class PerformanceMonitor:
    """
    Monitor và track pipeline performance.
    
    Tracks:
    1. Throughput (records/second)
    2. Latency (processing time)
    3. Resource usage
    4. Bottlenecks
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.snapshots: deque = deque(maxlen=max_history)
        self.stage_stats: Dict[str, Dict[str, Any]] = {}
        
        logger.info("PerformanceMonitor initialized")
    
    def record_snapshot(
        self,
        records_processed: int,
        duration_seconds: float,
        stage: str = "unknown"
    ):
        """
        Record performance snapshot.
        
        Args:
            records_processed: Number of records processed
            duration_seconds: Processing duration
            stage: Pipeline stage
        """
        timestamp = time.time()
        
        # Calculate metrics
        if duration_seconds > 0:
            records_per_second = records_processed / duration_seconds
            latency_ms = (duration_seconds / max(records_processed, 1)) * 1000
        else:
            records_per_second = 0
            latency_ms = 0
        
        snapshot = PerformanceSnapshot(
            timestamp=timestamp,
            cpu_percent=0.0,  # Would need psutil for real values
            memory_mb=0.0,
            records_per_second=records_per_second,
            latency_ms=latency_ms
        )
        
        self.snapshots.append(snapshot)
        
        # Update stage stats
        if stage not in self.stage_stats:
            self.stage_stats[stage] = {
                "total_records": 0,
                "total_duration": 0,
                "avg_throughput": 0,
                "avg_latency_ms": 0,
                "executions": 0
            }
        
        stats = self.stage_stats[stage]
        stats["total_records"] += records_processed
        stats["total_duration"] += duration_seconds
        stats["executions"] += 1
        stats["avg_throughput"] = (
            stats["total_records"] / stats["total_duration"]
            if stats["total_duration"] > 0 else 0
        )
        stats["avg_latency_ms"] = (
            (stats["total_duration"] * 1000) / stats["total_records"]
            if stats["total_records"] > 0 else 0
        )
    
    def get_current_throughput(self) -> float:
        """Get current throughput (records/second)."""
        if len(self.snapshots) < 2:
            return 0.0
        
        recent = list(self.snapshots)[-10:]  # Last 10 snapshots
        if not recent:
            return 0.0
        
        avg_rps = sum(s.records_per_second for s in recent) / len(recent)
        return avg_rps
    
    def get_average_latency(self) -> float:
        """Get average latency (ms)."""
        if not self.snapshots:
            return 0.0
        
        recent = list(self.snapshots)[-100:]  # Last 100 snapshots
        if not recent:
            return 0.0
        
        avg_latency = sum(s.latency_ms for s in recent) / len(recent)
        return avg_latency
    
    def get_stage_performance(self, stage: str) -> Dict[str, Any]:
        """Get performance metrics cho một stage."""
        stats = self.stage_stats.get(stage, {
            "total_records": 0,
            "total_duration": 0,
            "avg_throughput": 0,
            "avg_latency_ms": 0,
            "executions": 0
        })
        
        return {
            "stage": stage,
            "executions": stats["executions"],
            "total_records": stats["total_records"],
            "total_duration_seconds": round(stats["total_duration"], 2),
            "avg_throughput_rps": round(stats["avg_throughput"], 2),
            "avg_latency_ms": round(stats["avg_latency_ms"], 2),
            "efficiency_score": self._calculate_efficiency(stats)
        }
    
    def get_all_stage_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance for all stages."""
        return {
            stage: self.get_stage_performance(stage)
            for stage in self.stage_stats.keys()
        }
    
    def identify_bottlenecks(
        self,
        threshold_latency_ms: float = 1000
    ) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for stage, stats in self.stage_stats.items():
            if stats["avg_latency_ms"] > threshold_latency_ms:
                bottlenecks.append({
                    "stage": stage,
                    "avg_latency_ms": round(stats["avg_latency_ms"], 2),
                    "severity": "high" if stats["avg_latency_ms"] > 5000 else "medium",
                    "recommendation": f"Consider optimizing {stage} stage"
                })
        
        # Sort by latency
        bottlenecks.sort(key=lambda x: x["avg_latency_ms"], reverse=True)
        
        return bottlenecks
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        if not self.snapshots:
            return {"message": "No performance data available"}
        
        recent = list(self.snapshots)[-100:]
        
        return {
            "current_throughput_rps": round(self.get_current_throughput(), 2),
            "average_latency_ms": round(self.get_average_latency(), 2),
            "total_snapshots": len(self.snapshots),
            "stage_performance": self.get_all_stage_performance(),
            "bottlenecks": self.identify_bottlenecks(),
            "status": self._get_status()
        }
    
    def _calculate_efficiency(self, stats: Dict[str, Any]) -> float:
        """Calculate efficiency score (0-100)."""
        if stats["executions"] == 0:
            return 0.0
        
        # Higher throughput = better efficiency
        # Lower latency = better efficiency
        throughput_score = min(stats["avg_throughput"] / 100, 1.0) * 50
        
        # Lower latency is better
        latency_score = max(0, 1 - (stats["avg_latency_ms"] / 5000)) * 50
        
        return throughput_score + latency_score
    
    def _get_status(self) -> str:
        """Get overall performance status."""
        avg_latency = self.get_average_latency()
        throughput = self.get_current_throughput()
        
        if avg_latency < 100 and throughput > 50:
            return "excellent"
        elif avg_latency < 500 and throughput > 20:
            return "good"
        elif avg_latency < 1000:
            return "fair"
        else:
            return "poor"
    
    def reset(self):
        """Reset all performance data."""
        self.snapshots.clear()
        self.stage_stats.clear()
        logger.info("Performance data reset")
