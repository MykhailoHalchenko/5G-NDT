"""Request logging helpers (no longer depends on FastAPI)."""

from __future__ import annotations

import logging
import time
import uuid

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
