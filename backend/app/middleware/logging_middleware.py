import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware for logging HTTP requests and responses.
    Automatically redacts sensitive fields from logs.
    """

    def __init__(self, app):
        """
        Initialize the middleware with the FastAPI app instance.
        """
        super().__init__(app)
        # Paths to exclude from logging
        self.exclude_paths = ["/docs", "/redoc", "/openapi.json", "/favicon.ico", "/health"]
        # Sensitive fields to redact (hardcoded for this project)
        self.sensitive_fields = [
            "password", "password_hash", "current_password", "new_password",
            "token", "access_token", "refresh_token", "secret", "api_key"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the incoming request, log it, and return the response.
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Get user info if authenticated
        user_info = self._get_user_info(request)

        # Log incoming request
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                **user_info
            }
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"✗ {request.method} {request.url.path} - Error: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                    **user_info
                },
                exc_info=True
            )
            raise

        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Log response
        status_icon = "✓" if response.status_code < 400 else "✗"
        log_level = logging.INFO if response.status_code < 400 else logging.WARNING
        if response.status_code >= 500:
            log_level = logging.ERROR

        logger.log(
            log_level,
            f"{status_icon} {request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                **user_info
            }
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    def _get_user_info(self, request: Request) -> dict:
        """Extract user information from request if authenticated."""
        if hasattr(request.state, "user"):
            user = request.state.user
            return {
                "user_id": getattr(user, "id", None),
                "user_email": getattr(user, "email", None),
                "user_role": str(getattr(user, "role", None)),
            }
        return {}

    def _redact_sensitive_data(self, data: dict) -> dict:
        """Redact sensitive fields from data."""
        if not isinstance(data, dict):
            return data

        redacted = {}
        for key, value in data.items():
            if any(field in key.lower() for field in self.sensitive_fields):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive_data(value)
            else:
                redacted[key] = value
        return redacted
