"""Metrics query service (replaces FastAPI router).

Provides functions to query KPI data.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID

from ...core.kpi.aggregator import KPIAggregator
from ...core.kpi.metrics import list_metrics_for
from ...core.topology.models import KPI

_aggregator = KPIAggregator()


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
