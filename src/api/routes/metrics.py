"""Metrics query service — sync helpers and async aiohttp route handlers.

Provides functions to query KPI data and exposes them as async HTTP endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from aiohttp import web

from ...core.kpi.aggregator import KPIAggregator
from ...core.kpi.metrics import list_metrics_for
from ...core.topology.models import KPI

_aggregator = KPIAggregator()

# ── Sync helpers (used directly in integration tests) ─────────────────────────


def get_metric_definitions() -> List[Dict[str, Any]]:
    """Return metadata for all registered KPI metrics."""
    from ...core.kpi.metrics import METRICS

    return [
        {
            "name": m.name,
            "unit": m.unit,
            "description": m.description,
            "entity_types": list(m.entity_types),
        }
        for m in METRICS.values()
    ]


def get_metrics_for_entity_type(entity_type: str) -> List[Dict[str, Any]]:
    metrics = list_metrics_for(entity_type)
    return [
        {
            "name": m.name,
            "unit": m.unit,
            "description": m.description,
            "entity_types": list(m.entity_types),
        }
        for m in metrics
    ]


def get_kpi_summary(entity_id: UUID) -> Dict[str, Any]:
    summary = _aggregator.get_kpi_summary(entity_id)
    return {"entity_id": str(entity_id), "kpis": summary or {}}


def get_kpi_snapshots(entity_id: UUID, entity_type: str = "gNodeB") -> List[Dict[str, Any]]:
    kpis: List[KPI] = _aggregator.aggregate_entity(entity_id, entity_type)
    return [
        {
            "id": str(kpi.id),
            "entity_id": str(kpi.entity_id),
            "metric_name": kpi.metric_name,
            "value": kpi.value,
            "unit": kpi.unit,
            "severity": kpi.severity,
            "timestamp": kpi.timestamp.isoformat(),
        }
        for kpi in kpis
    ]


# ── aiohttp async route handlers ──────────────────────────────────────────────

routes = web.RouteTableDef()


@routes.get("/api/v1/metrics/definitions")
async def api_get_metric_definitions(request: web.Request) -> web.Response:
    """Return metadata for every registered KPI metric type."""
    return web.json_response(get_metric_definitions())


@routes.get("/api/v1/metrics/definitions/{entity_type}")
async def api_get_metrics_for_entity_type(request: web.Request) -> web.Response:
    """Return KPI metric definitions that apply to the specified entity type."""
    entity_type = request.match_info["entity_type"]
    return web.json_response(get_metrics_for_entity_type(entity_type))


@routes.get("/api/v1/metrics/summary/{entity_id}")
async def api_get_kpi_summary(request: web.Request) -> web.Response:
    """Return the most recent KPI values for the specified entity."""
    try:
        entity_id = UUID(request.match_info["entity_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    return web.json_response(get_kpi_summary(entity_id))


@routes.get("/api/v1/metrics/snapshots/{entity_id}")
async def api_get_kpi_snapshots(request: web.Request) -> web.Response:
    """Return all computed KPI snapshots for the specified entity."""
    try:
        entity_id = UUID(request.match_info["entity_id"])
    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid UUID format")
    entity_type = request.rel_url.query.get("entity_type", "gNodeB")
    return web.json_response(get_kpi_snapshots(entity_id, entity_type))


def register_routes(app: web.Application) -> None:
    """Register all metrics route handlers with an aiohttp Application."""
    app.add_routes(routes)
