"""KPI metric definitions.

Centralised registry of all known metric names, units, and descriptions
used across the 5G NDT platform.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    """Metadata for a single KPI metric."""

    name: str
    unit: str
    description: str
    entity_types: tuple


# ── Metric registry ───────────────────────────────────────────────────────────

METRICS: dict[str, MetricDefinition] = {
    # gNodeB metrics
    "total_throughput_mbps": MetricDefinition(
        name="total_throughput_mbps",
        unit="Mbps",
        description="Aggregate downlink + uplink throughput",
        entity_types=("gNodeB",),
    ),
    "average_latency_ms": MetricDefinition(
        name="average_latency_ms",
        unit="ms",
        description="Average round-trip latency to UE",
        entity_types=("gNodeB",),
    ),
    "latency_ms": MetricDefinition(
        name="latency_ms",
        unit="ms",
        description="End-to-end latency measurement",
        entity_types=("gNodeB", "NetworkSlice"),
    ),
    "packet_loss_percent": MetricDefinition(
        name="packet_loss_percent",
        unit="%",
        description="Percentage of lost packets",
        entity_types=("gNodeB", "NetworkSlice"),
    ),
    # CU metrics
    "cpu_utilization_percent": MetricDefinition(
        name="cpu_utilization_percent",
        unit="%",
        description="CPU utilization of the CU server",
        entity_types=("CU",),
    ),
    "memory_utilization_percent": MetricDefinition(
        name="memory_utilization_percent",
        unit="%",
        description="RAM utilization of the CU server",
        entity_types=("CU",),
    ),
    # DU metrics
    "current_load_percent": MetricDefinition(
        name="current_load_percent",
        unit="%",
        description="Real-time DU processing load",
        entity_types=("DU",),
    ),
    "active_ues": MetricDefinition(
        name="active_ues",
        unit="count",
        description="Number of currently active UE connections",
        entity_types=("DU", "gNodeB"),
    ),
    # Slice metrics
    "utilization_percent": MetricDefinition(
        name="utilization_percent",
        unit="%",
        description="Current slice capacity utilization",
        entity_types=("NetworkSlice",),
    ),
    "current_subscribers": MetricDefinition(
        name="current_subscribers",
        unit="count",
        description="Number of active slice subscribers",
        entity_types=("NetworkSlice",),
    ),
    # Connection metrics
    "bandwidth_mbps": MetricDefinition(
        name="bandwidth_mbps",
        unit="Mbps",
        description="Available bandwidth on a connection",
        entity_types=("Connection",),
    ),
    "link_latency_ms": MetricDefinition(
        name="link_latency_ms",
        unit="ms",
        description="Propagation latency on a connection",
        entity_types=("Connection",),
    ),
}


def get_metric(name: str) -> MetricDefinition:
    """Return the MetricDefinition for the given metric name.

    Raises:
        KeyError: If the metric name is not registered.
    """
    if name not in METRICS:
        raise KeyError(f"Unknown metric: {name!r}. Registered metrics: {list(METRICS)}")
    return METRICS[name]


def list_metrics_for(entity_type: str) -> list[MetricDefinition]:
    """Return all metric definitions applicable to the given entity type."""
    return [m for m in METRICS.values() if entity_type in m.entity_types]
