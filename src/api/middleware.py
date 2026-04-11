"""Request logging helpers — standalone utilities and FastAPI ASGI middleware."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


def log_request(method: str, path: str) -> str:
    """Log an incoming request and return a correlation ID."""
    request_id = str(uuid.uuid4())
    logger.info("request_id=%s method=%s path=%s", request_id, method, path)
    return request_id


def log_response(request_id: str, status: int, start_time: float) -> None:
    """Log a completed request with timing."""
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("request_id=%s status=%d duration_ms=%.1f", request_id, status, duration_ms)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs every request with a correlation ID and duration."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        request_id = str(uuid.uuid4())
        logger.info(
            "request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s status=%d duration_ms=%.1f",
            request_id,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
