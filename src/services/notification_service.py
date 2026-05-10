"""
Notification Service
====================

Business logic cho notifications và alerting.
Theo thiết kế: RECOMMENDED_STRUCTURE.md - src/services/notification_service.py

Responsibilities:
- Email notifications
- Slack notifications
- Alert management
- Notification templates
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Loại notification."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(Enum):
    """Mức độ ưu tiên."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """
    Service cho notification management.
    
    Provides:
    - Email notifications
    - Slack integration
    - Webhook notifications
    - Alert templates
    - Notification history
    """
    
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        logger.info("NotificationService initialized")
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Gửi notification."""
        try:
            # Log notification
            notification = {
                "id": f"notif_{datetime.utcnow().timestamp()}",
                "type": notification_type.value,
                "recipient": recipient,
                "subject": subject,
                "message": message[:500],  # Limit length
                "priority": priority.value,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "sent",
                "metadata": metadata or {}
            }
            
            self._history.append(notification)
            
            # In production, integrate with actual services
            if notification_type == NotificationType.EMAIL:
                logger.info(f"Email notification sent to {recipient}: {subject}")
            elif notification_type == NotificationType.SLACK:
                logger.info(f"Slack notification sent to {recipient}: {subject}")
            elif notification_type == NotificationType.WEBHOOK:
                logger.info(f"Webhook notification sent to {recipient}: {subject}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def send_pipeline_alert(
        self,
        pipeline_name: str,
        status: str,
        message: str,
        recipients: List[str]
    ) -> bool:
        """Gửi pipeline alert."""
        subject = f"Pipeline Alert: {pipeline_name} - {status}"
        
        for recipient in recipients:
            await self.send_notification(
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                subject=subject,
                message=message,
                priority=NotificationPriority.HIGH if status == "failed" else NotificationPriority.MEDIUM
            )
        
        return True
    
    async def send_quality_alert(
        self,
        city: str,
        quality_score: float,
        recipients: List[str]
    ) -> bool:
        """Gửi data quality alert."""
        subject = f"Data Quality Alert: {city} - Score: {quality_score:.2f}"
        message = f"Data quality score for {city} is {quality_score:.2f}, below acceptable threshold."
        
        for recipient in recipients:
            await self.send_notification(
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                subject=subject,
                message=message,
                priority=NotificationPriority.MEDIUM
            )
        
        return True
    
    async def get_notification_history(
        self,
        limit: int = 100,
        notification_type: Optional[NotificationType] = None
    ) -> List[Dict[str, Any]]:
        """Lấy notification history."""
        history = self._history
        
        if notification_type:
            history = [h for h in history if h["type"] == notification_type.value]
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return history[:limit]
