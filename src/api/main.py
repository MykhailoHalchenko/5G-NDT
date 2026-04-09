"""FastAPI application entry point for the 5G NDT REST API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .middleware import LoggingMiddleware, add_exception_handlers
from .routes import activation, metrics, topology

# ── Application factory ───────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup / shutdown events."""
    # TODO: initialise DB connections, Kafka consumer, discovery engine
    yield
    # TODO: gracefully close DB connections, stop background tasks


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="5G Network Digital Twin API",
        description=(
            "REST API for the KAI Network Digital Twin platform. "
            "Provides topology querying, KPI retrieval, and service activation."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom middleware ─────────────────────────────────────────────────────
    app.add_middleware(LoggingMiddleware)

    # ── Exception handlers ────────────────────────────────────────────────────
    add_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(topology.router, prefix="/api/v1")
    app.include_router(metrics.router, prefix="/api/v1")
    app.include_router(activation.router, prefix="/api/v1")

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"], summary="Health check")
    async def health() -> dict:
        """Return the service health status."""
        return {"status": "ok", "service": "5g-ndt-api", "version": "0.1.0"}

    return app


app = create_app()
