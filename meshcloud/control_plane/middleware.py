"""Middleware for MeshCloud security and rate limiting."""
import time

# Removed unused import: defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter

# Removed unused import: SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from meshcloud.security.auth import sanitize_filename, validate_file_size

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for input validation and request sanitization."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate and sanitize filename parameters
        if "filename" in request.path_params:
            filename = request.path_params["filename"]
            sanitized = sanitize_filename(filename)
            if sanitized != filename:
                return JSONResponse(status_code=400, content={"error": "Invalid filename"})
            request.path_params["filename"] = sanitized

        # Validate file size for upload endpoints
        if request.url.path in ["/upload", "/upload_chunk"] and request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if not validate_file_size(size):
                        return JSONResponse(status_code=413, content={"error": "File too large"})
                except ValueError:
                    pass  # Invalid content-length header

        # Add security headers
        start_time = time.time()

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        self.logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        self.logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path} " f"in {process_time:.3f}s"
        )

        return response


def create_rate_limit_exceeded_handler():
    """Create handler for rate limit exceeded errors."""

    def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Too many requests. Try again in {exc.retry_after} seconds.",
            },
            headers={"Retry-After": str(exc.retry_after)},
        )

    return rate_limit_handler
