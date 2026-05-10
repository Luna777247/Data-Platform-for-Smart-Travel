"""
Pipeline Module
===============

Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/pipelines/

Module này cung cấp các components cho data processing pipelines:
- orchestration: Pipeline orchestration và scheduling
- monitoring: Pipeline metrics và quality monitoring
- config: Pipeline configurations

Usage:
    from src.pipelines.orchestration import PipelineOrchestrator
    orchestrator = PipelineOrchestrator()
"""

from src.pipelines.orchestration.pipeline_orchestrator import PipelineOrchestrator
from src.pipelines.monitoring.metrics_collector import MetricsCollector
from src.pipelines.monitoring.quality_monitor import QualityMonitor

__all__ = [
    "PipelineOrchestrator",
    "MetricsCollector", 
    "QualityMonitor",
]
