"""
Authentication Utilities
========================

Helper functions for authentication.
"""

import hashlib
import secrets
from typing import Optional


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def mask_token(token: str, visible_chars: int = 4) -> str:
    """Mask a token for display (e.g., ****abcd)."""
    if len(token) <= visible_chars * 2:
        return "****"
    return f"****{token[-visible_chars:]}"


def generate_nonce(length: int = 16) -> str:
    """Generate a nonce for security purposes."""
    return secrets.token_hex(length)
