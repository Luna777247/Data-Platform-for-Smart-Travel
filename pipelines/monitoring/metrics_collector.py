"""
Pipeline Metrics Collector
==========================

Metrics collection cho pipeline monitoring.
Theo RECOMMENDED_STRUCTURE.md - pipelines/monitoring/metrics_collector.py
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from prometheus_client import Counter, Histogram, Gauge, Info

logger = logging.getLogger(__name__)


class PipelineMetricsCollector:
    """
    Collect và expose metrics cho Prometheus.
    
    Metrics:
    1. Execution counts
    2. Duration histograms
    3. Record counts
    4. Error rates
    5. Stage performance
    """
    
    def __init__(self):
        # Prometheus metrics
        self.execution_counter = Counter(
            'pipeline_executions_total',
            'Total pipeline executions',
            ['stage', 'city', 'status']
        )
        
        self.execution_duration = Histogram(
            'pipeline_execution_duration_seconds',
            'Pipeline execution duration',
            ['stage', 'city'],
            buckets=[.1, .5, 1, 2, 5, 10, 30, 60, 120, 300]
        )
        
        self.records_counter = Counter(
            'pipeline_records_processed_total',
            'Total records processed',
            ['stage', 'city', 'operation']
        )
        
        self.active_executions = Gauge(
            'pipeline_active_executions',
            'Currently active executions',
            ['stage']
        )
        
        self.quality_score = Gauge(
            'pipeline_quality_score',
            'Data quality score',
            ['stage', 'city']
        )
        
        # Internal metrics storage
        self.metrics_history: List[Dict[str, Any]] = []
        
        logger.info("PipelineMetricsCollector initialized")
    
    def record_execution_start(
        self,
        stage: str,
        city: str
    ):
        """Record start của execution."""
        self.active_executions.labels(stage=stage).inc()
        
        logger.debug(f"Execution started: {stage} for {city}")
    
    def record_execution_complete(
        self,
        stage: str,
        city: str,
        status: str,
        duration_seconds: float,
        records_in: int = 0,
        records_out: int = 0
    ):
        """
        Record completion của execution.
        
        Args:
            stage: Pipeline stage (bronze/silver/gold)
            city: Target city
            status: Execution status (completed/failed)
            duration_seconds: Execution duration
            records_in: Input records
            records_out: Output records
        """
        # Update Prometheus metrics
        self.execution_counter.labels(
            stage=stage,
            city=city,
            status=status
        ).inc()
        
        self.execution_duration.labels(
            stage=stage,
            city=city
        ).observe(duration_seconds)
        
        self.records_counter.labels(
            stage=stage,
            city=city,
            operation="input"
        ).inc(records_in)
        
        self.records_counter.labels(
            stage=stage,
            city=city,
            operation="output"
        ).inc(records_out)
        
        self.active_executions.labels(stage=stage).dec()
        
        # Store metric
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage": stage,
            "city": city,
            "status": status,
            "duration_seconds": duration_seconds,
            "records_in": records_in,
            "records_out": records_out
        }
        self.metrics_history.append(metric)
        
        logger.info(
            f"Execution complete: {stage} for {city} - "
            f"{status} ({records_in}->{records_out} records, "
            f"{duration_seconds:.2f}s)"
        )
    
    def record_quality_score(
        self,
        stage: str,
        city: str,
        score: float
    ):
        """Record quality score."""
        self.quality_score.labels(
            stage=stage,
            city=city
        ).set(score)
    
    def record_error(
        self,
        stage: str,
        city: str,
        error_type: str
    ):
        """Record error occurrence."""
        error_counter = Counter(
            'pipeline_errors_total',
            'Total errors',
            ['stage', 'city', 'error_type']
        )
        error_counter.labels(
            stage=stage,
            city=city,
            error_type=error_type
        ).inc()
    
    def get_metrics_summary(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get summary của collected metrics."""
        metrics = self.metrics_history
        
        if since:
            metrics = [
                m for m in metrics
                if datetime.fromisoformat(m["timestamp"]) >= since
            ]
        
        if not metrics:
            return {"message": "No metrics available"}
        
        # Calculate statistics
        total_executions = len(metrics)
        successful = sum(1 for m in metrics if m["status"] == "completed")
        failed = total_executions - successful
        
        avg_duration = sum(m["duration_seconds"] for m in metrics) / total_executions
        
        total_in = sum(m["records_in"] for m in metrics)
        total_out = sum(m["records_out"] for m in metrics)
        
        # By stage
        by_stage: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0,
            "total_records": 0
        })
        
        for m in metrics:
            stage = m["stage"]
            by_stage[stage]["count"] += 1
            
            if m["status"] == "completed":
                by_stage[stage]["successful"] += 1
            else:
                by_stage[stage]["failed"] += 1
            
            # Update average
            prev_avg = by_stage[stage]["avg_duration"]
            count = by_stage[stage]["count"]
            by_stage[stage]["avg_duration"] = (
                (prev_avg * (count - 1) + m["duration_seconds"]) / count
            )
            
            by_stage[stage]["total_records"] += m["records_out"]
        
        return {
            "total_executions": total_executions,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_executions if total_executions > 0 else 0,
            "avg_duration_seconds": round(avg_duration, 2),
            "total_records_in": total_in,
            "total_records_out": total_out,
            "by_stage": dict(by_stage),
            "time_range": {
                "from": metrics[0]["timestamp"] if metrics else None,
                "to": metrics[-1]["timestamp"] if metrics else None
            }
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus exposition format."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest().decode('utf-8')
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics_history = []
        
        # Reset Prometheus metrics
        for collector in [
            self.execution_counter,
            self.execution_duration,
            self.records_counter,
            self.active_executions,
            self.quality_score
        ]:
            collector.clear()
        
        logger.info("Metrics reset")
