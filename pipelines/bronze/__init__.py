"""
Bronze Layer Package
===================
Bronze layer processing cho Smart Tourism Data Platform

Bronze layer chứa raw data từ ingestion layer, được làm sạch và chuẩn hóa
trước khi chuyển sang Silver layer.

Modules:
- osm_processor: Process OSM raw data thành bronze records

Processing Steps:
1. Load raw data từ JSON files
2. Validate data structure
3. Clean và normalize fields
4. Calculate quality scores
5. Save processed bronze records

Example:
    from pipelines.bronze import BronzeOSMProcessor
    
    processor = BronzeOSMProcessor(city_id="tokyo", category="hotel")
    result = await processor.process()
"""

from .osm_processor import BronzeOSMProcessor

__all__ = [
    "BronzeOSMProcessor",
]