"""
Notification Utilities
======================

Helper functions for notifications and alerts.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def format_slack_message(
    title: str,
    message: str,
    severity: str = "info",
    fields: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Format message for Slack webhook."""
    colors = {
        "info": "#36a64f",
        "warning": "#ff9900",
        "error": "#ff0000",
        "critical": "#990000"
    }
    
    slack_message = {
        "attachments": [{
            "color": colors.get(severity, "#36a64f"),
            "title": title,
            "text": message,
            "footer": "Smart Tourism Platform",
            "ts": int(datetime.utcnow().timestamp())
        }]
    }
    
    if fields:
        slack_message["attachments"][0]["fields"] = [
            {"title": f["name"], "value": f["value"], "short": True}
            for f in fields
        ]
    
    return slack_message


def format_email_alert(
    subject: str,
    body: str,
    severity: str = "info"
) -> Dict[str, str]:
    """Format email alert."""
    severity_emoji = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "critical": "🚨"
    }
    
    return {
        "subject": f"{severity_emoji.get(severity, 'ℹ️')} [{severity.upper()}] {subject}",
        "body": body,
        "html": f"<h2>{severity.upper()}: {subject}</h2><p>{body}</p>"
    }


def truncate_message(message: str, max_length: int = 4000) -> str:
    """Truncate message to fit within limits."""
    if len(message) <= max_length:
        return message
    return message[:max_length - 3] + "..."


def create_notification_id(prefix: str = "notif") -> str:
    """Generate unique notification ID."""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
