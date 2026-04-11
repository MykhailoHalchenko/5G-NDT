"""5G Network Digital Twin — aiohttp application with OpenAPI (apispec) integration.

Exposes all Digital Twin capabilities as async REST endpoints.  The OpenAPI 3.0
specification is generated programmatically via ``apispec`` and served at
``/openapi.json``; an interactive Swagger UI is served at ``/docs``.

Run with:
    python -m src.api.app        (development, port 8000)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from aiohttp import web
from apispec import APISpec

from .middleware import cors_middleware, logging_middleware
from .routes.activation import register_routes as register_activation
from .routes.metrics import register_routes as register_metrics
from .routes.topology import register_routes as register_topology

logger = logging.getLogger(__name__)

# ── OpenAPI metadata ──────────────────────────────────────────────────────────

_DESCRIPTION = (
    "Real-time REST interface for the **5G NDT** platform built at the KAI Network Lab. "
    "Provides topology queries, KPI metrics, and network activation workflow management."
)

_SWAGGER_UI_HTML = """\
<!DOCTYPE html>
<html>
<head>
  <title>5G NDT API — Swagger UI</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet"
        href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/openapi.json",
      dom_id: "#swagger-ui",
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
      layout: "BaseLayout"
    })
  </script>
</body>
</html>
"""


# ── OpenAPI spec builder ──────────────────────────────────────────────────────


def build_openapi_spec() -> Dict[str, Any]:
    """Build and return the OpenAPI 3.0 specification as a plain dict.

    Uses ``apispec`` to construct the spec programmatically.  All paths are
    registered once at startup so the spec reflects the live route table.
    """
    spec = APISpec(
        title="5G Network Digital Twin API",
        version="0.1.0",
        openapi_version="3.0.3",
        info={"description": _DESCRIPTION},
    )

    # ── Tags ──────────────────────────────────────────────────────────────────
    spec.tag({"name": "Health", "description": "Service liveness and readiness probes."})
    spec.tag({"name": "Topology", "description": "Query the live 5G network topology."})
    spec.tag({"name": "Metrics", "description": "KPI metric definitions and telemetry snapshots."})
    spec.tag({"name": "Activation", "description": "Network activation workflow management."})

    # ── Health ────────────────────────────────────────────────────────────────
    spec.path(
        path="/health",
        operations={
            "get": {
                "tags": ["Health"],
                "summary": "Liveness probe",
                "responses": {"200": {"description": "Service is alive"}},
            }
        },
    )

    # ── Topology ──────────────────────────────────────────────────────────────
    spec.path(
        path="/api/v1/topology/",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "Get full topology snapshot",
                "responses": {"200": {"description": "Current topology snapshot"}},
            }
        },
    )
    spec.path(
        path="/api/v1/topology/gnodebs",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "List all gNodeBs",
                "responses": {"200": {"description": "List of gNodeB objects"}},
            }
        },
    )
    spec.path(
        path="/api/v1/topology/gnodebs/{gnb_id}",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "Get a specific gNodeB by UUID",
                "parameters": [
                    {"in": "path", "name": "gnb_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "gNodeB object"},
                    "404": {"description": "Not found"},
                },
            }
        },
    )
    spec.path(
        path="/api/v1/topology/slices",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "List all network slices",
                "responses": {"200": {"description": "List of NetworkSlice objects"}},
            }
        },
    )
    spec.path(
        path="/api/v1/topology/slices/{slice_id}",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "Get a specific network slice by UUID",
                "parameters": [
                    {"in": "path", "name": "slice_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "NetworkSlice object"},
                    "404": {"description": "Not found"},
                },
            }
        },
    )
    spec.path(
        path="/api/v1/topology/connections",
        operations={
            "get": {
                "tags": ["Topology"],
                "summary": "List all logical connections",
                "responses": {"200": {"description": "List of Connection objects"}},
            }
        },
    )

    # ── Metrics ───────────────────────────────────────────────────────────────
    spec.path(
        path="/api/v1/metrics/definitions",
        operations={
            "get": {
                "tags": ["Metrics"],
                "summary": "List all KPI metric definitions",
                "responses": {"200": {"description": "List of metric definition objects"}},
            }
        },
    )
    spec.path(
        path="/api/v1/metrics/definitions/{entity_type}",
        operations={
            "get": {
                "tags": ["Metrics"],
                "summary": "List KPI metrics applicable to a given entity type",
                "parameters": [
                    {"in": "path", "name": "entity_type", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "Filtered metric definition list"}},
            }
        },
    )
    spec.path(
        path="/api/v1/metrics/summary/{entity_id}",
        operations={
            "get": {
                "tags": ["Metrics"],
                "summary": "Get latest KPI summary for a network entity",
                "parameters": [
                    {"in": "path", "name": "entity_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {"200": {"description": "KPI summary dict"}},
            }
        },
    )
    spec.path(
        path="/api/v1/metrics/snapshots/{entity_id}",
        operations={
            "get": {
                "tags": ["Metrics"],
                "summary": "Get KPI snapshots for a network entity",
                "parameters": [
                    {"in": "path", "name": "entity_id", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"in": "query", "name": "entity_type", "schema": {"type": "string", "default": "gNodeB"}},
                ],
                "responses": {"200": {"description": "List of KPI snapshot dicts"}},
            }
        },
    )

    # ── Activation ────────────────────────────────────────────────────────────
    spec.path(
        path="/api/v1/activation/workflows",
        operations={
            "get": {
                "tags": ["Activation"],
                "summary": "List all activation workflows",
                "responses": {"200": {"description": "List of workflow dicts"}},
            },
            "post": {
                "tags": ["Activation"],
                "summary": "Submit a new activation workflow",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["workflow_type", "target_entity_id"],
                                "properties": {
                                    "workflow_type": {"type": "string"},
                                    "target_entity_id": {"type": "string", "format": "uuid"},
                                    "parameters": {"type": "object"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "202": {"description": "Workflow accepted"},
                    "422": {"description": "Validation failure"},
                },
            },
        },
    )
    spec.path(
        path="/api/v1/activation/workflows/{workflow_id}",
        operations={
            "get": {
                "tags": ["Activation"],
                "summary": "Get the status of an activation workflow",
                "parameters": [
                    {"in": "path", "name": "workflow_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "Workflow dict"},
                    "404": {"description": "Not found"},
                },
            }
        },
    )
    spec.path(
        path="/api/v1/activation/workflows/{workflow_id}/cancel",
        operations={
            "delete": {
                "tags": ["Activation"],
                "summary": "Cancel a pending or running workflow",
                "parameters": [
                    {"in": "path", "name": "workflow_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {"200": {"description": "Cancellation result"}},
            }
        },
    )
    spec.path(
        path="/api/v1/activation/workflows/{workflow_id}/rollback",
        operations={
            "post": {
                "tags": ["Activation"],
                "summary": "Roll back a completed or failed workflow",
                "parameters": [
                    {"in": "path", "name": "workflow_id", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {"200": {"description": "Rollback result"}},
            }
        },
    )

    return spec.to_dict()


# ── Application factory ───────────────────────────────────────────────────────


def create_app() -> web.Application:
    """Construct and configure the aiohttp application.

    * Attaches CORS and request-logging middlewares.
    * Registers all domain route handlers (topology, metrics, activation).
    * Adds ``/openapi.json`` (apispec-generated) and ``/docs`` (Swagger UI).
    * Registers startup/shutdown signal handlers.
    """
    _openapi_spec = build_openapi_spec()

    application = web.Application(middlewares=[cors_middleware, logging_middleware])

    # Domain routes
    register_topology(application)
    register_metrics(application)
    register_activation(application)

    # ── Meta-endpoints ────────────────────────────────────────────────────────

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def openapi_json(request: web.Request) -> web.Response:
        return web.json_response(_openapi_spec)

    async def swagger_ui(request: web.Request) -> web.Response:
        return web.Response(text=_SWAGGER_UI_HTML, content_type="text/html")

    application.router.add_get("/health", health)
    application.router.add_get("/openapi.json", openapi_json)
    application.router.add_get("/docs", swagger_ui)

    # ── Lifecycle hooks ────────────────────────────────────────────────────────

    async def on_startup(app: web.Application) -> None:
        logger.info("5G NDT API starting up — aiohttp + apispec")

    async def on_shutdown(app: web.Application) -> None:
        logger.info("5G NDT API shutting down")

    application.on_startup.append(on_startup)
    application.on_shutdown.append(on_shutdown)

    return application


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    host = "0.0.0.0"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    logging.basicConfig(level=logging.INFO)
    web.run_app(create_app(), host=host, port=port)
