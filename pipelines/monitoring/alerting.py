"""
Pipeline Alerting System
=========================

Alert management cho pipeline monitoring.
Theo RECOMMENDED_STRUCTURE.md - pipelines/monitoring/alerting.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(Enum):
    """Alert categories."""
    PIPELINE = "pipeline"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    DATA = "data"


@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    source: str
    timestamp: str
    metadata: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[str] = None


class AlertManager:
    """
    Manage alerts cho pipeline monitoring.
    
    Features:
    1. Alert creation và storage
    2. Alert routing (Slack, Email, Webhook)
    3. Alert acknowledgement
    4. Alert resolution
    5. Alert suppression
    """
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.suppressed_rules: List[Dict[str, Any]] = []
        self.routing_rules: Dict[str, List[str]] = {}
        
        logger.info("AlertManager initialized")
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        category: AlertCategory,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create new alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            category: Alert category
            source: Source component
            metadata: Additional data
            
        Returns:
            Created alert
        """
        alert_id = f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.alerts)}"
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        
        # Check if should be suppressed
        if self._should_suppress(alert):
            logger.debug(f"Alert suppressed: {title}")
            return alert
        
        self.alerts.append(alert)
        
        # Route alert
        self._route_alert(alert)
        
        logger.warning(
            f"Alert created [{severity.value}]: {title} from {source}"
        )
        
        return alert
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge một alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.metadata["acknowledged_by"] = acknowledged_by
                alert.metadata["acknowledged_at"] = datetime.utcnow().isoformat()
                
                logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True
        
        return False
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: str = ""
    ) -> bool:
        """Resolve một alert."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow().isoformat()
                alert.metadata["resolution_notes"] = resolution_notes
                
                logger.info(f"Alert resolved: {alert_id}")
                return True
        
        return False
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        category: Optional[AlertCategory] = None,
        source: Optional[str] = None,
        include_resolved: bool = False
    ) -> List[Alert]:
        """Get alerts với optional filtering."""
        alerts = self.alerts
        
        if not include_resolved:
            alerts = [a for a in alerts if not a.resolved]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        return sorted(
            alerts,
            key=lambda a: (a.severity.value, a.timestamp),
            reverse=True
        )
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary."""
        total = len(self.alerts)
        active = len([a for a in self.alerts if not a.resolved])
        acknowledged = len([a for a in self.alerts if a.acknowledged])
        
        by_severity = {
            sev.value: len([a for a in self.alerts if a.severity == sev])
            for sev in AlertSeverity
        }
        
        by_category = {
            cat.value: len([a for a in self.alerts if a.category == cat])
            for cat in AlertCategory
        }
        
        return {
            "total_alerts": total,
            "active_alerts": active,
            "resolved_alerts": total - active,
            "acknowledged_alerts": acknowledged,
            "by_severity": by_severity,
            "by_category": by_category,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def add_suppression_rule(
        self,
        category: AlertCategory,
        source_pattern: str,
        duration_minutes: int
    ):
        """Add alert suppression rule."""
        rule = {
            "category": category,
            "source_pattern": source_pattern,
            "expires_at": datetime.utcnow().timestamp() + (duration_minutes * 60)
        }
        
        self.suppressed_rules.append(rule)
        logger.info(f"Added suppression rule for {category.value}/{source_pattern}")
    
    def add_routing_rule(
        self,
        category: AlertCategory,
        channels: List[str]
    ):
        """Add alert routing rule."""
        self.routing_rules[category.value] = channels
        logger.info(f"Added routing rule: {category.value} -> {channels}")
    
    def _should_suppress(self, alert: Alert) -> bool:
        """Check if alert should be suppressed."""
        now = datetime.utcnow().timestamp()
        
        for rule in self.suppressed_rules:
            # Clean expired rules
            if rule["expires_at"] < now:
                continue
            
            # Check match
            if (rule["category"] == alert.category and
                rule["source_pattern"] in alert.source):
                return True
        
        return False
    
    def _route_alert(self, alert: Alert):
        """Route alert đến configured channels."""
        channels = self.routing_rules.get(alert.category.value, ["log"])
        
        for channel in channels:
            if channel == "log":
                self._send_to_log(alert)
            elif channel == "slack":
                self._send_to_slack(alert)
            elif channel == "email":
                self._send_to_email(alert)
            elif channel == "webhook":
                self._send_to_webhook(alert)
    
    def _send_to_log(self, alert: Alert):
        """Send alert to log."""
        logger.warning(
            f"ALERT [{alert.severity.value.upper()}] {alert.title}: "
            f"{alert.message} (Source: {alert.source})"
        )
    
    def _send_to_slack(self, alert: Alert):
        """Send alert to Slack (placeholder)."""
        # Implementation would use Slack webhook
        logger.info(f"Would send to Slack: {alert.title}")
    
    def _send_to_email(self, alert: Alert):
        """Send alert to Email (placeholder)."""
        # Implementation would use email service
        logger.info(f"Would send to Email: {alert.title}")
    
    def _send_to_webhook(self, alert: Alert):
        """Send alert to Webhook (placeholder)."""
        # Implementation would POST to webhook URL
        logger.info(f"Would send to Webhook: {alert.title}")
    
    # Alert factory methods
    
    def alert_pipeline_failure(
        self,
        pipeline_id: str,
        city: str,
        stage: str,
        error: str
    ) -> Alert:
        """Create pipeline failure alert."""
        return self.create_alert(
            title=f"Pipeline Failure: {pipeline_id}",
            message=f"Pipeline failed in {stage} stage for {city}: {error}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.PIPELINE,
            source=pipeline_id,
            metadata={"city": city, "stage": stage, "error": error}
        )
    
    def alert_quality_degradation(
        self,
        stage: str,
        city: str,
        quality_score: float,
        threshold: float
    ) -> Alert:
        """Create quality degradation alert."""
        return self.create_alert(
            title=f"Quality Degradation: {stage}/{city}",
            message=f"Quality score {quality_score:.2f} below threshold {threshold}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.QUALITY,
            source=stage,
            metadata={"city": city, "score": quality_score, "threshold": threshold}
        )
    
    def alert_performance_degradation(
        self,
        stage: str,
        metric: str,
        value: float,
        threshold: float
    ) -> Alert:
        """Create performance degradation alert."""
        return self.create_alert(
            title=f"Performance Issue: {stage}",
            message=f"{metric}={value:.2f} exceeds threshold {threshold}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.PERFORMANCE,
            source=stage,
            metadata={"metric": metric, "value": value, "threshold": threshold}
        )
