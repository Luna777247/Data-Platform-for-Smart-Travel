"""
Rate Limiting Middleware
========================

Middleware for API rate limiting.
"""

import logging
import time
from typing import Dict, Optional, Callable
from collections import defaultdict

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to rate limit requests.
    
    Simple in-memory rate limiting. In production, use Redis.
    """
    
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI app
            max_requests: Max requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        logger.info(f"RateLimitMiddleware initialized ({max_requests}/{window_seconds}s)")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Clean old requests
        now = time.time()
        cutoff = now - self.window_seconds
        
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Record request
        self.requests[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.max_requests - len(self.requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(cutoff + self.window_seconds))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for client."""
        # Try to get from auth token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:15]  # Use token prefix as ID
        
        # Fall back to IP address
        if request.client:
            return request.client.host
        
        return "unknown"


class RateLimitByUserMiddleware(BaseHTTPMiddleware):
    """Rate limiting based on authenticated user."""
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit for authenticated users."""
        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        
        if user:
            user_id = str(user)
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Clean old requests
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > cutoff
            ]
            
            # Check limit (higher limit for authenticated users)
            if len(self.requests[user_id]) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded for user"
                )
            
            self.requests[user_id].append(now)
        
        return await call_next(request)
