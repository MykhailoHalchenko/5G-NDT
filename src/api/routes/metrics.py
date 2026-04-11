"""Metrics query service — sync helpers and async FastAPI router.

Provides functions to query KPI data and exposes them as async HTTP endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

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


# ── FastAPI async router ───────────────────────────────────────────────────────

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get(
    "/definitions",
    summary="List all KPI metric definitions",
)
async def api_get_metric_definitions() -> List[Dict[str, Any]]:
    """Return metadata for every registered KPI metric type."""
    return get_metric_definitions()


@router.get(
    "/definitions/{entity_type}",
    summary="List KPI metrics applicable to a given entity type",
)
async def api_get_metrics_for_entity_type(entity_type: str) -> List[Dict[str, Any]]:
    """Return KPI metric definitions that apply to the specified entity type."""
    return get_metrics_for_entity_type(entity_type)


@router.get(
    "/summary/{entity_id}",
    summary="Get latest KPI summary for a network entity",
)
async def api_get_kpi_summary(entity_id: UUID) -> Dict[str, Any]:
    """Return the most recent KPI values for the specified entity."""
    return get_kpi_summary(entity_id)


@router.get(
    "/snapshots/{entity_id}",
    summary="Get KPI snapshots for a network entity",
)
async def api_get_kpi_snapshots(entity_id: UUID, entity_type: str = "gNodeB") -> List[Dict[str, Any]]:
    """Return all computed KPI snapshots for the specified entity within the aggregation window."""
    return get_kpi_snapshots(entity_id, entity_type)
