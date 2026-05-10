"""
Date Utilities
==============

Date and time helper functions.
"""

from datetime import datetime, timezone
from typing import Optional


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse string to datetime."""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso_format(dt: datetime) -> str:
    """Convert datetime to ISO format."""
    return dt.isoformat()


def from_iso_format(date_str: str) -> Optional[datetime]:
    """Parse ISO format string to datetime."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None
