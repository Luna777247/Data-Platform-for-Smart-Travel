"""
Metrics Collector
=================

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/monitoring/metrics_collector.py

Thu thập metrics cho pipeline execution.
Tích hợp với Prometheus cho monitoring.

Metrics collected:
- Pipeline execution counts (success/failure)
- Pipeline duration
- Records processed
- Data quality scores
- Resource usage
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Loại metric."""
    COUNTER = "counter"    # Cumulative metric
    GAUGE = "gauge"        # Current value
    HISTOGRAM = "histogram"  # Distribution


@dataclass
class MetricValue:
    """Giá trị của một metric."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metric_type: MetricType = MetricType.GAUGE


class MetricsCollector:
    """
    Collector cho pipeline metrics.
    
    Thu thập và expose metrics cho monitoring.
    Hỗ trợ cả Prometheus và internal metrics.
    
    Usage:
        collector = MetricsCollector()
        
        # Record pipeline completion
        collector.record_pipeline_completion("hanoi", "bronze", records=1000)
        
        # Get metrics for reporting
        metrics = collector.get_metrics()
    """
    
    def __init__(self, namespace: str = "smart_tourism"):
        self.namespace = namespace
        self._metrics: List[MetricValue] = []
        self._prometheus_metrics: Dict[str, Any] = {}
        
        # Initialize Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
        
        logger.info(f"MetricsCollector initialized (namespace={namespace})")
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        try:
            # Pipeline execution counter
            self._prometheus_metrics["pipeline_runs"] = Counter(
                f"{self.namespace}_pipeline_runs_total",
                "Total pipeline runs",
                ["city", "stage", "status"]
            )
            
            # Pipeline duration histogram
            self._prometheus_metrics["pipeline_duration"] = Histogram(
                f"{self.namespace}_pipeline_duration_seconds",
                "Pipeline execution duration",
                ["city", "stage"],
                buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
            )
            
            # Records processed counter
            self._prometheus_metrics["records_processed"] = Counter(
                f"{self.namespace}_records_processed_total",
                "Total records processed",
                ["city", "stage"]
            )
            
            # Data quality gauge
            self._prometheus_metrics["data_quality"] = Gauge(
                f"{self.namespace}_data_quality_score",
                "Data quality score (0-1)",
                ["city", "stage"]
            )
            
            # Active pipelines gauge
            self._prometheus_metrics["active_pipelines"] = Gauge(
                f"{self.namespace}_active_pipelines",
                "Number of currently running pipelines",
                ["city"]
            )
            
            # Error counter
            self._prometheus_metrics["errors"] = Counter(
                f"{self.namespace}_pipeline_errors_total",
                "Total pipeline errors",
                ["city", "stage", "error_type"]
            )
            
            logger.info("Prometheus metrics initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}")
    
    def record_pipeline_completion(
        self,
        city: str,
        stage: str,
        records: int = 0,
        duration_seconds: float = 0
    ) -> None:
        """Record một pipeline completion."""
        timestamp = datetime.utcnow()
        
        # Record to internal metrics
        self._metrics.append(MetricValue(
            name="pipeline_runs",
            value=1,
            labels={"city": city, "stage": stage, "status": "success"},
            timestamp=timestamp,
            metric_type=MetricType.COUNTER
        ))
        
        self._metrics.append(MetricValue(
            name="pipeline_duration",
            value=duration_seconds,
            labels={"city": city, "stage": stage},
            timestamp=timestamp,
            metric_type=MetricType.HISTOGRAM
        ))
        
        self._metrics.append(MetricValue(
            name="records_processed",
            value=records,
            labels={"city": city, "stage": stage},
            timestamp=timestamp,
            metric_type=MetricType.COUNTER
        ))
        
        # Record to Prometheus
        if PROMETHEUS_AVAILABLE and self._prometheus_metrics:
            try:
                self._prometheus_metrics["pipeline_runs"].labels(
                    city=city, stage=stage, status="success"
                ).inc()
                
                self._prometheus_metrics["pipeline_duration"].labels(
                    city=city, stage=stage
                ).observe(duration_seconds)
                
                self._prometheus_metrics["records_processed"].labels(
                    city=city, stage=stage
                ).inc(records)
                
            except Exception as e:
                logger.debug(f"Failed to record Prometheus metric: {e}")
        
        logger.debug(f"Recorded pipeline completion: {city}/{stage} ({records} records, "
                    f"{duration_seconds:.2f}s)")
    
    def record_pipeline_failure(
        self,
        city: str,
        stage: str,
        error_message: str,
        error_type: str = "generic"
    ) -> None:
        """Record một pipeline failure."""
        timestamp = datetime.utcnow()
        
        # Record to internal metrics
        self._metrics.append(MetricValue(
            name="pipeline_runs",
            value=1,
            labels={"city": city, "stage": stage, "status": "failure"},
            timestamp=timestamp,
            metric_type=MetricType.COUNTER
        ))
        
        self._metrics.append(MetricValue(
            name="errors",
            value=1,
            labels={"city": city, "stage": stage, "error_type": error_type},
            timestamp=timestamp,
            metric_type=MetricType.COUNTER
        ))
        
        # Record to Prometheus
        if PROMETHEUS_AVAILABLE and self._prometheus_metrics:
            try:
                self._prometheus_metrics["pipeline_runs"].labels(
                    city=city, stage=stage, status="failure"
                ).inc()
                
                self._prometheus_metrics["errors"].labels(
                    city=city, stage=stage, error_type=error_type
                ).inc()
                
            except Exception as e:
                logger.debug(f"Failed to record Prometheus metric: {e}")
        
        logger.debug(f"Recorded pipeline failure: {city}/{stage} - {error_message}")
    
    def record_data_quality(
        self,
        city: str,
        stage: str,
        quality_score: float
    ) -> None:
        """Record data quality score (0-1)."""
        timestamp = datetime.utcnow()
        
        # Clamp to 0-1 range
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Record to internal metrics
        self._metrics.append(MetricValue(
            name="data_quality",
            value=quality_score,
            labels={"city": city, "stage": stage},
            timestamp=timestamp,
            metric_type=MetricType.GAUGE
        ))
        
        # Record to Prometheus
        if PROMETHEUS_AVAILABLE and self._prometheus_metrics:
            try:
                self._prometheus_metrics["data_quality"].labels(
                    city=city, stage=stage
                ).set(quality_score)
                
            except Exception as e:
                logger.debug(f"Failed to record Prometheus metric: {e}")
    
    def record_active_pipelines(self, city: str, count: int) -> None:
        """Record số lượng active pipelines."""
        # Record to Prometheus
        if PROMETHEUS_AVAILABLE and self._prometheus_metrics:
            try:
                self._prometheus_metrics["active_pipelines"].labels(
                    city=city
                ).set(count)
                
            except Exception as e:
                logger.debug(f"Failed to record Prometheus metric: {e}")
    
    def get_metrics(
        self,
        name: Optional[str] = None,
        city: Optional[str] = None,
        stage: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MetricValue]:
        """Lấy metrics với filter."""
        metrics = self._metrics
        
        if name:
            metrics = [m for m in metrics if m.name == name]
        if city:
            metrics = [m for m in metrics if m.labels.get("city") == city]
        if stage:
            metrics = [m for m in metrics if m.labels.get("stage") == stage]
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        # Sort by timestamp descending
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        return metrics[:limit]
    
    def get_aggregated_metrics(
        self,
        metric_name: str,
        aggregation: str = "sum",
        since: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Lấy aggregated metrics."""
        metrics = self.get_metrics(name=metric_name, since=since)
        
        if not metrics:
            return {}
        
        # Group by labels
        groups: Dict[str, List[MetricValue]] = {}
        for m in metrics:
            key = ",".join(f"{k}={v}" for k, v in sorted(m.labels.items()))
            if key not in groups:
                groups[key] = []
            groups[key].append(m)
        
        # Aggregate
        result = {}
        for key, values in groups.items():
            if aggregation == "sum":
                result[key] = sum(m.value for m in values)
            elif aggregation == "avg":
                result[key] = sum(m.value for m in values) / len(values)
            elif aggregation == "count":
                result[key] = len(values)
            elif aggregation == "max":
                result[key] = max(m.value for m in values)
            elif aggregation == "min":
                result[key] = min(m.value for m in values)
        
        return result
    
    def cleanup_old_metrics(self, max_age_hours: int = 24) -> int:
        """Xóa metrics cũ để giảm memory usage."""
        cutoff = datetime.utcnow() - __import__('datetime').timedelta(hours=max_age_hours)
        
        old_count = len(self._metrics)
        self._metrics = [m for m in self._metrics if m.timestamp >= cutoff]
        removed = old_count - len(self._metrics)
        
        logger.info(f"Cleaned up {removed} old metrics")
        return removed
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics ở định dạng Prometheus exposition."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"
        
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return f"# Error: {e}\n"
    
    def get_summary(self) -> Dict[str, Any]:
        """Lấy summary của tất cả metrics."""
        now = datetime.utcnow()
        last_24h = now - __import__('datetime').timedelta(hours=24)
        
        # Count by status
        success_count = len(self.get_metrics(
            name="pipeline_runs",
            since=last_24h
        ))
        failure_count = len(self.get_metrics(
            name="errors",
            since=last_24h
        ))
        
        # Total records
        records_metrics = self.get_metrics(
            name="records_processed",
            since=last_24h
        )
        total_records = sum(m.value for m in records_metrics)
        
        # Quality scores
        quality_metrics = self.get_metrics(
            name="data_quality",
            since=last_24h
        )
        avg_quality = (
            sum(m.value for m in quality_metrics) / len(quality_metrics)
            if quality_metrics else 0
        )
        
        return {
            "total_pipelines_24h": success_count + failure_count,
            "successful_pipelines": success_count,
            "failed_pipelines": failure_count,
            "total_records_processed": total_records,
            "average_quality_score": round(avg_quality, 3),
            "total_metrics_stored": len(self._metrics)
        }
