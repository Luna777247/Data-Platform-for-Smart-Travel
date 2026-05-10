"""
Validation Utilities
====================

Data validation helper functions.
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*(?:\?[\w\.&=]*)?$'
    return bool(re.match(pattern, url))


def validate_phone(phone: str) -> bool:
    """Validate phone number format (basic)."""
    # Remove common separators and check if remaining is digits
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def validate_required(value: any, field_name: str) -> Optional[str]:
    """Validate required field."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return f"{field_name} is required"
    return None


def validate_length(
    value: str,
    field_name: str,
    min_len: int = 0,
    max_len: int = 255
) -> Optional[str]:
    """Validate string length."""
    if len(value) < min_len:
        return f"{field_name} must be at least {min_len} characters"
    if len(value) > max_len:
        return f"{field_name} must be at most {max_len} characters"
    return None
