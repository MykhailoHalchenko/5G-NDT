"""Request logging and CORS helpers — standalone utilities and aiohttp middlewares."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from aiohttp import web

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


@web.middleware
async def logging_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """aiohttp middleware: log every request with a correlation ID and duration."""
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    logger.info(
        "request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.path,
    )
    try:
        response: web.StreamResponse = await handler(request)
    except web.HTTPException as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_id=%s status=%d duration_ms=%.1f",
            request_id,
            exc.status,
            duration_ms,
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request_id=%s status=%d duration_ms=%.1f",
        request_id,
        response.status,
        duration_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@web.middleware
async def cors_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """aiohttp middleware: add CORS headers to every response.

    Handles OPTIONS preflight requests by returning an empty 200 response.
    """
    if request.method == "OPTIONS":
        response: web.StreamResponse = web.Response()
    else:
        response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response
