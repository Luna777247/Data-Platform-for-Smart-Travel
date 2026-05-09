"""
Shared Components Package
==========================
Shared utilities và schemas cho pipeline processing

Modules:
- schemas: Data models và type definitions
- utils: Common utility functions

Example:
    from pipelines.shared import make_ukey, setup_logging
    from pipelines.shared.schemas import BronzeRecord
"""

from .utils import setup_logging, make_ukey, normalize_coordinates
from .schemas import BronzeRecord, SilverPlace

__all__ = [
    "setup_logging",
    "make_ukey",
    "normalize_coordinates",
    "BronzeRecord",
    "SilverPlace",
]