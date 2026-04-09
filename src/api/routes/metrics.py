"""Metrics and KPI REST endpoints.

GET /api/v1/metrics/{entity_id}      — latest KPI values for an entity
GET /api/v1/kpi/{entity_id}          — KPI snapshots with severity
GET /api/v1/metrics/definitions      — list all known metric definitions
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ...core.kpi.aggregator import KPIAggregator
from ...core.kpi.metrics import MetricDefinition, list_metrics_for
from ...core.topology.models import KPI

router = APIRouter(prefix="/metrics", tags=["metrics", "kpi"])

_aggregator = KPIAggregator()


@router.get(
    "/definitions",
    response_model=List[Dict[str, Any]],
    summary="List all metric definitions",
)
async def list_metric_definitions() -> List[Dict[str, Any]]:
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


@router.get(
    "/entity/{entity_type}",
    response_model=List[Dict[str, Any]],
    summary="List metrics applicable to an entity type",
)
async def metrics_for_entity_type(entity_type: str) -> List[Dict[str, Any]]:
    """Return metric definitions for the given entity type (e.g. 'gNodeB')."""
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


@router.get(
    "/{entity_id}/summary",
    response_model=Dict[str, Any],
    summary="Get latest KPI summary for an entity",
)
async def get_kpi_summary(entity_id: UUID) -> Dict[str, Any]:
    """Return the latest KPI summary (metric_name -> value) for a network entity."""
    summary = _aggregator.get_kpi_summary(entity_id)
    if summary is None:
        return {"entity_id": str(entity_id), "kpis": {}}
    return {"entity_id": str(entity_id), "kpis": summary}


@router.get(
    "/{entity_id}/kpi",
    response_model=List[Dict[str, Any]],
    summary="Get KPI snapshots with severity for an entity",
)
async def get_kpi_snapshots(entity_id: UUID, entity_type: str = "gNodeB") -> List[Dict[str, Any]]:
    """Return computed KPI snapshots with severity levels for a network entity."""
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
