"""
Unit Tests Package
==================
Unit tests cho Smart Tourism Data Platform

Test Organization:
- test_core/: Tests cho core modules (config, database, logging)
- test_services/: Tests cho business services
- test_utils/: Tests cho utility functions
- test_api/: Tests cho API layer (schemas, dependencies)

Running Tests:
    pytest tests/unit/           # Run all unit tests
    pytest tests/unit/test_core/ # Run specific module tests
    pytest -v                  # Verbose output
    pytest --cov=src           # With coverage
"""

# Import common test utilities
import pytest

__all__ = ["pytest"]
