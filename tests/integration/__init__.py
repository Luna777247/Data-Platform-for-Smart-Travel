"""
Integration Tests Package
=========================
Integration tests cho Smart Tourism Data Platform

Integration tests verify rằng các components hoạt động cùng nhau đúng cách,
bao gồm database interactions, API endpoints, và external service calls.

Test Coverage:
- API endpoints: Full HTTP request/response cycle
- Database: MongoDB và Redis interactions
- External services: OSM API, Google Places API mocking
- Authentication: JWT token flow

Running Tests:
    pytest tests/integration/           # Run all integration tests
    pytest tests/integration/test_api.py # Run API tests only
    pytest -v --tb=short               # Verbose với short traceback

Note: Integration tests require running database services
      (MongoDB, Redis) để thực hiện actual connections.
"""

# Import pytest cho testing framework
import pytest

__all__ = ["pytest"]
