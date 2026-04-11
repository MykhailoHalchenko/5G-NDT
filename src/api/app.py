"""5G Network Digital Twin — FastAPI application with OpenAPI integration.

Exposes all Digital Twin capabilities as async REST endpoints and automatically
generates an OpenAPI 3.1 specification accessible at ``/openapi.json`` and
interactive Swagger UI at ``/docs``.

Run with:
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .middleware import RequestLoggingMiddleware
from .routes.activation import router as activation_router
from .routes.metrics import router as metrics_router
from .routes.topology import router as topology_router

logger = logging.getLogger(__name__)

# ── OpenAPI metadata ──────────────────────────────────────────────────────────

_DESCRIPTION = """
## 5G Network Digital Twin API

Real-time REST interface for the **5G NDT** platform built at the KAI Network Lab.

### Capabilities
* **Topology** — query gNodeBs, network slices and logical connections in
  the live topology graph.
* **Metrics** — retrieve KPI definitions and per-entity KPI snapshots with
  automated severity classification (INFO / WARNING / CRITICAL).
* **Activation** — submit, monitor, cancel and roll-back network activation
  workflows for service provisioning and slice management.

### Authentication
All endpoints accept an optional `Bearer` token in the `Authorization` header.
Token validation is handled by the authentication module (JWT in production).
"""

_TAGS_METADATA = [
    {
        "name": "Topology",
        "description": "Query the live 5G network topology (gNodeBs, slices, connections).",
    },
    {
        "name": "Metrics",
        "description": "KPI metric definitions and per-entity telemetry snapshots.",
    },
    {
        "name": "Activation",
        "description": "Network service activation workflow management.",
    },
    {
        "name": "Health",
        "description": "Service liveness and readiness probes.",
    },
]


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    logger.info("5G NDT API starting up")
    yield
    logger.info("5G NDT API shutting down")


# ── Application factory ───────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    application = FastAPI(
        title="5G Network Digital Twin API",
        description=_DESCRIPTION,
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_tags=_TAGS_METADATA,
        lifespan=lifespan,
    )

    # CORS — allow all origins for internal lab use; restrict in production
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request/response logging with correlation IDs
    application.add_middleware(RequestLoggingMiddleware)

    # API routers
    application.include_router(topology_router, prefix="/api/v1")
    application.include_router(metrics_router, prefix="/api/v1")
    application.include_router(activation_router, prefix="/api/v1")

    # Health probe
    @application.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict:
        return {"status": "ok"}

    return application


# Module-level application instance used by uvicorn
app = create_app()
