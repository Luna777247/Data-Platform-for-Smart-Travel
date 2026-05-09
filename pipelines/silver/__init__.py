"""
Silver Layer Package
===================
Silver layer processing cho Smart Tourism Data Platform

Silver layer chứa cleaned và normalized data từ Bronze layer,
với deduplication và business metrics calculation.

Modules:
- silver_processor: Process bronze records thành silver records

Processing Steps:
1. Load bronze data từ multiple sources
2. Deduplicate records sử dụng spatial và name matching
3. Merge duplicate records với conflict resolution
4. Calculate business metrics (popularity, completeness)
5. Create standardized silver records

Example:
    from pipelines.silver import SilverProcessor
    
    processor = SilverProcessor(city_id="tokyo")
    result = await processor.process()
"""

from .silver_processor import SilverProcessor

__all__ = [
    "SilverProcessor",
]