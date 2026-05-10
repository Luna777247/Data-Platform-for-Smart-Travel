"""
Pipelines Shared Module
=========================

Shared components cho pipeline modules:
- schemas: Data contracts (BronzeRecord, SilverRecord, GoldRecord)
- utils: Common utilities
"""

from src.pipelines.shared.schemas import BronzeRecord, SilverRecord, GoldRecord

__all__ = ["BronzeRecord", "SilverRecord", "GoldRecord"]
