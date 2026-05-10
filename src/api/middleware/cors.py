"""
CORS Middleware Configuration
===========================

CORS (Cross-Origin Resource Sharing) configuration for the API.
"""

from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from src.core.config import settings


def setup_cors_middleware(app):
    """
    Setup CORS middleware for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Get allowed origins from settings
    origins = settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"]
    
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=600,  # 10 minutes
    )
    
    return app
