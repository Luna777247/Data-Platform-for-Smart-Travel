"""
Pipeline Tests Package
======================
Tests cho data processing pipeline components

Test Coverage:
- Ingestion: OSM data collection và bronze record creation
- Bronze: Raw data processing và cleaning
- Silver: Data deduplication và normalization
- Validators: Data quality và schema validation

Running Tests:
    pytest tests/pipeline/              # Run all pipeline tests
    pytest tests/pipeline/test_raw_ingestion.py  # Specific test file
    pytest -v -k "test_bronze"          # Filter by test name
"""

# Import pytest cho testing framework
import pytest

__all__ = ["pytest"]
