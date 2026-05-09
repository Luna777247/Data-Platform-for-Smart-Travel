"""
Services Package
==================
Business logic services cho Smart Tourism Data Platform

Services:
- pipeline_management_service: Pipeline control và execution
- data_query_service: Data query và retrieval
- monitoring_service: Monitoring và alerting
- data_quality_service: Data quality checks
- notification_service: Notifications (email, slack, etc.)
- auth_service: Authentication và authorization

All services implement Service Pattern với dependency injection support.
"""

from .pipeline_management_service import PipelineManagementService

__all__ = [
    "PipelineManagementService",
]