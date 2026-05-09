"""
API Package
===========
FastAPI REST API layer cho Smart Tourism Data Platform

Structure:
- routes: API endpoints (pipeline, data, monitoring, health, admin)
- schemas: Pydantic models for request/response validation
- dependencies: FastAPI dependencies (auth, database, monitoring)
- middleware: Custom middleware (logging, CORS, rate limiting)

Example:
    from src.api.routes import pipeline_router
    from src.api.schemas import PipelineExecutionRequest
"""

__version__ = "1.0.0"
